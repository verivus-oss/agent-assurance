#!/usr/bin/env python3
"""Run pinned Lychee with exact source and URL exceptions, then assert coverage."""

from _literal_path import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import _literal_args as argparse
from _literal_json import InvalidJSON, loads as loads_json
from prepare_link_scan import select_links, split_record, tracked_files


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


def check_report(report: dict, candidates: list[str], source: Path) -> None:
    population = len(candidates)
    for key, expected in (("total", population), ("unique", population),
                          ("successful", population), ("unknown", 0),
                          ("unsupported", 0), ("timeouts", 0),
                          ("excludes", 0), ("errors", 0)):
        if type(report.get(key)) is not int or report[key] != expected:
            raise RuntimeError("Lychee report population differs from prepared URLs: " + key)
    success = report.get("success_map")
    if not isinstance(success, dict) or set(success) != {str(source)}:
        raise RuntimeError("Lychee report used an unexpected input source")
    entries = success[str(source)]
    if not isinstance(entries, list) or len(entries) != population:
        raise RuntimeError("Lychee report omitted successful URLs")
    urls = [entry.get("url") for entry in entries if isinstance(entry, dict)]
    if len(urls) != population or sorted(urls) != candidates:
        raise RuntimeError("Lychee report URL set differs from prepared URLs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lychee", required=True)
    args = parser.parse_args()
    binary = Path(args.lychee).resolve()
    if not binary.is_file():
        raise RuntimeError("pinned Lychee binary is absent")
    version = run(binary, ["--version"])
    if version.returncode or version.stdout.strip() != "lychee 0.24.2":
        raise RuntimeError("Lychee version differs from the pinned scanner")
    tracked = tracked_files()
    with TemporaryDirectory(prefix="link-scan-") as work:
        root = Path(work)
        rows = require_dump(binary, root / "all-links.txt", ".")
        candidates, _ = select_links(rows, tracked)
        source = root / "candidate-links.txt"
        source.write_text("".join(url + "\n" for url in candidates))
        redump = require_dump(binary, root / "candidate-dump.txt", str(source))
        if len(redump) != len(candidates) or any(row.endswith(" [excluded]") for row in redump):
            raise RuntimeError("Lychee did not admit every prepared candidate")
        parsed = [split_record(row)[0] for row in redump]
        if sorted(parsed) != candidates:
            raise RuntimeError("Lychee candidate input differs from extracted URL set")
        report_path = root / "report.json"
        result = run(binary, ["--config", "lychee.toml", "--no-progress", "--format", "json",
                              "--output", str(report_path), str(source)])
        if result.returncode or not report_path.is_file():
            raise RuntimeError("Lychee found a broken link or could not complete the scan")
        report = loads_json(report_path.read_text())
        if not isinstance(report, dict):
            raise RuntimeError("Lychee did not return a JSON report")
        check_report(report, candidates, source)
    print(f"link scan: {len(candidates)} distinct URLs checked, 0 errors")


if __name__ == "__main__":
    try:
        main()
    except (InvalidJSON, OSError, RuntimeError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
