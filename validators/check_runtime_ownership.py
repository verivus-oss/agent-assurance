#!/usr/bin/env python3
"""Audit descriptor dispositions and require executed evidence for new owners."""

import argparse
import json
import hashlib
from copy import deepcopy
import uuid
from pathlib import Path
import sys

import _toml11 as toml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference/database"))
from _contract import bundle_digest, load_mapping  # noqa: E402


def declarations(root):
    load_mapping(root)
    mapping = toml.loads((root / "reference/database/vocabulary-storage.toml").read_text())
    descriptors = {path.relative_to(root).as_posix(): toml.loads(path.read_text())["kind"]
                   for pattern in ("core/*-kind.toml", "profiles/*/*-kind.toml") for path in sorted(root.glob(pattern))}
    deferred, sections, scoped = {}, set(), {}
    for path, kind in descriptors.items():
        ids = []
        for invariant in kind.get("hard_invariants", []):
            identity = (path, invariant["id"])
            ids.append(invariant["id"])
            owner = invariant["enforced_by"]
            if "(planned)" in owner:
                if (root / owner.removesuffix(" (planned)")).is_file():
                    raise ValueError(f"stale planned marker names a shipped validator: {identity!r}")
                deferred[identity] = owner
            if kind["name"] in {"adapter-contract", "adapter-registry-binding"}:
                scoped[(kind["name"], invariant["id"])] = owner
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate invariant ID in {path}")
        for section in kind.get("required_sections", []):
            identity = (path, section["table"])
            if identity in sections:
                raise ValueError(f"duplicate required section: {identity!r}")
            sections.add(identity)
    ledger = mapping.get("deferred_invariants", [])
    actual = {(row["descriptor"], row["id"]): row["enforced_by"] for row in ledger}
    if len(actual) != len(ledger) or actual != deferred or any(not row.get("follow_up") or not row.get("reason") for row in ledger):
        raise ValueError("deferred invariant ledger is incomplete, stale, duplicated, or lacks a reviewed reason")
    section_rows = mapping.get("required_section_dispositions", [])
    actual_sections = {(row["descriptor"], row["table"]) for row in section_rows}
    if len(actual_sections) != len(section_rows) or actual_sections != sections:
        raise ValueError("required-section disposition ledger does not cover the descriptor tree exactly")
    for row in section_rows:
        adapter_section = row["descriptor"].endswith("/adapter-contract-kind.toml")
        expected = "implemented" if adapter_section else "residual"
        if row.get("status") != expected:
            raise ValueError("required-section disposition claims an unimplemented obligation")
        if not adapter_section:
            followup = "enforce-gate-decision-cited-bundles" if row["descriptor"].endswith("/gate-decision-kind.toml") else "audit-required-section-instance-enforcement"
            if row.get("follow_up") != followup:
                raise ValueError("required-section residual lost its explicit follow-up")
    owners = mapping.get("invariant_owners", [])
    actual_owners = {(row["kind"], row["id"]) for row in owners}
    if len(actual_owners) != len(owners) or actual_owners != set(scoped):
        raise ValueError("new-kind invariant ownership ledger is incomplete, stale, or duplicated")
    routes = {"python", "rust-auto", "rust-kind", "go-auto", "go-kind"}
    for row in owners:
        scope = row["id"] == "INV04"
        if row.get("disposition") != ("scope-boundary" if scope else "implemented"):
            raise ValueError("computational invariant cannot be exempted as a scope boundary")
        python_owner = "validators/validate_" + row["kind"].replace("-", "_") + ".py"
        expected_owner = "scope declaration; no validator action" if scope else python_owner
        if (scoped[(row["kind"], row["id"])] != expected_owner or row.get("python_owner") != python_owner
                or not (root / python_owner).is_file() or set(row.get("implementations", [])) != routes):
            raise ValueError("new invariant owner is missing or does not cover every implementation route")
    return {"descriptor_files": len(descriptors), "deferred_invariants": len(deferred),
            "required_sections": len(sections), "new_invariant_owners": len(owners)}, owners


