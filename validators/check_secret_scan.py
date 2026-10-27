#!/usr/bin/env python3
"""Run Gitleaks without authored regex allowlists and check exact old findings."""

import _literal_args as argparse
from _literal_json import InvalidJSON, loads as loads_json
import _toml11 as toml
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


PUBLIC_HEX_SHA256 = "9f9f5111f7b27a781f1f1ddde5ebc2dd2b796bfc7365c9c28b548e564176929f"
PUBLIC_HEX_FILE = "validators/unresolvable-commit-citations.toml"
PUBLIC_HEX_RULE = "generic-api-key"
KNOWN_COMMITS = frozenset({
    "6c0b27b19d2cbaf32ddaaff2638175f18d683974",
    "f64bfa0500802eee910e27f40c6d4152474c2252",
    "8e52e9bab66d4e2bc1b52b427f69ef0c562096ff",
    "ffac3a202344f42f7608795866065971a08d42ed",
})
GIT_LOG_ARGS = ("--full-history", "--all", "-m", "--diff-filter=tuxdb")
GIT_LOG_OPTIONS = " ".join(GIT_LOG_ARGS)


def known_public_literal(finding: dict) -> bool:
    secret = finding.get("Secret")
    return (
        finding.get("RuleID") == PUBLIC_HEX_RULE
        and finding.get("File") == PUBLIC_HEX_FILE
        and finding.get("Commit") in KNOWN_COMMITS
        and isinstance(secret, str)
        and hashlib.sha256(secret.encode()).hexdigest() == PUBLIC_HEX_SHA256
    )


