#!/usr/bin/env python3
"""Run pinned Lychee with exact source and URL exceptions, then assert coverage."""

from _literal_path import Path
import hashlib
import subprocess
import sys
from tempfile import TemporaryDirectory

import _literal_args as argparse
from _literal_json import InvalidJSON, dumps as dumps_json, loads as loads_json
from _credential_git import git
from _working_source import DIFF_FORMAT, working_delta
from prepare_link_scan import (SKIP_DIRECTORIES, SKIP_HOSTS,
                               select_links, split_record, tracked_files)


def run(binary: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603  # noqa: S603
        [str(binary), *arguments], capture_output=True, text=True, check=False,
    )


def require_dump(binary: Path, output: Path, subject: str) -> list[str]:
    result = run(binary, ["--config", "lychee.toml", "--no-progress", "--format", "json",
                          "--output", str(output), "--dump", subject])
    if result.returncode or not output.is_file():
        raise RuntimeError("Lychee did not extract its link inputs")
    rows = output.read_text().splitlines()
    if not rows:
        raise RuntimeError("Lychee extracted no link inputs")
    return rows


def report_outcomes(report: dict, candidates: list[str], source: Path) -> dict:
    """Validate the entire outcome partition and retain only declared fields."""
    if (not isinstance(report, dict) or type(candidates) is not list or not candidates
            or any(type(url) is not str or not url.startswith(("http://", "https://"))
                   or any(ord(char) < 32 or ord(char) == 127 for char in url) for url in candidates)):
        raise RuntimeError("link report requires a complete distinct HTTP candidate population")
    if candidates != sorted(set(candidates)):
        raise RuntimeError("link report candidate population is repeated or unordered")
    population = len(candidates)
    for key, expected in (("total", population), ("unique", population),
                          ("unknown", 0), ("unsupported", 0),
                          ("excludes", 0), ("cached", 0), ("remaps", 0)):
        if type(report.get(key)) is not int or report[key] != expected:
            raise RuntimeError("Lychee report population differs from prepared URLs: " + key)
    counts = {}
    for key in ("successful", "errors", "timeouts"):
        value = report.get(key)
        if type(value) is not int or not 0 <= value <= population:
            raise RuntimeError("Lychee report has an invalid outcome count: " + key)
        counts[key] = value
    if sum(counts.values()) != population:
        raise RuntimeError("Lychee outcome counts do not cover the prepared URLs")
    if report.get("excluded_map") != {}:
        raise RuntimeError("Lychee report contains unexpected excluded outcomes")
    visited = set()
    failures = []
    for key, map_key, outcome in (("successful", "success_map", "success"),
                                  ("errors", "error_map", "error"),
                                  ("timeouts", "timeout_map", "timeout")):
        mapping = report.get(map_key)
        if not isinstance(mapping, dict) or set(mapping) != ({str(source)} if counts[key] else set()):
            raise RuntimeError("Lychee report used an unexpected input source: " + map_key)
        entries = mapping.get(str(source), [])
        if not isinstance(entries, list) or len(entries) != counts[key]:
            raise RuntimeError("Lychee report omitted outcome URLs: " + map_key)
        for entry in entries:
            if not isinstance(entry, dict) or type(entry.get("url")) is not str:
                raise RuntimeError("Lychee report has an invalid URL entry")
            url = entry["url"]
            if url not in candidates or url in visited:
                raise RuntimeError("Lychee report repeated or substituted a prepared URL")
            status = entry.get("status")
            if (not isinstance(status, dict) or type(status.get("text")) is not str
                    or not status["text"]):
                raise RuntimeError("Lychee report omitted an outcome status")
            code = status.get("code")
            if code is not None and (type(code) is not int or not 100 <= code <= 599):
                raise RuntimeError("Lychee report has an invalid HTTP status")
            if outcome == "success" and (code is None or not (200 <= code <= 299 or code in (403, 429))):
                raise RuntimeError("Lychee successful URL has an unaccepted HTTP status")
            visited.add(url)
            if outcome != "success":
                failures.append({"url": url, "outcome": outcome, "http_status": code})
    if visited != set(candidates):
        raise RuntimeError("Lychee report URL set differs from prepared URLs")
    if len(failures) != counts["errors"] + counts["timeouts"]:
        raise RuntimeError("Lychee failure population differs from its outcome counts")
    return {"status": "failed" if failures else "passed", "total": population, **counts,
            "failures": sorted(failures, key=lambda entry: entry["url"])}


def check_report(report: dict, candidates: list[str], source: Path) -> None:
    if report_outcomes(report, candidates, source)["status"] != "passed":
        raise RuntimeError("Lychee reported failed prepared URLs")


def source_identity(root: Path) -> dict:
    actual = git(root, ["rev-parse", "--show-toplevel"]).decode().rstrip("\n")
    if actual != str(root):
        raise RuntimeError("link checking requires the Git checkout root")
    commit = git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode().rstrip("\n")
    if len(commit) not in (40, 64) or any(char not in "0123456789abcdef" for char in commit):
        raise RuntimeError("link source is not a named commit")
    status = git(root, ["status", "--porcelain", "-z"])
    byte_clean, delta = working_delta(root, commit)
    return {"commit": commit, "tree_state": "clean" if not status and byte_clean else "working-files",
            "status_sha256": hashlib.sha256(status).hexdigest(),
            "diff_format": DIFF_FORMAT, "diff_sha256": delta}


