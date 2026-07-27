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

# Kinds whose sidecars this check covers. Others have no sidecars yet.
KINDS = ("state-mutation", "mutation-claim")


def collect_output(case: pathlib.Path, rs: str, go: str, repo_root: str) -> str:
    text = ""
    commands = [
        [sys.executable, "validators/validate_state_mutation.py", "--repo-root", repo_root, str(case)],
        [rs, "--repo-root", repo_root, str(case)],
        [go, "-repo-root", repo_root, str(case)],
        [sys.executable, "validators/validate_closure_root.py", "--repo-root", repo_root, str(case)],
    ]
    for cmd in commands:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
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

    cases = [
        c
        for c in sorted(pathlib.Path(args.cases).glob("*/invalid/*.toml"))
        if not c.name.endswith(".expected.toml") and c.parent.parent.name in KINDS
    ]
    if not cases:
        print("error: no cases discovered", file=sys.stderr)
        return 2

    outputs = {c: collect_output(c, args.rs, args.go, args.repo_root) for c in cases}

    sidecars: dict[pathlib.Path, tuple[list[str], list[str]]] = {}
    missing: list[str] = []
    for case in cases:
        side = case.with_suffix("").with_suffix(".expected.toml")
        if not side.exists():
            missing.append(case.name)
            continue
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
    for name in missing:
        print(f"NOTE {name} has no sidecar (verdict-only case)")
    if failures:
        print(f"\nDISCRIMINATION FAILED ({len(failures)})")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("DISCRIMINATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
