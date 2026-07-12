#!/usr/bin/env python3
"""Validate the root-level `closure_root` field required by SPEC §12.

The closure-root rule (SPEC §12) mandates that every conforming
DAG-TOML document carry a root-level `closure_root` field whose value
is a `<algorithm>:<lowercase-hex-digest>` digest over the canonical
concatenation of upstream artifact hashes and upstream revocation
snapshots. This validator enforces the spec-layer source-hash subset
that is currently machine-declared in DAG-TOML:

  1. The field is present at the document root (not nested under
     `[meta]` or any other table).
  2. The value is a non-empty string of shape
     `<algo>:<lowercase-hex>` where `<algo>` is drawn from the closed
     set declared in `core/ontology.toml` under the
     `closure_root.digest_algorithm` attribute vocabulary
     (`sha256` | `sha384` | `sha512`).
  3. The hex digest length matches the declared algorithm
     (64 / 96 / 128 lowercase hex chars).
  4. Forbidden weaker algorithms (`md5`, `sha1`) are explicitly
     rejected with a pointed error message.
  5. `[provenance].source_sha256`, when present, is folded into the
     canonical closure input stream and must produce the declared
     `closure_root`.

A document that has no upstream evidence MUST still emit the
canonical empty-closure sentinel `sha256:e3b0…b855` (the SHA-256 of
zero bytes). Kind-specific `cites_upstream` fields and revocation
snapshots remain profile/runtime-layer work until their canonical
record forms are promoted into SPEC §12.8.

Exit code 0 on pass; 1 on any violation.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py

ALGO_HEX_LENGTHS = {
    "sha256": 64,
    "sha384": 96,
    "sha512": 128,
}

FORBIDDEN_ALGOS = ("md5", "sha1")

CLOSURE_ROOT_RE = re.compile(r"^([a-z0-9]+):([0-9a-f]+)$")

EMPTY_CLOSURE_SENTINELS = {
    "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "sha384:38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da274edebfe76f65fbd51ad2f14898b95b",
    "sha512:cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
}

# SPEC §12.8.1: profile-pinned closure records. The pin map is keyed by
# `template_kind` (kind names are namespace-partitioned per SPEC §6.1,
# so a kind maps to at most one profile). Built from every
# `profiles/*/PROFILE.toml` under --repo-root, with `closure_records`
# unioned across `extends` like `contained_kinds`. Declaration-shape
# enforcement (INV07) belongs to validate_profile_descriptor.py; this
# module consumes well-formed declarations.
PINNED_VALUE_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def load_pinned_records(
    repo_root: pathlib.Path,
) -> dict[str, list[tuple[str, str, str]]]:
    """Return {template_kind: [(field, presence, profile_name), ...]}."""
    descriptors: dict[str, dict] = {}
    profiles_dir = repo_root / "profiles"
    if profiles_dir.is_dir():
        for entry in sorted(profiles_dir.iterdir()):
            candidate = entry / "PROFILE.toml"
            if not candidate.is_file():
                continue
            try:
                doc = tomllib.loads(candidate.read_text())
            except (OSError, tomllib.TOMLDecodeError):
                continue
            meta = doc.get("meta") or {}
            if meta.get("template_kind") != "profile-descriptor":
                continue
            profile = doc.get("profile") or {}
            name = profile.get("name")
            if isinstance(name, str):
                descriptors[name] = profile

    pin_map: dict[str, list[tuple[str, str, str]]] = {}
    for name in descriptors:
        seen: set[str] = set()

        def visit(node: str) -> None:
            if node in seen or node not in descriptors:
                return
            seen.add(node)
            profile = descriptors[node]
            records = profile.get("closure_records")
            if isinstance(records, list):
                for record in records:
                    if not isinstance(record, dict):
                        continue
                    kind = record.get("contained_kind")
                    field = record.get("field")
                    presence = record.get("presence")
                    if (
                        isinstance(kind, str)
                        and isinstance(field, str)
                        and presence in ("required", "when-present")
                    ):
                        existing = pin_map.setdefault(kind, [])
                        # Dedup by (field, presence) only: a record
                        # inherited through `extends` reaches this map
                        # once per extending root, but its record string
                        # excludes the profile name, so keying dedup on
                        # the profile would double-emit the record and
                        # corrupt the digest stream.
                        if not any(
                            f == field and pr == presence for f, pr, _ in existing
                        ):
                            existing.append((field, presence, name))
            for child in profile.get("extends", []) or []:
                if isinstance(child, str):
                    visit(child)

        visit(name)
    for records_list in pin_map.values():
        records_list.sort()
    return pin_map


def _loaded_profile_names(repo_root: pathlib.Path) -> frozenset[str]:
    """Names of every loadable profile-descriptor (SPEC §12.8.1 pin
    resolution: a pinned-kind document's framework_profile must resolve
    to one of these)."""
    names: set[str] = set()
    profiles_dir = repo_root / "profiles"
    if profiles_dir.is_dir():
        for entry in sorted(profiles_dir.iterdir()):
            candidate = entry / "PROFILE.toml"
            if not candidate.is_file():
                continue
            try:
                doc = tomllib.loads(candidate.read_text())
            except (OSError, tomllib.TOMLDecodeError):
                continue
            meta = doc.get("meta") or {}
            profile = doc.get("profile") or {}
            name = profile.get("name")
            if meta.get("template_kind") == "profile-descriptor" and isinstance(
                name, str
            ):
                names.add(name)
    return frozenset(names)


def _walk_field(data: dict, dotted: str):
    current = data
    for segment in dotted.split("."):
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current


def pinned_closure_inputs(
    data: dict,
    pin_map: dict[str, list[tuple[str, str, str]]],
    loaded_profiles: frozenset[str],
) -> tuple[list[str], list[str]]:
    """SPEC §12.8.1 record emission + pin resolution for one document.

    Pins resolve by template_kind over the full loaded descriptor set,
    in EVERY mode that validates closure_root; a document of a pinned
    kind with a missing/unresolvable framework_profile is rejected.
    There is no pin-free fall-through for a pinned kind.
    """
    meta = data.get("meta")
    if not isinstance(meta, dict):
        return [], []
    template_kind = meta.get("template_kind")
    if not isinstance(template_kind, str):
        template_kind = meta.get("kind")  # legacy synonym
    if not isinstance(template_kind, str) or template_kind not in pin_map:
        return [], []

    errors: list[str] = []
    framework_profile = meta.get("framework_profile")
    if not isinstance(framework_profile, str) or not framework_profile:
        errors.append(
            f"documents of pinned kind `{template_kind}` MUST declare "
            f"`meta.framework_profile` (SPEC §12.8.1 pin resolution)"
        )
    elif framework_profile not in loaded_profiles:
        errors.append(
            f"`meta.framework_profile` `{framework_profile}` does not "
            f"resolve to a loaded profile-descriptor (SPEC §12.8.1 pin "
            f"resolution; pinned kind `{template_kind}`)"
        )

    records: list[str] = []
    for field, presence, profile_name in pin_map[template_kind]:
        value = _walk_field(data, field)
        if value is None:
            if presence == "required":
                errors.append(
                    f"pinned closure record `{field}` (required by profile "
                    f"`{profile_name}`, SPEC §12.8.1) is missing"
                )
            continue
        if not isinstance(value, str) or not PINNED_VALUE_RE.match(value):
            errors.append(
                f"pinned closure record `{field}` must match "
                f"`sha256:<64 lowercase hex chars>` (SPEC §12.8.1), "
                f"got {value!r}"
            )
            continue
        records.append(f"{field} {value}\n")
    return records, errors


def canonical_source_hash_inputs(data: dict) -> tuple[list[str], list[str]]:
    """Return canonical SPEC-layer closure records and shape errors.

    At schema_version 0.1.0 the byte-level algorithm is pinned for the
    cross-kind source hash every DAG-TOML document can declare:

        provenance.source_sha256 <sha256:lowercase-hex>\n

    Records are sorted before hashing so future repeated source-hash
    inputs have deterministic order.
    """
    provenance = data.get("provenance")
    if not isinstance(provenance, dict):
        return [], []

    raw = provenance.get("source_sha256")
    if raw is None:
        return [], []
    if not isinstance(raw, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", raw):
        return [], [
            "`[provenance].source_sha256`, when present, must match "
            "`sha256:<64 lowercase hex chars>`"
        ]
    return [f"provenance.source_sha256 {raw}\n"], []


def expected_closure_root(algo: str, records: list[str]) -> str:
    stream = "".join(sorted(records)).encode("utf-8")
    digest = hashlib.new(algo)
    digest.update(stream)
    return f"{algo}:{digest.hexdigest()}"


def validate(
    path: pathlib.Path,
    pin_map: dict[str, list[tuple[str, str, str]]] | None = None,
    loaded_profiles: frozenset[str] = frozenset(),
) -> list[str]:
    errors: list[str] = []
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"{path}: cannot parse TOML ({exc})"]

    if "closure_root" not in data:
        return [
            f"{path}: missing required root-level `closure_root` field "
            f"(SPEC §12.1). Self-contained documents MUST use the "
            f"empty-closure sentinel "
            f"`sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`."
        ]

    value = data["closure_root"]
    if not isinstance(value, str) or not value:
        errors.append(
            f"{path}: `closure_root` must be a non-empty string, "
            f"got {type(value).__name__}: {value!r}"
        )
        return errors

    match = CLOSURE_ROOT_RE.match(value)
    if not match:
        errors.append(
            f"{path}: `closure_root` must match `<algo>:<lowercase-hex-digest>` "
            f"(SPEC §12.1). Got: {value!r}"
        )
        return errors

    algo, hexpart = match.group(1), match.group(2)

    if algo in FORBIDDEN_ALGOS:
        errors.append(
            f"{path}: `closure_root` uses forbidden weak digest "
            f"algorithm `{algo}`. SPEC §12.1 forbids MD5 and SHA-1 — "
            f"use SHA-256 or stronger."
        )
        return errors

    expected_len = ALGO_HEX_LENGTHS.get(algo)
    if expected_len is None:
        errors.append(
            f"{path}: `closure_root` uses unknown digest algorithm "
            f"`{algo}`. Allowed at SPEC §12.1: "
            f"{sorted(ALGO_HEX_LENGTHS)}."
        )
        return errors

    if len(hexpart) != expected_len:
        errors.append(
            f"{path}: `closure_root` digest hex length is "
            f"{len(hexpart)} chars; algorithm `{algo}` requires "
            f"{expected_len}."
        )

    records, input_errors = canonical_source_hash_inputs(data)
    pinned_records, pinned_errors = pinned_closure_inputs(
        data, pin_map or {}, loaded_profiles
    )
    records = records + pinned_records
    input_errors = input_errors + pinned_errors
    for err in input_errors:
        errors.append(f"{path}: {err}")
    if input_errors:
        return errors

    expected = expected_closure_root(algo, records)
    if value != expected:
        if records:
            errors.append(
                f"{path}: `closure_root` does not match SPEC §12.8 "
                f"source-hash closure. Expected `{expected}` from "
                f"{len(records)} canonical source-hash input(s), got `{value}`."
            )
        else:
            errors.append(
                f"{path}: self-contained documents MUST use the "
                f"canonical empty-closure sentinel `{expected}`; got `{value}`."
            )

    return errors


ALWAYS_SPEC_RESERVED_KINDS = frozenset({
    # Meta kinds — the kind that describes other kinds, plus the
    # ontology kind used by `core/ontology.toml` and friends. Both
    # are spec-layer infrastructure, not declared via a separate
    # `*-kind.toml` descriptor.
    "kind-descriptor",
    "ontology",
})


def _kind_name_from_descriptor(path: pathlib.Path) -> str | None:
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return None
    kind = data.get("kind")
    if isinstance(kind, dict):
        name = kind.get("name")
        if isinstance(name, str):
            return name
    return None


def spec_reserved_kinds(repo_root: pathlib.Path) -> frozenset[str]:
    """Build the closed set of spec-reserved `template_kind` values.

    A spec-reserved kind is one declared by a `*-kind.toml` descriptor
    under `core/` or under any spec-reserved profile's directory
    (`profiles/<name>/*-kind.toml`), plus the two meta kinds
    (`kind-descriptor`, `ontology`). The set is the conformance
    scope of the closure-root rule (SPEC §12.1).

    Discovering the set dynamically (instead of hardcoding it)
    means new kinds added by future spec/profile work
    automatically come under §12 the moment their `*-kind.toml`
    descriptor lands.
    """
    found: set[str] = set(ALWAYS_SPEC_RESERVED_KINDS)
    for descriptor in (repo_root / "core").glob("*-kind.toml"):
        name = _kind_name_from_descriptor(descriptor)
        if name:
            found.add(name)
    profiles_dir = repo_root / "profiles"
    if profiles_dir.exists():
        for descriptor in profiles_dir.glob("*/*-kind.toml"):
            name = _kind_name_from_descriptor(descriptor)
            if name:
                found.add(name)
    return frozenset(found)


def is_conforming_toml(path: pathlib.Path, spec_reserved: frozenset[str]) -> bool:
    """A conforming DAG-TOML document declares a spec-reserved
    `[meta].template_kind`.

    The closure-root rule (SPEC §12) applies to every such document.
    Process-artifact TOMLs (review bundles, claim-analysis runs,
    ad-hoc local-tool documents using non-spec-reserved `template_kind`
    values) are out of conformance scope and skipped silently.
    """
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return False
    meta = data.get("meta")
    if not isinstance(meta, dict):
        return False
    tk = meta.get("template_kind")
    return isinstance(tk, str) and tk in spec_reserved


def discover_conforming(
    roots: list[pathlib.Path],
    spec_reserved: frozenset[str],
) -> list[pathlib.Path]:
    """Find every conforming DAG-TOML document under the given roots.

    Walks each root recursively, skips hidden directories and any
    `target/` build output, parses each `*.toml` once to check
    whether its `[meta].template_kind` is spec-reserved. The cost is one
    TOML parse per candidate file; for the public spec repo that's
    well under a second.
    """
    out: list[pathlib.Path] = []
    skip_dirs = {"target", "node_modules", "__pycache__"}
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            if root.suffix == ".toml" and is_conforming_toml(root, spec_reserved):
                out.append(root)
            continue
        for path in sorted(root.rglob("*.toml")):
            if any(part.startswith(".") or part in skip_dirs for part in path.parts):
                continue
            if is_conforming_toml(path, spec_reserved):
                out.append(path)
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate root-level `closure_root` per SPEC §12.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "TOML file(s) to validate. Ignored when --discover is given."
        ),
    )
    parser.add_argument(
        "--discover",
        nargs="+",
        metavar="ROOT",
        help=(
            "Discover every conforming DAG-TOML document under each ROOT "
            "(recursively) and validate them all. A conforming document "
            "is any TOML whose `[meta].template_kind` is one of the kinds "
            "declared by `core/*-kind.toml`, by any spec-reserved profile's "
            "`*-kind.toml` (under `profiles/<name>/`), or is the meta kind "
            "`kind-descriptor` / `ontology`. Process-artifact TOMLs that "
            "use non-spec-reserved `template_kind` values are skipped. Use this "
            "in CI so new kind descriptors / profiles / examples can't "
            "regress the §12 rule by not appearing in a hand-maintained "
            "list."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help=(
            "Repository root containing `core/*-kind.toml` and "
            "`profiles/<name>/*-kind.toml` (used by --discover to "
            "derive the spec-reserved kind set). Defaults to the current "
            "working directory."
        ),
    )
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root).resolve()
    pin_map = load_pinned_records(repo_root)
    loaded_profiles = _loaded_profile_names(repo_root)

    if args.discover:
        spec_reserved = spec_reserved_kinds(repo_root)
        targets = discover_conforming(
            [pathlib.Path(r) for r in args.discover], spec_reserved
        )
        if not targets:
            print(
                "CLOSURE-ROOT VALIDATION: no conforming TOMLs found "
                f"under {args.discover} for spec-reserved kinds={sorted(spec_reserved)}.",
                file=sys.stderr,
            )
            return 1
    else:
        if not args.paths:
            parser.error("provide TOML paths or use --discover ROOT [ROOT ...].")
        targets = [pathlib.Path(p) for p in args.paths]

    failures: list[str] = []
    checked = 0
    for path in targets:
        if not path.exists():
            failures.append(f"{path}: does not exist")
            continue
        checked += 1
        failures.extend(validate(path, pin_map, loaded_profiles))

    if failures:
        for f in failures:
            print(f"FAIL {f}", file=sys.stderr)
        print(
            f"\nCLOSURE-ROOT VALIDATION FAILED: {len(failures)} "
            f"error(s) across {checked} file(s).",
            file=sys.stderr,
        )
        return 1

    print(f"CLOSURE-ROOT VALIDATION PASSED ({checked} file(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
