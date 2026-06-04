#!/usr/bin/env python3
"""DAG-TOML cross-implementation conformance runner.

Runs every fixture under conformance/cases/<kind>/{valid,invalid}/ through
all three validator implementations (Rust primary, Go primary, Python
reference) and fails unless they agree:

- valid fixtures must be ACCEPTED (exit 0) by every implementation
- invalid fixtures must be REJECTED (exit 1) by every implementation
- when a `<name>.expected.toml` sidecar declares `error_contains`, every
  rejecting implementation's output must contain each substring

Known, deliberately tolerated divergences live in
conformance/known-divergences.toml. Each entry downgrades a specific
(case, implementation) mismatch from a failure to a loud warning, the
same pattern the Makefile uses for TOML_CONFORMANCE_SKIPS: a baseline of
currently-known drift, not a green light. Revisit every entry whenever a
validator changes; if a run newly agrees, remove the entry.

Exit codes: 0 all agree (modulo known divergences), 1 disagreement,
2 infrastructure error (missing binary, unparseable fixture).
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import tomllib

# Maps a case-directory kind to the Python reference validator.
PY_VALIDATORS = {
    "implementation-dag": "validators/validate_implementation_dag.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DAG-TOML conformance corpus.")
    parser.add_argument("--rs", required=True, help="Path to the dagtoml-validate-rs binary.")
    parser.add_argument("--go", required=True, help="Path to the dagtoml-validate-go binary.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root passed through to every validator (default: .).",
    )
    parser.add_argument(
        "--cases",
        default="conformance/cases",
        help="Corpus root (default: conformance/cases).",
    )
    parser.add_argument(
        "--known-divergences",
        default="conformance/known-divergences.toml",
        help="TOML file of tolerated (case, implementation) mismatches.",
    )
    return parser.parse_args()


def run_validator(cmd: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        print(f"error: cannot execute {cmd[0]}", file=sys.stderr)
        raise SystemExit(2)
    return proc.returncode, proc.stdout + proc.stderr


def load_known_divergences(path: pathlib.Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    doc = tomllib.loads(path.read_text())
    known: dict[tuple[str, str], str] = {}
    for entry in doc.get("divergence", []):
        for impl in entry["implementations"]:
            known[(entry["case"], impl)] = entry["reason"]
    return known


def main() -> int:
    args = parse_args()
    cases_root = pathlib.Path(args.cases)
    known = load_known_divergences(pathlib.Path(args.known_divergences))

    failures: list[str] = []
    warnings: list[str] = []
    total = 0

    for kind_dir in sorted(p for p in cases_root.iterdir() if p.is_dir()):
        kind = kind_dir.name
        py_validator = PY_VALIDATORS.get(kind)
        if py_validator is None:
            failures.append(f"{kind}: no Python reference validator registered in runner.py")
            continue
        for verdict_dir in ("valid", "invalid"):
            for fixture in sorted((kind_dir / verdict_dir).glob("*.toml")):
                if fixture.name.endswith(".expected.toml"):
                    continue
                total += 1
                expect_reject = verdict_dir == "invalid"
                case_id = f"{kind}/{verdict_dir}/{fixture.name}"

                sidecar = fixture.with_suffix("").with_suffix(".expected.toml")
                expected_substrings: list[str] = []
                if sidecar.exists():
                    expected_substrings = tomllib.loads(sidecar.read_text()).get(
                        "error_contains", []
                    )

                runs = {
                    "rs": run_validator(
                        [args.rs, "--repo-root", args.repo_root, str(fixture)]
                    ),
                    "go": run_validator(
                        [args.go, "-repo-root", args.repo_root, str(fixture)]
                    ),
                    "py": run_validator(
                        [sys.executable, py_validator, str(fixture)]
                    ),
                }

                row = " ".join(f"{impl}={code}" for impl, (code, _) in runs.items())
                marks: list[str] = []
                for impl, (code, output) in runs.items():
                    if code == 2:
                        failures.append(
                            f"{case_id}: {impl} infrastructure error (exit 2):\n{output}"
                        )
                        continue
                    rejected = code != 0
                    if rejected != expect_reject:
                        want = "reject" if expect_reject else "accept"
                        message = f"{case_id}: {impl} should {want} but exited {code}"
                        reason = known.get((case_id, impl))
                        if reason is not None:
                            warnings.append(f"{message} [known divergence: {reason}]")
                            marks.append(f"{impl}:KNOWN")
                        else:
                            failures.append(message + (f"\n{output}" if output else ""))
                            marks.append(f"{impl}:FAIL")
                        continue
                    if expect_reject:
                        for needle in expected_substrings:
                            if needle.lower() not in output.lower():
                                failures.append(
                                    f"{case_id}: {impl} rejected but output lacks "
                                    f"`{needle}`:\n{output}"
                                )
                                marks.append(f"{impl}:MSG")
                status = ",".join(marks) if marks else "ok"
                print(f"  {case_id:<70} {row}  {status}")

    print(f"\nconformance: {total} cases")
    for warning in warnings:
        print(f"WARN {warning}")
    if failures:
        print(f"\nCONFORMANCE FAILED ({len(failures)} disagreement(s))")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("CONFORMANCE PASSED" + (f" ({len(warnings)} known divergence(s) tolerated)" if warnings else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
