#!/usr/bin/env python3
"""Prove every conformance sidecar DISCRIMINATES rather than merely matches.

`conformance/runner.py` checks that each invalid case's `error_contains`
needles appear in its own output. That is necessary and not sufficient: a
needle can also appear in a DIFFERENT case's output, in which case it would
happily bless the wrong defect class, and the sidecar asserts far less than it
appears to.

This was found live. `hollow-proof.expected.toml` asserted only
`"RKM02"`, and the RKC02 diagnostic contains that string incidentally while
naming the invariants a proved record must face ("so that RKM02, RKM04 and
RKM06 apply to it"). Swapping the sidecar onto `mutation-claim/array-proof`
left the corpus green. A bare `"RKM04"` needle was worse, matching four other
cases.

This runs the whole cross-product: for every (sidecar, case) pair where the
case is not the sidecar's owner, the sidecar MUST NOT match. Where a sidecar
legitimately cannot discriminate, the pair is whitelisted below with a reason,
the same contract as known-divergences.toml.

Exit 0 all sidecars discriminate, 1 one or more do not, 2 infrastructure error.
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "validators"))
import _toml11 as tomllib  # noqa: E402

# Pairs that share a defect class by construction and cannot be separated by
# any message needle. They discriminate by VERDICT instead: see the reason.
ALLOWED_COLLISIONS = {
    frozenset({"array-proof.toml", "table-proof.toml"}): (
        "Same RKC02 defect, different TOML shape (table vs array of tables), so "
        "the diagnostic is identical by design. They discriminate by verdict: "
        "reverting Go's hasKey to tableOf reddens array-proof and leaves "
        "table-proof green, which is the bug the pair exists to catch."
    ),
}

# The discovered case directories define the governed kind population.
# The kind-layer reference validator per kind. The primaries dispatch on
# template_kind themselves, so they need no per-kind entry.
KIND_VALIDATOR = {
    "state-mutation": "validators/validate_state_mutation.py",
    "mutation-claim": "validators/validate_state_mutation.py",
    'adapter-contract': 'validators/validate_adapter_contract.py',
    'adapter-registry-binding': 'validators/validate_adapter_registry_binding.py',
    'gate-decision': 'validators/validate_gate_decision.py',
    "api-snapshot": "validators/validate_api_snapshot.py",
    "implementation-dag": "validators/validate_implementation_dag.py",
}


def discover_cases(root: pathlib.Path) -> list[pathlib.Path]:
    """The tree defines the population; sidecars cannot hide missing specimens."""
    directories = sorted(path for path in root.iterdir() if path.is_dir())
    if not directories:
        raise ValueError("no conformance kind directories discovered")
    missing = set(KIND_VALIDATOR) - {directory.name for directory in directories}
    if missing:
        raise ValueError(f"mapped kinds have no conformance directory: {sorted(missing)}")
    cases = []
    for directory in directories:
        if directory.name not in KIND_VALIDATOR:
            raise ValueError(f"kind has no KIND_VALIDATOR mapping: {directory.name}")
        for verdict in ("valid", "invalid"):
            files = sorted(path for path in (directory / verdict).glob("*.toml")
                           if not path.name.endswith(".expected.toml"))
            if not files:
                raise ValueError(f"{directory.name} has no {verdict} control")
            for side in (directory / verdict).glob("*.expected.toml"):
                if side.with_name(side.name.removesuffix(".expected.toml") + ".toml") not in files:
                    raise ValueError(f"orphan sidecar: {side}")
            if verdict == "invalid":
                for case in files:
                    if not case.with_suffix(".expected.toml").is_file():
                        raise ValueError(f"invalid specimen has no expected sidecar: {case}")
                cases.extend(files)
    return cases


def collect_output(case: pathlib.Path, rs: str, go: str, repo_root: str) -> str:
    text = ""
    kind_validator = KIND_VALIDATOR[case.parent.parent.name]
    commands = [
        [sys.executable, kind_validator, "--repo-root", repo_root, str(case)],
        [rs, "--repo-root", repo_root, str(case)],
        [go, "-repo-root", repo_root, str(case)],
        [sys.executable, "validators/validate_closure_root.py", "--repo-root", repo_root, str(case)],
    ]
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)  # nosec B603 # noqa: S603
        except FileNotFoundError:
            print(f"error: cannot execute {cmd[0]}", file=sys.stderr)
            raise SystemExit(2)
        text += proc.stdout + proc.stderr
    return text.lower()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rs", required=True)
    parser.add_argument("--go", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--cases", default="conformance/cases")
    args = parser.parse_args()

    try:
        cases = discover_cases(pathlib.Path(args.cases))
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    outputs = {c: collect_output(c, args.rs, args.go, args.repo_root) for c in cases}

    sidecars: dict[pathlib.Path, tuple[list[str], list[str]]] = {}
    for case in cases:
        side = case.with_suffix(".expected.toml")
        if not side.exists():
            raise AssertionError("discovered sidecar disappeared")
        doc = tomllib.loads(side.read_text())
        sidecars[case] = (
            doc.get("error_contains", []),
            doc.get("error_not_contains", []),
        )

    failures: list[str] = []
    for owner, (needles, forbidden) in sorted(sidecars.items()):
        if not needles:
            failures.append(f"{owner.name}: sidecar declares no error_contains")
            continue
        own = outputs[owner]
        if not all(needle.lower() in own for needle in needles) or any(word.lower() in own for word in forbidden):
            failures.append(f"{owner.name}: sidecar fails to match its own specimen")
        for other in cases:
            if other == owner:
                continue
            text = outputs[other]
            matches = all(n.lower() in text for n in needles) and not any(
                f.lower() in text for f in forbidden
            )
            if not matches:
                continue
            pair = frozenset({owner.name, other.name})
            if pair in ALLOWED_COLLISIONS:
                print(f"  ALLOWED  {owner.name} ~ {other.name}")
                continue
            failures.append(
                f"{owner.name}: its sidecar also matches {other.name}, so it does "
                f"not discriminate and could bless that defect class instead"
            )

    print(f"\ndiscrimination: {len(sidecars)} sidecar(s) over {len(cases)} case(s)")
    if failures:
        print(f"\nDISCRIMINATION FAILED ({len(failures)})")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("DISCRIMINATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
