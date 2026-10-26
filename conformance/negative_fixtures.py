#!/usr/bin/env python3
"""Require explicit rejection evidence for every recursively discovered negative."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validators"))
import _toml11 as toml  # noqa: E402


def population(root: Path, ledger: Path):
    discovered = {path.relative_to(root).as_posix() for path in (root / "examples/negative").rglob("*.toml")}
    doc = toml.loads(ledger.read_text())
    entries = doc.get("fixtures", [])
    names = [entry["path"] for entry in entries]
    if not discovered or len(names) != len(set(names)) or set(names) != discovered:
        raise ValueError("negative fixture ledger has missing, duplicate, or orphan entries")
    for entry in entries:
        control = root / entry["positive_control"]
        if not control.is_file() or control.is_relative_to(root / "examples/negative"):
            raise ValueError("each negative fixture needs an existing positive control")
        if not entry.get("routes"):
            raise ValueError("negative fixture lacks validation routes")
        for route in entry["routes"]:
            if not (root / route["python_validator"]).is_file() or not route.get("error_contains"):
                raise ValueError("negative fixture lacks a diagnostic owner")
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--rs", type=Path, required=True)
    parser.add_argument("--go", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    entries = population(root, root / "conformance/negative-expectations.toml")
    observed, failures, controls = [], [], set()
    for entry in entries:
        for route in entry["routes"]:
            for language, prefix in (("rust", [str(args.rs.resolve()), "--repo-root", str(root), "--mode", route["mode"]]),
                                      ("go", [str(args.go.resolve()), "--repo-root", str(root), "--mode", route["mode"]]),
                                      ("python", [sys.executable, str(root / route["python_validator"])])):
                if language == "python" and Path(route["python_validator"]).name not in {
                    "validate_traceability.py", "validate_implementation_dag.py", "validate_review_readiness.py"}:
                    prefix += ["--repo-root", str(root)]
                control_key = (tuple(prefix), entry["positive_control"])
                if control_key not in controls:
                    result = subprocess.run([*prefix, str(root / entry["positive_control"])], cwd=root,  # nosec B603 # noqa: S603
                                            capture_output=True, text=True, timeout=60)
                    if result.returncode != 0:
                        failures.append({"control": entry["positive_control"], "language": language,
                                         "output": result.stdout + result.stderr})
                    controls.add(control_key)
                result = subprocess.run([*prefix, str(root / entry["path"])], cwd=root,  # nosec B603 # noqa: S603
                                        capture_output=True, text=True, timeout=60)
                output = result.stdout + result.stderr
                matches = (result.returncode == 1 and all(needle.lower() in output.lower() for needle in route["error_contains"])
                           and not any(needle.lower() in output.lower() for needle in route.get("error_not_contains", [])))
                for diagnostic, count in route.get("diagnostic_counts", {}).items():
                    if sum(diagnostic in line for line in output.splitlines()) != count:
                        matches = False
                observation = {"fixture": entry["path"], "route": route["mode"], "implementation": language,
                               "passed": matches, "exit": result.returncode, "output": output}
                observed.append(observation)
                if not matches:
                    failures.append(observation)
    expected = 3 * sum(len(entry["routes"]) for entry in entries)
    if len(observed) != expected or not controls:
        raise AssertionError("negative fixture population did not execute completely")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({"status": "failed" if failures else "passed", "fixture_count": len(entries),
                                      "positive_controls": len(controls), "observations": observed,
                                      "failures": failures, "skipped": []}, ensure_ascii=True, indent=2))
    for failure in failures:
        print(json.dumps(failure, ensure_ascii=True))
    print(f"Compared {len(entries)} discovered negatives through {expected} explicit routes; "
          f"{len(controls)} positive controls; skipped=[]")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