def executed(root, path, owners):
    from check_database_vocabularies import source_identity
    receipt = json.loads(path.read_text())
    if (receipt.get("status") != "passed" or receipt.get("skipped") != []
            or receipt.get("source") != source_identity(root) or receipt.get("contract_bundle_sha256") != bundle_digest(root)):
        raise ValueError("missing or stale runtime-document execution receipt")
    sys.path.insert(0, str(root / "conformance"))
    from runtime_specimens import specimens
    routes = {"python", "rust-auto", "rust-kind", "go-auto", "go-kind"}
    cases = specimens(root)
    expected = {(case.name, route): case for case in cases for route in routes}
    outcomes = receipt.get("expected_outcomes", [])
    if (receipt.get("specimen_count") != len(cases) or len(outcomes) != len(expected)
            or {(row["specimen"], row["implementation"]) for row in outcomes} != set(expected)):
        raise ValueError("runtime receipt lost an independently expected specimen or route")
    for row in outcomes:
        case = expected[(row["specimen"], row["implementation"])]
        if (row.get("expected") != ("accept" if case.accepted else "reject") or row.get("exit_code") != (0 if case.accepted else 1)
                or row.get("owner") != case.owner or row.get("passed") is not True
                or (case.needle and case.needle.lower() not in row.get("output", "").lower())):
            raise ValueError("runtime receipt lacks the intended verdict and diagnostic")
    if len(receipt.get("binaries", {})) != 2:
        raise ValueError("runtime receipt is missing a primary validator binary")
    for name, digest in receipt["binaries"].items():
        binary = root / name
        if not binary.is_file() or hashlib.sha256(binary.read_bytes()).hexdigest() != digest:
            raise ValueError("runtime receipt refers to a missing or stale binary")
    for row in receipt.get("scope_boundaries", []):
        trace = Path(row.get("trace", ""))
        if not trace.is_file() or hashlib.sha256(trace.read_bytes()).hexdigest() != row.get("trace_sha256"):
            raise ValueError("runtime receipt refers to a missing or stale syscall trace")
    for row in owners:
        for implementation in row["implementations"]:
            if row["disposition"] == "scope-boundary":
                witnesses = [item for item in receipt.get("scope_boundaries", [])
                             if item["kind"] == row["kind"] and item["implementation"] == implementation]
                if len(witnesses) != 1 or any(witnesses[0].get(name) != value for name, value in
                                             (("executions", 1), ("network_calls", 0), ("reference_opens", 0))):
                    raise ValueError("scope boundary lacks its executed syscall instrument")
            else:
                witnesses = [item for item in receipt.get("expected_outcomes", [])
                             if item["specimen"].startswith(row["kind"] + "/") and item["owner"] == row["fixture_owner"]
                             and item["implementation"] == implementation]
                if {item["expected"] for item in witnesses} != {"accept", "reject"} or not all(item["passed"] for item in witnesses):
                    raise ValueError(f"invariant has no independent positive and negative fixture evidence: {row['kind']}/{row['id']}/{implementation}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--declarations-only", action="store_true")
    group.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    try:
        counts, owners = declarations(root)
        if args.receipt:
            executed(root, args.receipt, owners)
            receipt_controls(root, args.receipt, owners)
    except (ValueError, KeyError, OSError) as exc:
        print("FAIL: " + str(exc))
        return 1
    print("Compared discovered descriptors with exact disposition ledgers" +
          ("; skipped executed ownership checks (partial declarations-only run)" if args.declarations_only else "; executed every new owner in every route; skipped=[]"))
    print(json.dumps(counts, sort_keys=True))
    return 0


def receipt_controls(root, path, owners):
    original = json.loads(path.read_text())
    work = root / ".local/runtime-ownership-controls" / uuid.uuid4().hex
    work.mkdir(parents=True)
    controls = []
    for name, edit, needle in (
        ("zero-specimens", lambda row: row.update(specimen_count=0, expected_outcomes=[]), "expected specimen"),
        ("missing-route", lambda row: row["expected_outcomes"].pop(), "expected specimen"),
        ("wrong-diagnostic", lambda row: next(item for item in row["expected_outcomes"] if item["expected"] == "reject").update(output="unrelated failure"), "verdict and diagnostic"),
        ("missing-boundary", lambda row: row["scope_boundaries"].pop(), "syscall instrument"),
        ("network-side-effect", lambda row: row["scope_boundaries"][0].update(network_calls=1), "syscall instrument"),
        ("stale-binary", lambda row: row["binaries"].update({next(iter(row["binaries"])): "0" * 64}), "stale binary"),
        ("missing-trace", lambda row: row["scope_boundaries"][0].update(trace="absent-trace"), "stale syscall trace"),
    ):
        receipt = deepcopy(original)
        edit(receipt)
        candidate = work / (name + ".json")
        candidate.write_text(json.dumps(receipt))
        try:
            executed(root, candidate, owners)
        except ValueError as exc:
            if needle not in str(exc):
                raise AssertionError("receipt control failed for an unrelated reason: " + str(exc)) from exc
            controls.append({"control": name, "status": "rejected", "output": str(exc)})
        else:
            raise AssertionError("ownership receipt control survived: " + name)
    (work / "controls.json").write_text(json.dumps(controls, indent=2))
    print(f"Verified {len(controls)} runtime receipt failure controls against the complete passing receipt")


if __name__ == "__main__":
    raise SystemExit(main())
