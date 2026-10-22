#!/usr/bin/env python3
"""Check fixed runtime-document expectations in three independent validators."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "conformance"))
from runtime_specimens import FIELDS, dump, specimens, prepare_roots  # noqa: E402
from _runtime_validation import validate_document  # noqa: E402
from _vocabulary import load_catalog  # noqa: E402


def commands(case, path, root, rs, go):
    return {
        "python": [sys.executable, str(root / f"validators/validate_{case.kind.replace('-', '_')}.py"), "--repo-root", str(root), str(path)],
        "rust-auto": [str(rs), "--repo-root", str(root), str(path)],
        "rust-kind": [str(rs), "--repo-root", str(root), "--mode", case.kind, str(path)],
        "go-auto": [str(go), "--repo-root", str(root), str(path)],
        "go-kind": [str(go), "--repo-root", str(root), "--mode", case.kind, str(path)],
    }


def boundary_checks(root, work, rs, go, strace):
    """Trace syscall boundaries instead of assuming inert refs were not used."""
    results = []
    for case in specimens(root):
        if not case.name.endswith("/canonical") or case.kind == "gate-decision":
            continue
        doc = deepcopy(case.doc)
        marker = "issue74-inert-reference"
        if case.kind == "adapter-contract":
            doc["adapter"]["input_source"] = "https://example.invalid/" + marker
            doc["adapter"]["conformance_fixtures"] = [{"raw_input_ref": marker + ".raw", "expected_bundle_ref": marker + ".toml"}]
            doc["adapter"]["declared_invariants"][0]["enforced_by"] = marker + "-must-not-execute"
        else:
            doc["binding"]["registry_url"] = "https://example.invalid/" + marker
            doc["binding"]["adapter_ref"] = marker
            doc["binding"]["trust_anchor_refs"] = [{"anchor_id": marker}]
        path = work / (case.kind + "-boundary.toml")
        path.write_bytes(dump(doc))
        for language, command in commands(case, path, root, rs, go).items():
            trace = work / (case.kind + "-" + language + ".trace")
            # Explicit local test binaries and fixed routes, without a shell.
            proc = subprocess.run([str(strace), "-f", "-qq", "-s", "4096", "-e", "trace=%network,execve,execveat,openat,open",  # nosec B603 # noqa: S603
                                   "-o", str(trace), *command], cwd=root, capture_output=True, text=True, timeout=60,
                                  env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            text = trace.read_text() if trace.is_file() else ""
            executions = re.findall(r"\bexecve(?:at)?\(", text)
            # The trace selection contains only network, execution, and open calls.
            names = re.findall(r"(?:^|\n)(?:\[pid +[0-9]+\] +|[0-9]+ +)?([a-zA-Z0-9_]+)\(", text)
            network = [name for name in names if name not in {"execve", "execveat", "open", "openat"}]
            reference_opens = [line for line in text.splitlines() if re.search(r"\bopen(?:at)?\(", line) and marker in line]
            if proc.returncode or len(executions) != 1 or network or marker in text:
                raise AssertionError(f"{case.kind}/{language}: scope boundary failed or instrumentation did not run: {proc.stdout}{proc.stderr}")
            results.append({"kind": case.kind, "implementation": language, "executions": len(executions), "network_calls": len(network),
                            "reference_opens": len(reference_opens), "trace": str(trace), "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest()})
    if len(results) != 10:
        raise AssertionError("scope boundary instrument did not cover both new kinds and every dispatch route")
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--rs", required=True, type=Path)
    parser.add_argument("--go", required=True, type=Path)
    parser.add_argument("--strace", type=Path, default=shutil.which("strace"))
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    root, work = args.repo_root.resolve(), args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({"status": "incomplete", "skipped": []}) + "\n")
    rs, go = args.rs.resolve(), args.go.resolve()
    if not rs.is_file() or not go.is_file() or args.strace is None or not Path(args.strace).is_file():
        parser.error("fresh Rust and Go binaries plus strace are required; unavailable instrumentation is not a skipped pass")
    catalog = load_catalog(root)
    from check_database_vocabularies import source_identity
    from _contract import bundle_digest
    identity, digest = source_identity(root), bundle_digest(root)
    for kind, section, field, tokens, _ in FIELDS:
        attribute = {"id_derivation": "adapter_id_derivation", "verdict": "gate_decision_verdict"}.get(field, field)
        if catalog[attribute].extensible or set(tokens) != set(catalog[attribute].values):
            raise ValueError(f"independent expectations require review after a vocabulary change: {attribute}")
    cases = specimens(root)
    roots = prepare_roots(root, work / "trusted-inputs")
    observations, failures = [], []
    for index, case in enumerate(cases):
        path = work / f"specimen-{index:03}.toml"
        path.write_bytes(dump(case.doc))
        for language, command in commands(case, path, roots[case.root_mode], rs, go).items():
            proc = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=60)  # nosec B603 # noqa: S603
            text = proc.stdout + proc.stderr
            passed = ((proc.returncode == 0) == case.accepted and proc.returncode in {0, 1}
                      and (not case.needle or case.needle.lower() in text.lower()))
            observation = {"specimen": case.name, "owner": case.owner, "implementation": language,
                           "expected": "accept" if case.accepted else "reject", "exit_code": proc.returncode,
                           "passed": passed, "output": text}
            observations.append(observation)
            if not passed:
                failures.append(observation)
        if index % 40 == 0:
            print(f"checked {index + 1}/{len(cases)} runtime specimens", flush=True)
    if len(observations) != len(cases) * 5 or not any(case.accepted for case in cases) or all(case.accepted for case in cases):
        raise AssertionError("incomplete independent validator population")
    if failures:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps({"status": "failed", "failures": failures}, indent=2))
        for failure in failures:
            print(json.dumps(failure, ensure_ascii=True))
        return 1
    # Captured root validation must not reopen the root. The path now holds a
    # different invalid version; all checks still observe the supplied tree.
    case = next(case for case in cases if case.name == "adapter-contract/canonical")
    captured_path = work / "changed-after-capture.toml"
    captured_path.write_text("invalid TOML after capture")
    if validate_document(case.doc, captured_path, root, case.kind):
        raise AssertionError("captured-root validation reopened the changed root or rejected the fixed positive control")
    # File-less entry points must not launch anything or open any URL.
    with patch("subprocess.run", side_effect=AssertionError("validator executed a child process")):
        if validate_document(case.doc, captured_path, root, case.kind):
            raise AssertionError("captured-root validation failed its no-subprocess control")
    boundaries = boundary_checks(root, work, rs, go, Path(args.strace).resolve())
    if source_identity(root) != identity or bundle_digest(root) != digest:
        raise ValueError("trusted source changed during the runtime-document checks")
    receipt = {"status": "passed", "source": identity, "contract_bundle_sha256": digest, "specimen_count": len(cases),
               "expected_outcomes": observations, "scope_boundaries": boundaries, "skipped": [],
               "binaries": {str(path.relative_to(root)) if path.is_relative_to(root) else str(path):
                            hashlib.sha256(path.read_bytes()).hexdigest() for path in (rs, go)}}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=True, indent=2) + "\n")
    print(f"PASS: {len(cases)} fixed specimens across five routes; ten traced scope boundaries; skipped=[]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