def artifact_target(root: Path, target: Path, tracked: set[str]) -> Path:
    target = target.resolve()
    if target.is_relative_to(root):
        relative = target.relative_to(root)
        if str(relative) in tracked or not relative.parts or relative.parts[0] != ".local":
            raise ValueError("link reports require an external or untracked .local output path")
    return target


def write_report(path: Path, record: dict, summary: Path | None = None) -> None:
    payload = dumps_json(record, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    if summary is not None:
        with summary.open("a", encoding="utf-8") as output:
            output.write("\n### Link scan result\n\n```json\n" + payload + "```\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lychee", required=True)
    parser.add_argument("--report", type=Path, default=Path(".local/link-scan/report.json"))
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    record = {"schema_version": "link-scan-v1", "status": "incomplete", "phase": "source",
              "comparison": "Prepared HTTP candidates from the pinned extractor against their complete classified outcomes",
              "source_exclusions": sorted(SKIP_DIRECTORIES), "hidden_path_segments_excluded": True,
              "host_exceptions": sorted(SKIP_HOSTS),
              "outside_subject": ["complete extractor and dependency source audit", "other driver and scanner entry points"]}
    destination = summary = None
    try:
        checkout = Path.cwd().resolve()
        record["source"] = source_identity(checkout)
        tracked = tracked_files()
        report_target = artifact_target(checkout, args.report, tracked)
        summary_target = None if args.summary is None else artifact_target(checkout, args.summary, tracked)
        if summary_target == report_target:
            raise ValueError("link report and summary destinations must differ")
        destination, summary = report_target, summary_target

        def phase(name):
            record["phase"] = name
            write_report(destination, record)

        phase("scanner-identity")
        binary = Path(args.lychee).resolve()
        if not binary.is_file():
            raise RuntimeError("pinned Lychee binary is absent")
        binary_digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        record["scanner"] = {"expected_version": "lychee 0.24.2", "binary_sha256": binary_digest}
        write_report(destination, record)
        version = run(binary, ["--version"])
        if version.returncode or version.stdout.strip() != "lychee 0.24.2":
            raise RuntimeError("Lychee version differs from the pinned scanner")
        record["scanner"]["version"] = "lychee 0.24.2"
        with TemporaryDirectory(prefix="link-scan-") as work:
            root = Path(work)
            phase("extraction")
            rows = require_dump(binary, root / "all-links.txt", ".")
            candidates, exceptions = select_links(rows, tracked)
            record["candidate_urls"] = candidates
            record["candidate_urls_sha256"] = hashlib.sha256("\0".join(candidates).encode()).hexdigest()
            record["excepted_urls"] = sorted(exceptions)
            source = root / "candidate-links.txt"
            source.write_text("".join(url + "\n" for url in candidates))
            phase("admission")
            redump = require_dump(binary, root / "candidate-dump.txt", str(source))
            if len(redump) != len(candidates) or any(row.endswith(" [excluded]") for row in redump):
                raise RuntimeError("Lychee did not admit every prepared candidate")
            parsed = [split_record(row)[0] for row in redump]
            if sorted(parsed) != candidates:
                raise RuntimeError("Lychee candidate input differs from extracted URL set")
            phase("checking")
            report_path = root / "report.json"
            result = run(binary, ["--config", "lychee.toml", "--no-progress", "--format", "json",
                                  "--output", str(report_path), str(source)])
            record["scanner_exit_status"] = result.returncode
            if not report_path.is_file():
                raise RuntimeError("Lychee did not return its outcome report")
            outcomes = report_outcomes(loads_json(report_path.read_text()), candidates, source)
            if result.returncode != (0 if outcomes["status"] == "passed" else 2):
                raise RuntimeError("Lychee exit status disagrees with its complete URL outcomes")
        phase("source-recheck")
        if source_identity(checkout) != record["source"] or hashlib.sha256(binary.read_bytes()).hexdigest() != binary_digest:
            raise RuntimeError("link source or scanner identity changed during checking")
        record.update(outcomes)
        record["phase"] = "complete"
    except (InvalidJSON, OSError, RuntimeError, ValueError, TypeError) as exc:
        record["status"] = "incomplete"
        record["failure_type"] = type(exc).__name__
        print("FAIL: " + str(exc), file=sys.stderr)
    if destination is not None:
        try:
            write_report(destination, record, summary)
        except OSError as exc:
            record.update(status="incomplete", phase="report-delivery", failure_type=type(exc).__name__)
            try:
                write_report(destination, record)
            except OSError as retry:
                print("FAIL: cannot retain incomplete link report: " + type(retry).__name__, file=sys.stderr)
            print("FAIL: cannot retain link report: " + type(exc).__name__, file=sys.stderr)
            return 2
    if record["status"] == "incomplete":
        return 2
    if record["status"] == "failed":
        for failure in record["failures"]:
            print("link failure: " + dumps_json(failure, sort_keys=True), file=sys.stderr)
        return 1
    print("link scan at " + record["source"]["commit"] + " (" + record["source"]["tree_state"] + "): "
          + str(record["total"]) + " distinct prepared URLs checked, 0 errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
