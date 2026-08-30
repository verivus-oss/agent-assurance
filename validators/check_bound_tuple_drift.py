#!/usr/bin/env python3
"""Fail when the three implementations disagree about a SPEC 12.8.2 bound tuple.

A bound tuple is a digest, carried in a document, over a named set of that
document's own fields. The set is security-critical: a field outside it is not
committed to by the external proof, so two documents differing only in that
field share one tuple digest and the proof cannot tell them apart.

Until this gate existed the set was compiled into three implementations and
named nowhere a machine could read. Changing it meant editing
`validators/validate_state_mutation.py`, `tools/dagtoml-validate-rs/src/main.rs`
and `tools/dagtoml-validate-go/main.go`, with nothing comparing the three. A
partial edit produced two implementations computing one tuple and a third
computing another, over the same document, silently.

WHY THE IMPLEMENTATIONS STILL COMPILE IT IN
-------------------------------------------
The obvious alternative is to have all three READ the profile declaration at
run time. That is rejected on two grounds. It would make a producer-supplied
descriptor authoritative over what a producer's own document commits to, so a
third-party profile could shrink its own tuple. And it would collapse three
independent encodings into one, which is the property that makes a divergence
observable in the first place. This gate keeps the three copies and adds a
fourth, declarative statement they are all measured against, on the same
contract as the EXPECTED_COUNTS mirrors in `check_attribute_values.py`.

ORDER IS NOT COMPARED
---------------------
SPEC 12.8.2 sorts the records bytewise before hashing, so the tuple digest
depends on the field set and the values, never on declaration order. Sets are
compared; a pure reordering is not drift and is not reported as such.

USAGE
    python3 validators/check_bound_tuple_drift.py [--repo-root .]

Exit 0 when every implementation agrees with every declaration, 1 on drift,
2 on an infrastructure error. A source file that is missing, or a constant
this gate cannot locate, is an infrastructure error and never a pass: a
mirror gate that skips its subject has measured nothing.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _toml11 as tomllib  # noqa: E402

GIT = shutil.which("git")

# Each implementation's copy of the tuple, and how to find it. The block is
# sliced from the constant's name to its closing delimiter before any field is
# extracted, so a similarly shaped literal elsewhere in the file cannot be
# mistaken for it.
SOURCES = {
    "python": {
        "path": "validators/validate_state_mutation.py",
        "open": r"BOUND_TUPLE_FIELDS\s*=\s*\(",
        "close": r"\)",
        "field": r'"([A-Za-z0-9_.-]+)"',
    },
    "rust": {
        "path": "tools/dagtoml-validate-rs/src/main.rs",
        "open": r"BOUND_TUPLE_FIELDS\s*:\s*\[\([^\]]*\]\s*=\s*\[",
        "close": r"\];",
        "field": r'\(\s*"([A-Za-z0-9_.-]+)"\s*,',
    },
    "go": {
        "path": "tools/dagtoml-validate-go/main.go",
        "open": r"boundTupleFields\s*=\s*\[\]\[2\]string\{",
        "close": r"\n\}",
        "field": r'\{\s*"([A-Za-z0-9_.-]+)"\s*,',
    },
}


class Infrastructure(Exception):
    """The gate could not run, as distinct from finding drift."""


def profile_descriptors(root: pathlib.Path) -> list[pathlib.Path]:
    """Every tracked PROFILE.toml, derived from the tree rather than listed.

    A new profile that declares a bound tuple is pulled into scope by
    existing, which is the point: an enumeration written by hand goes stale
    the first time someone adds a profile.
    """
    out = subprocess.run(  # nosec B603  # noqa: S603
        [GIT, "ls-files", "-z", "profiles/*/PROFILE.toml"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if out.returncode != 0:
        raise Infrastructure(
            f"git ls-files failed under {root} (exit {out.returncode}): "
            + (out.stderr.strip() or "no stderr")
        )
    return [root / p for p in out.stdout.split("\0") if p]


def declared_tuples(root: pathlib.Path) -> dict[str, dict]:
    """Bound tuples declared across every profile descriptor, keyed by kind."""
    found: dict[str, dict] = {}
    for path in profile_descriptors(root):
        rel = path.relative_to(root).as_posix()
        try:
            doc = tomllib.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001
            raise Infrastructure(f"{rel}: could not parse: {exc}") from exc
        for index, entry in enumerate(doc.get("profile", {}).get("bound_tuples", [])):
            where = f"{rel}: [[profile.bound_tuples]] entry {index}"
            for key in ("contained_kind", "digest_field", "fields"):
                if key not in entry:
                    raise Infrastructure(f"{where} is missing `{key}`")
            kind = entry["contained_kind"]
            if kind in found:
                raise Infrastructure(
                    f"{where} declares a second bound tuple for `{kind}`, "
                    f"already declared in {found[kind]['where']}. A kind carries "
                    "at most one tuple; this gate compares by kind and cannot "
                    "tell two apart."
                )
            fields = entry["fields"]
            if not isinstance(fields, list) or not fields:
                raise Infrastructure(f"{where}.fields must be a non-empty array")
            if len(set(fields)) != len(fields):
                raise Infrastructure(f"{where}.fields contains a duplicate")
            found[kind] = {
                "fields": set(fields),
                "digest_field": entry["digest_field"],
                "where": where,
            }
    return found


def compiled_tuple(root: pathlib.Path, impl: str) -> set[str]:
    """The tuple one implementation actually compiles in."""
    spec = SOURCES[impl]
    path = root / spec["path"]
    if not path.is_file():
        raise Infrastructure(
            f"{spec['path']} is missing. This gate compares the three "
            "implementations against the declaration; it cannot report a pass "
            "over an implementation it did not read."
        )
    text = path.read_text()
    opener = re.search(spec["open"], text)
    if opener is None:
        raise Infrastructure(
            f"{spec['path']}: could not locate the bound-tuple constant. "
            "Either it was renamed, in which case update SOURCES here in the "
            "same change, or it was deleted, in which case that implementation "
            "no longer enforces SPEC 12.8.2."
        )
    closer = re.search(spec["close"], text[opener.end():])
    if closer is None:
        raise Infrastructure(
            f"{spec['path']}: found the constant but not the end of its block"
        )
    block = text[opener.end():opener.end() + closer.start()]
    fields = re.findall(spec["field"], block)
    if not fields:
        raise Infrastructure(
            f"{spec['path']}: the bound-tuple block parsed to zero fields. "
            "An empty tuple would commit to nothing."
        )
    if len(set(fields)) != len(fields):
        raise Infrastructure(f"{spec['path']}: duplicate field in the tuple")
    return set(fields)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    root = pathlib.Path(args.repo_root).resolve()

    if GIT is None:
        print("error: git not found on PATH", file=sys.stderr)
        return 2

    try:
        declared = declared_tuples(root)
        compiled = {impl: compiled_tuple(root, impl) for impl in SOURCES}
    except Infrastructure as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not declared:
        print(
            "error: no [[profile.bound_tuples]] declared in any profile "
            "descriptor, yet every implementation compiles a tuple in. Either "
            "the declaration was removed, or this gate is looking in the wrong "
            "place. Refusing to pass.",
            file=sys.stderr,
        )
        return 2

    # One tuple exists in the repository today. The implementations name their
    # constant once each and do not label it with a kind, so this gate can only
    # attribute a compiled tuple to a kind while there is exactly one. A second
    # declaration is a deliberate stop: generalise the constants to carry their
    # kind, then generalise this comparison, in the same change.
    if len(declared) != 1:
        print(
            f"error: {len(declared)} bound tuples are declared "
            f"({', '.join(sorted(declared))}), but each implementation exposes "
            "one unlabelled constant, so a compiled tuple can no longer be "
            "attributed to a kind. Make the constants carry their kind and "
            "generalise this gate in the same change.",
            file=sys.stderr,
        )
        return 2

    kind, decl = next(iter(declared.items()))
    print("bound-tuple mirror gate")
    print(f"  declared in             {decl['where']}")
    print(f"  kind                    {kind}")
    print(f"  digest carried in       {decl['digest_field']}")
    print(f"  fields declared         {len(decl['fields'])}")

    fail = False
    for impl in sorted(compiled):
        got = compiled[impl]
        if got == decl["fields"]:
            print(f"  {impl:<22}  {len(got)} fields, agrees")
            continue
        fail = True
        print(f"\nFAIL: {impl} ({SOURCES[impl]['path']}) disagrees with the "
              f"declaration in {decl['where']}:", file=sys.stderr)
        for extra in sorted(got - decl["fields"]):
            print(f"  + {extra}  compiled in but not declared", file=sys.stderr)
        for missing in sorted(decl["fields"] - got):
            print(f"  - {missing}  declared but not compiled in", file=sys.stderr)

    if fail:
        print(
            "\nA bound tuple that differs between implementations makes two of "
            "them compute a different digest over the same document. Decide "
            "which set is correct against spec.md SPEC 12.8.2, then change the "
            "declaration and all three implementations together.",
            file=sys.stderr,
        )
        return 1

    print("\nOK: the declaration and all three implementations name one field set")
    return 0


if __name__ == "__main__":
    sys.exit(main())