def reachable_commits(root: Path) -> tuple[set[str], set[str]]:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required to bound the secret scan")
    shallow = subprocess.run(  # nosec B603  # noqa: S603
        [git, "rev-parse", "--is-shallow-repository"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if shallow.returncode or shallow.stdout.strip() != "false":
        raise RuntimeError("secret scan requires a full Git checkout")
    populations = []
    for revision in ("--all", "HEAD"):
        listed = subprocess.run(  # nosec B603  # noqa: S603
            [git, "rev-list", revision], cwd=root, capture_output=True, text=True, check=False,
        )
        if listed.returncode:
            raise RuntimeError("cannot enumerate reachable Git commits")
        populations.append(set(listed.stdout.splitlines()))
    all_commits, head_commits = populations
    if not head_commits or not head_commits <= all_commits:
        raise RuntimeError("secret scan has no complete HEAD ancestry")
    return all_commits, head_commits


def scanned_count(stderr: str) -> int:
    marker = " commits scanned."
    numbers = []
    for line in stderr.splitlines():
        if marker in line:
            before = line.split(marker, 1)[0].split()
            if before and before[-1].isdecimal():
                numbers.append(int(before[-1]))
    if len(numbers) != 1:
        raise RuntimeError("Gitleaks did not report one commit population")
    return numbers[0]


def text_change_commits(numstat: bytes, reachable: set[str]) -> set[str]:
    marker = b"SCAN-COMMIT:"
    patch_commits: set[str] = set()
    current: str | None = None
    rename_paths = 0
    for record in numstat.split(b"\0"):
        if rename_paths:
            if not record:
                raise RuntimeError("Git numstat reported incomplete rename paths")
            rename_paths -= 1
            continue
        if record.startswith(marker):
            sha = record[len(marker):]
            if len(sha) != 40 or any(byte not in b"0123456789abcdef" for byte in sha):
                raise RuntimeError("Git numstat reported an invalid commit marker")
            current = sha.decode("ascii")
            if current not in reachable:
                raise RuntimeError("Git numstat reported an unreachable commit")
            continue
        item = record.lstrip(b"\n")
        if not item:
            continue
        fields = item.split(b"\t", 2)
        if current is None or len(fields) != 3:
            raise RuntimeError("Git numstat reported an unreadable patch record")
        added, deleted = fields[:2]
        if not ((added.isdigit() and deleted.isdigit()) or (added == b"-" and deleted == b"-")):
            raise RuntimeError("Git numstat reported an unreadable patch record")
        if added.isdigit() and (int(added) > 0 or int(deleted) > 0):
            patch_commits.add(current)
        if not fields[2]:
            rename_paths = 2
    if rename_paths or current is None or not patch_commits:
        raise RuntimeError("Git numstat has no complete text-change history")
    return patch_commits


def patch_bearing_commits(root: Path, reachable: set[str]) -> set[str]:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required to enumerate text-change commits")
    result = subprocess.run(  # nosec B603  # noqa: S603
        [git, "log", "--format=SCAN-COMMIT:%H", "--numstat", "-z", *GIT_LOG_ARGS],
        cwd=root, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError("cannot enumerate text-change Git commits")
    return text_change_commits(result.stdout, reachable)


def check_scan_population(scanned: int, reachable: set[str], head_ancestry: set[str],
                          expected: set[str], patch_commits: set[str]) -> None:
    # Gitleaks counts commits with text fragments, including deletion-only hunks.
    if not patch_commits or not patch_commits <= reachable or scanned != len(patch_commits):
        raise RuntimeError("Gitleaks scan count disagrees with text-change Git history")
    if not head_ancestry or not head_ancestry <= reachable or not (expected & head_ancestry):
        raise RuntimeError("known public finding control is absent from HEAD ancestry")


def check_findings(findings: list, expected_commits: set[str]) -> None:
    seen: set[str] = set()
    unexpected = []
    for finding in findings:
        if not isinstance(finding, dict) or not known_public_literal(finding):
            unexpected.append(finding)
            continue
        commit = finding["Commit"]
        if commit in seen:
            raise RuntimeError("Gitleaks repeated a known public finding")
        seen.add(commit)
    if unexpected:
        print("FAIL: Gitleaks reported " + str(len(unexpected)) + " unapproved finding(s)", file=sys.stderr)
        for finding in unexpected:
            if isinstance(finding, dict):
                print("  rule=" + str(finding.get("RuleID")) + " file=" + str(finding.get("File"))
                      + " commit=" + str(finding.get("Commit")), file=sys.stderr)
        raise RuntimeError("secret scan found candidates for review")
    if seen != expected_commits:
        raise RuntimeError("known public finding population changed; review the scan and exception")


def check_no_ignore_file(root: Path) -> None:
    ignore = root / ".gitleaksignore"
    if ignore.exists() or ignore.is_symlink():
        raise RuntimeError("Gitleaks ignore file is not permitted")


def check_exact_config(config: Path) -> None:
    try:
        document = toml.loads_bytes(config.read_bytes())
    except toml.TOMLDecodeError as exc:
        raise RuntimeError(f"Gitleaks configuration could not be parsed: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"Gitleaks configuration could not be read: {exc}") from exc
    if (not isinstance(document, dict) or set(document) != {"extend"}
            or not isinstance(document["extend"], dict)
            or set(document["extend"]) != {"useDefault"}
            or document["extend"]["useDefault"] is not True):
        raise RuntimeError("Gitleaks configuration must contain only the default rule extension")


def gitleaks_command(binary: Path, config: str, report: Path,
                     log_options: str = GIT_LOG_OPTIONS) -> list[str]:
    return [
        str(binary), "detect", "--source", ".", "--config", config,
        "--no-banner", "--no-color", "--log-level", "info",
        "--ignore-gitleaks-allow", "--log-opts=" + log_options,
        "--report-format", "json", "--report-path", str(report), "--exit-code", "1",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gitleaks", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    binary = Path(args.gitleaks).resolve()
    if not binary.is_file() or not (root / ".gitleaks.toml").is_file():
        raise RuntimeError("Gitleaks binary and configuration are required")
    check_no_ignore_file(root)
    check_exact_config(root / ".gitleaks.toml")
    reachable, head_ancestry = reachable_commits(root)
    patch_commits = patch_bearing_commits(root, reachable)
    expected = KNOWN_COMMITS & reachable
    if not expected:
        raise RuntimeError("known public finding control is absent from this history")
    with TemporaryDirectory(prefix="gitleaks-report-") as directory:
        report = Path(directory) / "findings.json"
        result = subprocess.run(  # nosec B603  # noqa: S603
            gitleaks_command(binary, ".gitleaks.toml", report),
            cwd=root, capture_output=True, text=True, check=False,
        )
        if result.returncode not in (0, 1) or not report.is_file():
            raise RuntimeError("Gitleaks did not complete and write its report")
        telemetry = result.stdout + "\n" + result.stderr
        try:
            scanned = scanned_count(telemetry)
        except RuntimeError as exc:
            marker_count = telemetry.count(" commits scanned.")
            marker_state = "none" if marker_count == 0 else "one unreadable" if marker_count == 1 else "multiple"
            raise RuntimeError(
                str(exc) + f" (result={'findings' if result.returncode == 1 else 'clear'}, "
                f"stdout_present={bool(result.stdout)}, stderr_present={bool(result.stderr)}, "
                f"markers={marker_state})"
            ) from exc
        check_scan_population(scanned, reachable, head_ancestry, expected, patch_commits)
        findings = loads_json(report.read_text())
        if not isinstance(findings, list) or (result.returncode == 0) != (len(findings) == 0):
            raise RuntimeError("Gitleaks exit status disagrees with its report")
        check_findings(findings, expected)
    print(f"secret scan: {scanned} commits reported, {len(expected)} exact public finding(s), 0 other findings")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, InvalidJSON, OSError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
