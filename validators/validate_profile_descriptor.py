#!/usr/bin/env python3
"""Validate a DAG-TOML profile-descriptor file.

A profile-descriptor is a TOML document whose `[meta].template_kind`
is `"profile-descriptor"`. It documents a profile per spec.md §6.1
and is the only artifact that declares profile inheritance
(`[profile].extends`) and namespacing posture
(`[profile].namespace`) in machine-readable form.

This validator enforces the hard invariants INV01..INV05 listed in
`core/profile-descriptor-kind.toml`:

  INV01 — namespace partition consistency:
          namespace == "spec.reserved"   iff   name matches ^[a-z][a-z0-9-]*$
          (unprefixed kebab-case)
          otherwise namespace MUST be a strict reverse-DNS prefix of name
          (matches ^[a-z][a-z0-9-]*(\\.[a-z][a-z0-9-]*)+$).
  INV02 — `extends` is acyclic.
  INV03 — every entry of `extends` resolves to a loaded profile-descriptor.
  INV04 — `ontology` points at an existing file with
          `[meta].template_kind = "ontology"`.
  INV05 — every entry of `contained_kinds` resolves to a `*-kind.toml`
          under repo root whose `[meta].describes_kind` matches the entry.

  INV08: `bound_tuples` entries (spec.md §12.8.2) are well-formed:
          exactly the keys contained_kind/digest_field/fields;
          contained_kind is in the post-`extends`-union contained_kinds
          and declares at most one tuple; digest_field and every member
          of fields match the frozen path grammar; fields is non-empty
          and repeats nothing; and neither digest_field nor closure_root
          appears in fields.

  INV07: `closure_records` entries (spec.md §12.8.1) are well-formed:
          exactly the keys contained_kind/field/presence; contained_kind
          is in the post-`extends`-union contained_kinds; field matches
          the frozen path grammar and is not closure_root,
          provenance.source_sha256, a `meta.*` path, or a §12.9 posture
          field; presence is "required" or "when-present"; and no
          duplicate (contained_kind, field) pair survives the
          post-`extends` union. (INV06 is the IJB ontology-resolution
          invariant, enforced by validate_ijb_conformance.py.)

The validator loads every profile-descriptor it finds under
`profiles/*/PROFILE.toml`; for each file under validation, that file
itself (and only it) is merged into the resolution set, matching the
primaries' fall-back semantics (U10 review fix 3).
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py


# \Z, not $: Python's $ also matches before a trailing newline; rs/go
# reject such names, so $ would be a cross-implementation divergence
# (U10 review round 2, R2-1).
UNPREFIXED_RE = re.compile(r"^[a-z][a-z0-9-]*\Z")
REVERSE_DNS_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+\Z")

REQUIRED_PROFILE_FIELDS = (
    "name",
    "namespace",
    "owner",
    "license",
    "extends",
    "ontology",
    "contained_kinds",
)

# INV07 (spec.md §12.8.1): profile-pinned closure records.
CLOSURE_RECORD_KEYS = ("contained_kind", "field", "presence")
CLOSURE_RECORD_PRESENCE = ("required", "when-present")
# \Z, not $: see the equivalent note in validate_closure_root.py
# (Python's $ tolerates a trailing newline; rs/go do not).
CLOSURE_RECORD_FIELD_RE = re.compile(r"^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*\Z")
CLOSURE_RECORD_FORBIDDEN_FIELDS = (
    "closure_root",
    "provenance.source_sha256",
)
POSTURE_FIELDS = ("confidentiality", "license", "embargo_until")

BOUND_TUPLE_KEYS = ("contained_kind", "digest_field", "fields")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a DAG-TOML profile-descriptor file.",
    )
    parser.add_argument("files", nargs="+", help="profile descriptor TOML files")
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Repository root (used to resolve ontology + contained-kinds paths).",
    )
    return parser.parse_args()


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def discover_descriptors(repo_root: pathlib.Path) -> dict[str, tuple[pathlib.Path, dict]]:
    """Discover every profile-descriptor under `profiles/*/PROFILE.toml`."""
    found: dict[str, tuple[pathlib.Path, dict]] = {}
    profiles_dir = repo_root / "profiles"
    if not profiles_dir.is_dir():
        return found
    for entry in sorted(profiles_dir.iterdir()):
        candidate = entry / "PROFILE.toml"
        if not candidate.is_file():
            continue
        try:
            doc = load_toml(candidate)
        except tomllib.TOMLDecodeError:
            continue
        meta = doc.get("meta") or {}
        if meta.get("template_kind") != "profile-descriptor":
            continue
        profile = doc.get("profile") or {}
        name = profile.get("name")
        if isinstance(name, str):
            found[name] = (candidate, doc)
    return found


def check_namespace_partition(name: str, namespace: str) -> list[str]:
    errors: list[str] = []
    is_unprefixed = bool(UNPREFIXED_RE.match(name))
    is_reverse_dns = bool(REVERSE_DNS_RE.match(name))
    if not (is_unprefixed or is_reverse_dns):
        errors.append(
            f"[profile].name `{name}` does not match the SPEC §2.5 namespacing "
            f"partition (must be unprefixed kebab-case for spec-reserved profiles, "
            f"or a reverse-DNS name for non-spec-reserved profiles)"
        )
        return errors
    if is_unprefixed:
        if namespace != "spec.reserved":
            errors.append(
                f"[profile].namespace `{namespace}` is inconsistent with "
                f"unprefixed name `{name}` (SPEC §2.5: unprefixed names are "
                f"reserved for spec-reserved profiles, which MUST declare "
                f"`namespace = \"spec.reserved\"`)"
            )
    else:
        # reverse-DNS
        if namespace == "spec.reserved":
            errors.append(
                f"[profile].namespace = \"spec.reserved\" is not permitted for "
                f"reverse-DNS name `{name}` (SPEC §2.5: `spec.reserved` is for "
                f"spec-reserved unprefixed profiles)"
            )
        elif not name.startswith(namespace + "."):
            errors.append(
                f"[profile].namespace `{namespace}` is not a strict reverse-DNS "
                f"prefix of name `{name}` (SPEC §2.5)"
            )
    return errors


def effective_profile_sets(
    name: str,
    descriptors: dict[str, tuple[pathlib.Path, dict]],
) -> tuple[set[str], list[tuple[str, dict]]]:
    """Union `contained_kinds` and `closure_records` across the
    `extends` graph rooted at `name` (spec.md §6.1 rules 3 and 4).
    Returns (effective_kinds, [(declaring_profile, record), ...])."""
    kinds: set[str] = set()
    records: list[tuple[str, dict]] = []
    seen: set[str] = set()

    def visit(node: str) -> None:
        if node in seen or node not in descriptors:
            return
        seen.add(node)
        _, doc = descriptors[node]
        profile = doc.get("profile") or {}
        for slug in profile.get("contained_kinds", []) or []:
            if isinstance(slug, str):
                kinds.add(slug)
        recs = profile.get("closure_records")
        if isinstance(recs, list):
            for rec in recs:
                if isinstance(rec, dict):
                    records.append((node, rec))
        for child in profile.get("extends", []) or []:
            if isinstance(child, str):
                visit(child)

    visit(name)
    return kinds, records


def effective_bound_tuples(
    name: str,
    descriptors: dict[str, tuple[pathlib.Path, dict]],
) -> list[tuple[str, dict]]:
    """Union `bound_tuples` across the `extends` graph rooted at `name`.

    Separate from effective_profile_sets so that function keeps the shape
    the two primaries mirror. Returns [(declaring_profile, tuple), ...].
    """
    tuples: list[tuple[str, dict]] = []
    seen: set[str] = set()

    def visit(node: str) -> None:
        if node in seen or node not in descriptors:
            return
        seen.add(node)
        _, doc = descriptors[node]
        profile = doc.get("profile") or {}
        declared = profile.get("bound_tuples")
        if isinstance(declared, list):
            for entry in declared:
                if isinstance(entry, dict):
                    tuples.append((node, entry))
        for child in profile.get("extends", []) or []:
            if isinstance(child, str):
                visit(child)

    visit(name)
    return tuples


def check_bound_tuples(
    descriptor_path: pathlib.Path,
    name: str,
    profile: dict,
    descriptors: dict[str, tuple[pathlib.Path, dict]],
) -> list[str]:
    """INV08 (spec.md §12.8.2): profile-declared bound tuples."""
    errors: list[str] = []
    bound_tuples = profile.get("bound_tuples")
    if bound_tuples is None:
        bound_tuples = []
    if not isinstance(bound_tuples, list):
        return [
            f"{descriptor_path}: [profile].bound_tuples must be an array "
            f"of tables (INV08)"
        ]

    for index, entry in enumerate(bound_tuples):
        where = f"{descriptor_path}: [[profile.bound_tuples]] entry {index}"
        if not isinstance(entry, dict):
            errors.append(f"{where} must be a table (INV08)")
            continue
        unknown = sorted(set(entry) - set(BOUND_TUPLE_KEYS))
        if unknown:
            errors.append(
                f"{where} carries unknown keys {unknown} (INV08: exactly "
                f"contained_kind / digest_field / fields)"
            )
        bad_shape = False
        for key in ("contained_kind", "digest_field"):
            value = entry.get(key)
            if not isinstance(value, str) or not value:
                errors.append(f"{where}.{key} must be a non-empty string (INV08)")
                bad_shape = True
        fields = entry.get("fields")
        if not isinstance(fields, list) or not fields:
            errors.append(
                f"{where}.fields must be a non-empty array of strings (INV08: "
                f"a tuple over no fields commits to nothing)"
            )
            bad_shape = True
        elif not all(isinstance(f, str) and f for f in fields):
            errors.append(
                f"{where}.fields must contain only non-empty strings (INV08)"
            )
            bad_shape = True
        if bad_shape:
            continue

        digest_field = entry["digest_field"]
        if not CLOSURE_RECORD_FIELD_RE.match(digest_field):
            errors.append(
                f"{where}.digest_field `{digest_field}` does not match the "
                r"frozen path grammar ^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$ "
                f"(INV08)"
            )
        elif (
            digest_field == "closure_root"
            or digest_field.split(".")[0] == "meta"
            or digest_field in POSTURE_FIELDS
        ):
            errors.append(
                f"{where}.digest_field `{digest_field}` is a forbidden carrier "
                f"(INV08: not closure_root, no meta.* path, no §12.9 posture "
                f"field)"
            )

        for field in fields:
            if not CLOSURE_RECORD_FIELD_RE.match(field):
                errors.append(
                    f"{where}.fields member `{field}` does not match the "
                    r"frozen path grammar ^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$ "
                    f"(INV08)"
                )
        if len(set(fields)) != len(fields):
            duplicated = sorted({f for f in fields if fields.count(f) > 1})
            errors.append(
                f"{where}.fields repeats {duplicated} (INV08: the tuple is a "
                f"set of fields, and a repeat contributes one record while "
                f"reading as two)"
            )
        if digest_field in fields:
            errors.append(
                f"{where}.digest_field `{digest_field}` is also one of its own "
                f"`fields` (INV08: the digest cannot commit to itself)"
            )
        if "closure_root" in fields:
            errors.append(
                f"{where}.fields includes `closure_root` (INV08: a profile "
                f"pins the digest_field into the closure stream, so a tuple "
                f"over closure_root makes each depend on the other and neither "
                f"computable)"
            )

    effective_kinds, _ = effective_profile_sets(name, descriptors)
    for index, entry in enumerate(bound_tuples):
        if not isinstance(entry, dict):
            continue
        contained_kind = entry.get("contained_kind")
        if isinstance(contained_kind, str) and contained_kind:
            if contained_kind not in effective_kinds:
                errors.append(
                    f"{descriptor_path}: [[profile.bound_tuples]] entry "
                    f"{index}.contained_kind `{contained_kind}` is not in the "
                    f"post-extends-union contained_kinds (INV08)"
                )

    kinds: list[str] = []
    for _, entry in effective_bound_tuples(name, descriptors):
        ck = entry.get("contained_kind")
        if isinstance(ck, str) and ck:
            kinds.append(ck)
    for ck in sorted({k for k in kinds if kinds.count(k) > 1}):
        errors.append(
            f"{descriptor_path}: `{ck}` declares more than one bound tuple "
            f"after the extends union (INV08: a kind carries at most one, "
            f"because a document has one digest_field per tuple and two "
            f"declarations for one kind cannot both be the tuple it commits to)"
        )

    return errors


def check_closure_records(
    descriptor_path: pathlib.Path,
    name: str,
    profile: dict,
    descriptors: dict[str, tuple[pathlib.Path, dict]],
) -> list[str]:
    """INV07 (spec.md §12.8.1): profile-pinned closure records."""
    errors: list[str] = []
    closure_records = profile.get("closure_records")
    if closure_records is None:
        closure_records = []
    if not isinstance(closure_records, list):
        return [
            f"{descriptor_path}: [profile].closure_records must be an array "
            f"of tables (INV07)"
        ]

    for index, entry in enumerate(closure_records):
        where = f"{descriptor_path}: [[profile.closure_records]] entry {index}"
        if not isinstance(entry, dict):
            errors.append(f"{where} must be a table (INV07)")
            continue
        unknown = sorted(set(entry) - set(CLOSURE_RECORD_KEYS))
        if unknown:
            errors.append(
                f"{where} carries unknown keys {unknown} (INV07: exactly "
                f"contained_kind / field / presence)"
            )
        bad_shape = False
        for key in CLOSURE_RECORD_KEYS:
            value = entry.get(key)
            if not isinstance(value, str) or not value:
                errors.append(f"{where}.{key} must be a non-empty string (INV07)")
                bad_shape = True
        if bad_shape:
            continue

        field = entry["field"]
        presence = entry["presence"]
        if not CLOSURE_RECORD_FIELD_RE.match(field):
            errors.append(
                f"{where}.field `{field}` does not match the frozen path "
                r"grammar ^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$ (INV07)"
            )
        elif (
            field in CLOSURE_RECORD_FORBIDDEN_FIELDS
            or field.split(".")[0] == "meta"
            or field in POSTURE_FIELDS
        ):
            errors.append(
                f"{where}.field `{field}` is a forbidden pin target (INV07: "
                f"not closure_root, not provenance.source_sha256, no meta.* "
                f"path, no §12.9 posture field)"
            )
        if presence not in CLOSURE_RECORD_PRESENCE:
            errors.append(
                f"{where}.presence `{presence}` must be one of "
                f"{list(CLOSURE_RECORD_PRESENCE)} (INV07)"
            )

    effective_kinds, effective_records = effective_profile_sets(name, descriptors)

    for index, entry in enumerate(closure_records):
        if not isinstance(entry, dict):
            continue
        contained_kind = entry.get("contained_kind")
        if isinstance(contained_kind, str) and contained_kind:
            if contained_kind not in effective_kinds:
                errors.append(
                    f"{descriptor_path}: [[profile.closure_records]] entry "
                    f"{index}.contained_kind `{contained_kind}` is not in the "
                    f"post-extends-union contained_kinds (INV07)"
                )

    pairs: list[tuple[str, str]] = []
    for _, rec in effective_records:
        ck = rec.get("contained_kind")
        fld = rec.get("field")
        if isinstance(ck, str) and isinstance(fld, str):
            pairs.append((ck, fld))
    duplicates = sorted({pair for pair in pairs if pairs.count(pair) > 1})
    for ck, fld in duplicates:
        errors.append(
            f"{descriptor_path}: duplicate closure-record pin "
            f"(`{ck}`, `{fld}`) after the extends union (INV07)"
        )

    return errors


def check_extends_acyclic(
    name: str,
    descriptors: dict[str, tuple[pathlib.Path, dict]],
) -> list[str]:
    """Walk the extends graph from `name` looking for a cycle."""
    errors: list[str] = []
    visiting: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in path:
            cycle = " -> ".join(path[path.index(node):] + [node])
            errors.append(f"`extends` graph contains a cycle: {cycle}")
            return
        if node in visiting:
            return
        visiting.add(node)
        if node not in descriptors:
            return  # INV03 handled separately
        _, doc = descriptors[node]
        profile = doc.get("profile") or {}
        for child in profile.get("extends", []) or []:
            if isinstance(child, str):
                visit(child, path + [node])

    visit(name, [])
    return errors


def validate_one(
    descriptor_path: pathlib.Path,
    repo_root: pathlib.Path,
    descriptors: dict[str, tuple[pathlib.Path, dict]],
) -> list[str]:
    errors: list[str] = []
    try:
        doc = load_toml(descriptor_path)
    except FileNotFoundError:
        return [f"{descriptor_path}: file not found"]
    except tomllib.TOMLDecodeError as exc:
        return [f"{descriptor_path}: invalid TOML: {exc}"]

    meta = doc.get("meta")
    if not isinstance(meta, dict):
        return [f"{descriptor_path}: missing required `[meta]` table"]
    if meta.get("template_kind") != "profile-descriptor":
        return [
            f"{descriptor_path}: meta.template_kind must equal "
            f"`\"profile-descriptor\"` (got {meta.get('template_kind')!r})"
        ]

    profile = doc.get("profile")
    if not isinstance(profile, dict):
        return [f"{descriptor_path}: missing required `[profile]` table"]

    for field in REQUIRED_PROFILE_FIELDS:
        if field not in profile:
            errors.append(f"{descriptor_path}: [profile].{field} is required")

    if errors:
        return errors

    name = profile["name"]
    namespace = profile["namespace"]
    extends = profile["extends"]
    ontology = profile["ontology"]
    contained_kinds = profile["contained_kinds"]

    if not isinstance(name, str) or not name:
        errors.append(f"{descriptor_path}: [profile].name must be a non-empty string")
    if not isinstance(namespace, str) or not namespace:
        errors.append(
            f"{descriptor_path}: [profile].namespace must be a non-empty string"
        )
    if not isinstance(extends, list):
        errors.append(f"{descriptor_path}: [profile].extends must be an array")
    if not isinstance(ontology, str) or not ontology:
        errors.append(
            f"{descriptor_path}: [profile].ontology must be a non-empty string"
        )
    if not isinstance(contained_kinds, list):
        errors.append(
            f"{descriptor_path}: [profile].contained_kinds must be an array"
        )
    if errors:
        return errors

    # INV01 — namespace partition consistency
    errors.extend(check_namespace_partition(name, namespace))

    # INV02 — extends is acyclic
    errors.extend(check_extends_acyclic(name, descriptors))

    # INV03 — every extends entry resolves to a loaded descriptor
    for entry in extends:
        if not isinstance(entry, str):
            errors.append(
                f"{descriptor_path}: [profile].extends entries must be strings"
            )
            continue
        if entry not in descriptors:
            errors.append(
                f"{descriptor_path}: [profile].extends entry `{entry}` does not "
                f"resolve to a loaded profile-descriptor (looked under "
                f"`profiles/*/PROFILE.toml` and the file under validation)"
            )

    # INV04 — ontology path exists and is an ontology
    ontology_path = (repo_root / ontology).resolve()
    if not ontology_path.exists() or not ontology_path.is_file():
        errors.append(
            f"{descriptor_path}: [profile].ontology path does not resolve to a "
            f"file ({ontology_path})"
        )
    else:
        try:
            ontology_doc = load_toml(ontology_path)
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"{descriptor_path}: ontology parse failure: {exc}")
        else:
            ont_meta = ontology_doc.get("meta") or {}
            if ont_meta.get("template_kind") != "ontology":
                errors.append(
                    f"{descriptor_path}: [profile].ontology ({ontology}) does "
                    f"not declare `template_kind = \"ontology\"`"
                )

    # INV05 — every contained_kinds entry resolves to a *-kind.toml
    for slug in contained_kinds:
        if not isinstance(slug, str) or not slug:
            errors.append(
                f"{descriptor_path}: [profile].contained_kinds entries must be "
                f"non-empty strings"
            )
            continue
        candidates = _kind_descriptor_candidates(repo_root, slug, profile_name=name)
        matched = None
        for candidate in candidates:
            if not candidate.exists():
                continue
            try:
                kd_doc = load_toml(candidate)
            except tomllib.TOMLDecodeError:
                continue
            kd_meta = kd_doc.get("meta") or {}
            if (
                kd_meta.get("template_kind") == "kind-descriptor"
                and kd_meta.get("describes_kind") == slug
            ):
                matched = candidate
                break
        if matched is None:
            errors.append(
                f"{descriptor_path}: [profile].contained_kinds entry `{slug}` "
                f"does not resolve to a `*-kind.toml` whose "
                f"`[meta].describes_kind` matches the entry "
                f"(searched: {[str(c) for c in candidates]})"
            )

    # INV07: profile-pinned closure records (spec.md §12.8.1)
    errors.extend(check_closure_records(descriptor_path, name, profile, descriptors))
    errors.extend(check_bound_tuples(descriptor_path, name, profile, descriptors))

    return errors


def _kind_descriptor_candidates(
    repo_root: pathlib.Path, slug: str, profile_name: str
) -> list[pathlib.Path]:
    """Return the conventional locations a kind-descriptor for `slug`
    may live under. Searches profile dir, core/, and any other profile
    dirs as a fallback."""
    candidates = [
        repo_root / "profiles" / profile_name / f"{slug}-kind.toml",
        repo_root / "core" / f"{slug}-kind.toml",
    ]
    profiles_dir = repo_root / "profiles"
    if profiles_dir.is_dir():
        for entry in sorted(profiles_dir.iterdir()):
            if not entry.is_dir():
                continue
            candidates.append(entry / f"{slug}-kind.toml")
    # dedupe while preserving order
    seen: set[pathlib.Path] = set()
    deduped: list[pathlib.Path] = []
    for c in candidates:
        rc = c.resolve()
        if rc in seen:
            continue
        seen.add(rc)
        deduped.append(c)
    return deduped


def main() -> int:
    args = parse_args()
    repo_root = pathlib.Path(args.repo_root).resolve()
    descriptors = discover_descriptors(repo_root)

    # Duplicate profile names would shadow each other in the name-keyed
    # map and could erase closure pins; refuse to validate anything
    # (SPEC 12.8.1 pin resolution, mirrored by the closure validators).
    seen_names: dict[str, pathlib.Path] = {}
    duplicate_errors: list[str] = []
    profiles_dir = repo_root / "profiles"
    if profiles_dir.is_dir():
        for entry in sorted(profiles_dir.iterdir()):
            candidate = entry / "PROFILE.toml"
            if not candidate.is_file():
                continue
            try:
                dup_doc = load_toml(candidate)
            except (FileNotFoundError, tomllib.TOMLDecodeError):
                continue
            if (dup_doc.get("meta") or {}).get("template_kind") != "profile-descriptor":
                continue
            dup_name = (dup_doc.get("profile") or {}).get("name")
            if not isinstance(dup_name, str):
                continue
            if dup_name in seen_names:
                duplicate_errors.append(
                    f"duplicate profile-descriptor name `{dup_name}` "
                    f"({seen_names[dup_name]} and {candidate}): pin resolution "
                    f"refuses to proceed (SPEC §12.8.1)"
                )
            else:
                seen_names[dup_name] = candidate
    if duplicate_errors:
        print("PROFILE DESCRIPTOR VALIDATION FAILED")
        for line in duplicate_errors:
            print(f"- {line}")
        return 1

    all_errors: list[str] = []
    for raw in args.files:
        path = pathlib.Path(raw).resolve()
        # Merge ONLY the file under validation into the resolution set
        # (rs/go resolve the root through the discovered map with a
        # fall-back to the document itself; a global merge of every CLI
        # file would give Python cross-file extends resolution the
        # primaries do not have; U10 review, fix 3).
        per_file = dict(descriptors)
        try:
            doc = load_toml(path)
        except (FileNotFoundError, tomllib.TOMLDecodeError):
            doc = None
        if doc is not None and (doc.get("meta") or {}).get("template_kind") == "profile-descriptor":
            name = (doc.get("profile") or {}).get("name")
            if isinstance(name, str) and name not in per_file:
                per_file[name] = (path, doc)
        errs = validate_one(path, repo_root, per_file)
        if errs:
            all_errors.append(f"--- {path} ---")
            all_errors.extend(errs)

    if all_errors:
        print("PROFILE DESCRIPTOR VALIDATION FAILED")
        for line in all_errors:
            print(f"- {line}")
        return 1

    print("PROFILE DESCRIPTOR VALIDATION PASSED")
    print(f"- files validated: {len(args.files)}")
    print(f"- profiles in resolution set: {len(descriptors)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
