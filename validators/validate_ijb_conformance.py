#!/usr/bin/env python3
"""Validate IJB conformance for an ontology, kind-descriptor, or
instance DAG-TOML file.

Implements the structural surface of spec.md §10 (`Foundation: IJB`):

Ontology files (rules 1–4):

1. Every `[[entities]]` block declares `ijb_primitive` and `ijb_class`.
2. Every `[[relations]]` block declares `ijb_primitive` and `ijb_class`.
3. Every `[[attribute_vocabularies]]` block declares `ijb_primitive`
   and `ijb_constraint_type`.
4. Every `ijb_primitive` value is one of the six (`thing | scope | path
   | observed | constraint | time`). Every `ijb_class` value is
   `structural` or `instance`. Every `ijb_constraint_type` value is
   `structural`, `policy`, or `observed`.

Kind-descriptor files (rules KD1–KD3 per SPEC §10.2):

KD1. `[kind]` declares `ijb_primitive = "thing"` and `ijb_class =
     "structural"`.
KD2. Every `[[kind.required_fields]]`, `[[kind.required_sections]]`,
     `[[kind.hard_invariants]]` block, and the `[kind.relation_to_ontology]`
     table declare `ijb_primitive = "constraint"` and
     `ijb_constraint_type = "structural"`.
KD3. Every `[[kind.example]]` block declares `ijb_primitive =
     "observed"` (no class field; observed is instance-by-nature).

Instance files (rules 5–6):

5. Every entity prefix used resolves to a declared `[[entities]]`
   block in the core ontology plus, where `framework_profile` is set,
   the matching profile ontology.
6. Every relation predicate used resolves to a declared
   `[[relations]]` block in those same ontologies, and that relation
   declaration carries `ijb_primitive`.

Out of scope for v0.1.0 (see SPEC §10.4):

- Free-text reality-check forbidden-concept matching
  (`strategy`/`culture`/`alignment`/`risk posture`). Substring matching
  in prose without false positives is non-trivial; deferred to v0.2.0.
- Cross-document instance-pairing enforcement for structural relations
  (the IJB grammar's structural→instance pairing rule).
"""

from __future__ import annotations

import argparse
import contextlib
import pathlib
import re
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py


IJB_PRIMITIVES = ("thing", "scope", "path", "observed", "constraint", "time")
IJB_CLASSES = ("structural", "instance")
IJB_CONSTRAINT_TYPES = ("structural", "policy", "observed")

CORE_ONTOLOGY_RELPATH = "core/ontology.toml"
PROFILE_ONTOLOGY_TEMPLATE = "profiles/{profile}/ontology.toml"

# Profile name aliases per SPEC §2.5.
FRAMEWORK_PROFILE_ALIASES = {"AGDF": "agent-assurance"}

# SPEC §2.5 namespacing partition regexes (mirrors the Rust + Go primaries).
UNPREFIXED_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
REVERSE_DNS_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+$")
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

# SPEC §2.7 closed set for confidentiality.
CONFIDENTIALITY_CLOSED = (
    "public",
    "restricted",
    "confidential",
    "trade-secret",
    "embargoed",
)

# SPEC §11.1 closed set for provenance.encryption.hash_is_over.
HASH_IS_OVER_CLOSED = ("plaintext", "ciphertext")

# SPEC §2.7 RFC 3339 date-or-datetime regexes. Syntactic only; the
# validator MUST NOT compare against wall-clock time.
RFC3339_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RFC3339_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$"
)


def _is_rfc3339_date_or_datetime(s: str) -> bool:
    return bool(RFC3339_DATE_RE.match(s) or RFC3339_DATETIME_RE.match(s))

# Matches a candidate uppercase entity prefix (chars before the first `:`).
UPPERCASE_PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate IJB conformance for a DAG-TOML ontology or instance file.",
    )
    parser.add_argument("file", help="Path to the TOML file to validate.")
    parser.add_argument(
        "--repo-root",
        help=(
            "Repository root. Required for instance files so the core and "
            "profile ontologies can be loaded for resolution."
        ),
    )
    parser.add_argument(
        "--check-references-exist",
        action="store_true",
        help=(
            "Accepted for parity with the other validators in this "
            "repository. Currently has no additional effect: this "
            "validator already resolves entity prefixes and relation "
            "predicates against on-disk ontologies whenever --repo-root "
            "is supplied."
        ),
    )
    return parser.parse_args()


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _block_label(block: dict, kind: str) -> str:
    if kind == "entities":
        return block.get("id_prefix") or block.get("id_pattern") or "?"
    if kind == "relations":
        return block.get("predicate") or "?"
    if kind == "attribute_vocabularies":
        return block.get("attribute") or "?"
    return "?"


# SPEC §10.2 "Structural ontology declarations" table — the full row
# set the validator enforces, including the meta and extension-rules
# rows that lie outside the array-of-tables blocks. Per SPEC §2.7,
# the disclosure-posture fields (`confidentiality`, `license`,
# `embargo_until`) are also classifiable here when declared.
_META_FIELD_MAP = {
    "framework_profile": ("scope",      "structural", None),
    "template_kind":     ("scope",      "structural", None),
    "schema_version":    ("constraint", None,         "structural"),
    "ontology_version":  ("constraint", None,         "structural"),
    "confidentiality":   ("constraint", None,         "policy"),
    "license":           ("constraint", None,         "policy"),
    "embargo_until":     ("time",       None,         None),
}


def validate_ontology(doc: dict, source: str) -> list[str]:
    """Enforce the SPEC §10.2 ontology-declaration mapping.

    All rows from §10.2 "Structural ontology declarations" are covered:
    `[[entities]]`, `[[relations]]`, `[[attribute_vocabularies]]`,
    `[extension_rules]`, plus the per-field meta annotations under
    `[meta.ijb_field_primitives]` for `framework_profile`,
    `template_kind`, `schema_version`, and `ontology_version`.

    Each row's annotations are pinned to the exact values in §10.2;
    mutating any of them to a different valid IJB value (e.g. swapping
    `[[entities]]` to `path` instead of `thing`, or swapping the
    `[extension_rules]` constraint-type) is rejected.
    """
    errors: list[str] = []

    for index, block in enumerate(doc.get("entities", [])):
        label = _block_label(block, "entities")
        errors.extend(
            _check_primitive_class(
                block,
                f"{source}:entities[{index}] ({label})",
                expected_primitive="thing",
                expected_class="structural",
                expected_constraint_type=None,
            )
        )

    for index, block in enumerate(doc.get("relations", [])):
        label = _block_label(block, "relations")
        errors.extend(
            _check_primitive_class(
                block,
                f"{source}:relations[{index}] (predicate={label})",
                expected_primitive="path",
                expected_class="structural",
                expected_constraint_type=None,
            )
        )

    for index, block in enumerate(doc.get("attribute_vocabularies", [])):
        label = _block_label(block, "attribute_vocabularies")
        prefix = f"{source}:attribute_vocabularies[{index}] (attribute={label})"
        # SPEC §10.2 row "[[attribute_vocabularies]]" pins
        # `ijb_primitive = "constraint"`. The constraint-type
        # qualifier may legitimately be any of
        # `structural | policy | observed` (see SPEC §10.2 note):
        # `confidentiality`, `license`, `disclosure_posture` etc.
        # declare policy posture, while shape-checked vocabularies
        # stay `"structural"`.
        prim = block.get("ijb_primitive")
        if prim is None:
            errors.append(f"{prefix}: missing required `ijb_primitive`")
        elif prim not in IJB_PRIMITIVES:
            errors.append(
                f"{prefix}: `ijb_primitive = \"{prim}\"` is not one of "
                f"{list(IJB_PRIMITIVES)}"
            )
        elif prim != "constraint":
            errors.append(
                f"{prefix}: `ijb_primitive = \"{prim}\"` does not match the "
                f"SPEC §10.2 mapping (expected `\"constraint\"`)"
            )
        if "ijb_class" in block:
            errors.append(
                f"{prefix}: `ijb_class` is not permitted on attribute_vocabularies "
                f"blocks (SPEC §10.2 carries no class field for constraints)"
            )
        ct = block.get("ijb_constraint_type")
        if ct is None:
            errors.append(f"{prefix}: missing required `ijb_constraint_type`")
        elif ct not in IJB_CONSTRAINT_TYPES:
            errors.append(
                f"{prefix}: `ijb_constraint_type = \"{ct}\"` is not one of "
                f"{list(IJB_CONSTRAINT_TYPES)}"
            )

    ext = doc.get("extension_rules")
    if isinstance(ext, dict):
        errors.extend(
            _check_primitive_class(
                ext,
                f"{source}:[extension_rules]",
                expected_primitive="constraint",
                expected_class=None,
                expected_constraint_type="structural",
            )
        )
    else:
        errors.append(
            f"{source}: missing required `[extension_rules]` table "
            f"(SPEC §10.2 row)"
        )

    meta = doc.get("meta") or {}
    field_prims = meta.get("ijb_field_primitives")
    if not isinstance(field_prims, dict):
        errors.append(
            f"{source}: missing required `[meta.ijb_field_primitives]` "
            f"table (per-field meta annotations per SPEC §10.2)"
        )
    else:
        for fname, (ep, ec, ect) in _META_FIELD_MAP.items():
            fblock = field_prims.get(fname)
            in_meta = fname in meta

            if fblock is None:
                # No annotation. Only required when the underlying
                # [meta] field is actually present (so callers MUST
                # classify what they declare).
                if in_meta:
                    errors.append(
                        f"{source}:[meta.ijb_field_primitives].{fname}: "
                        f"missing required inline annotation table for the "
                        f"`[meta].{fname}` field"
                    )
                continue

            if not isinstance(fblock, dict):
                errors.append(
                    f"{source}:[meta.ijb_field_primitives].{fname}: "
                    f"must be an inline annotation table "
                    f"(got `{type(fblock).__name__}`)"
                )
                continue

            # Annotation present. Validate it whether or not the
            # underlying `[meta]` field is set: the annotation table
            # itself is the normative declaration of the field's IJB
            # role and must conform to the SPEC §10.2 mapping.
            errors.extend(
                _check_primitive_class(
                    fblock,
                    f"{source}:[meta.ijb_field_primitives].{fname}",
                    expected_primitive=ep,
                    expected_class=ec,
                    expected_constraint_type=ect,
                )
            )

        # Reject unknown annotation keys — every entry in
        # [meta.ijb_field_primitives] must correspond to a known
        # SPEC §10.2 meta-field row.
        for fname in field_prims:
            if fname not in _META_FIELD_MAP:
                errors.append(
                    f"{source}:[meta.ijb_field_primitives].{fname}: "
                    f"unknown meta-field annotation key (not listed in "
                    f"SPEC §10.2)"
                )

    return errors


def _check_primitive_class(
    block: dict,
    path_prefix: str,
    expected_primitive: str,
    expected_class: str | None,
    expected_constraint_type: str | None,
) -> list[str]:
    """Helper: check a kind-descriptor block carries the expected
    IJB annotations. `expected_class` and `expected_constraint_type`
    are mutually exclusive — `observed` blocks have neither."""
    errors: list[str] = []
    prim = block.get("ijb_primitive")
    if prim is None:
        errors.append(f"{path_prefix}: missing required `ijb_primitive`")
    elif prim not in IJB_PRIMITIVES:
        errors.append(
            f"{path_prefix}: `ijb_primitive = \"{prim}\"` is not one of "
            f"{list(IJB_PRIMITIVES)}"
        )
    elif prim != expected_primitive:
        errors.append(
            f"{path_prefix}: `ijb_primitive = \"{prim}\"` does not match the "
            f"SPEC §10.2 mapping (expected `\"{expected_primitive}\"`)"
        )
    if expected_class is not None:
        cls = block.get("ijb_class")
        if cls is None:
            errors.append(f"{path_prefix}: missing required `ijb_class`")
        elif cls not in IJB_CLASSES:
            errors.append(
                f"{path_prefix}: `ijb_class = \"{cls}\"` is not one of "
                f"{list(IJB_CLASSES)}"
            )
        elif cls != expected_class:
            errors.append(
                f"{path_prefix}: `ijb_class = \"{cls}\"` does not match the "
                f"SPEC §10.2 mapping (expected `\"{expected_class}\"`)"
            )
    else:
        # Mutual exclusion (SPEC §10.1, §10.2): blocks whose mapping does
        # not carry a class field MUST NOT declare `ijb_class`.
        if "ijb_class" in block:
            errors.append(
                f"{path_prefix}: `ijb_class` is not permitted on this block "
                f"per SPEC §10.2 (the mapping carries no class field; "
                f"`ijb_primitive = \"{expected_primitive}\"` is "
                f"instance-by-nature)"
            )
    if expected_constraint_type is not None:
        ct = block.get("ijb_constraint_type")
        if ct is None:
            errors.append(
                f"{path_prefix}: missing required `ijb_constraint_type`"
            )
        elif ct not in IJB_CONSTRAINT_TYPES:
            errors.append(
                f"{path_prefix}: `ijb_constraint_type = \"{ct}\"` is not one of "
                f"{list(IJB_CONSTRAINT_TYPES)}"
            )
        elif ct != expected_constraint_type:
            errors.append(
                f"{path_prefix}: `ijb_constraint_type = \"{ct}\"` does not "
                f"match the SPEC §10.2 mapping "
                f"(expected `\"{expected_constraint_type}\"`)"
            )
    else:
        # Mutual exclusion: blocks whose mapping carries `ijb_class` (or
        # neither qualifier) MUST NOT also declare `ijb_constraint_type`.
        if "ijb_constraint_type" in block:
            errors.append(
                f"{path_prefix}: `ijb_constraint_type` is not permitted on "
                f"this block per SPEC §10.2 (the mapping carries no "
                f"constraint-type qualifier; "
                f"`ijb_primitive = \"{expected_primitive}\"` is not a "
                f"constraint)"
            )
    return errors


def validate_kind_descriptor(doc: dict, source: str) -> list[str]:
    """Enforce kind-descriptor IJB annotations per SPEC §10.2.

    SPEC §10.2 "Kind-descriptor blocks" table:

      | Block                          | ijb_primitive | ijb_class / ijb_constraint_type |
      |--------------------------------|---------------|---------------------------------|
      | [kind]                         | thing         | structural (class)              |
      | [[kind.required_fields]]       | constraint    | structural (constraint_type)    |
      | [[kind.required_sections]]     | constraint    | structural (constraint_type)    |
      | [[kind.hard_invariants]]       | constraint    | structural (constraint_type)    |
      | [[kind.example]]               | observed      | (no class field)                |
      | [kind.relation_to_ontology]    | constraint    | structural (constraint_type)    |
    """
    errors: list[str] = []

    kind = doc.get("kind")
    if not isinstance(kind, dict):
        errors.append(f"{source}: kind-descriptor missing required `[kind]` table")
        return errors

    errors.extend(
        _check_primitive_class(
            kind,
            f"{source}:[kind]",
            expected_primitive="thing",
            expected_class="structural",
            expected_constraint_type=None,
        )
    )

    constraint_arrays = (
        ("required_fields", "[[kind.required_fields]]"),
        ("required_sections", "[[kind.required_sections]]"),
        ("hard_invariants", "[[kind.hard_invariants]]"),
    )
    for key, header in constraint_arrays:
        entries = kind.get(key, [])
        for index, block in enumerate(entries):
            if not isinstance(block, dict):
                continue
            label = block.get("id") or block.get("path") or block.get("table") or "?"
            errors.extend(
                _check_primitive_class(
                    block,
                    f"{source}:{header}[{index}] ({label})",
                    expected_primitive="constraint",
                    expected_class=None,
                    expected_constraint_type="structural",
                )
            )

    for index, block in enumerate(kind.get("example", [])):
        if not isinstance(block, dict):
            continue
        label = block.get("name") or block.get("file") or "?"
        errors.extend(
            _check_primitive_class(
                block,
                f"{source}:[[kind.example]][{index}] ({label})",
                expected_primitive="observed",
                expected_class=None,
                expected_constraint_type=None,
            )
        )

    rto = kind.get("relation_to_ontology")
    if isinstance(rto, dict):
        errors.extend(
            _check_primitive_class(
                rto,
                f"{source}:[kind.relation_to_ontology]",
                expected_primitive="constraint",
                expected_class=None,
                expected_constraint_type="structural",
            )
        )

    return errors


def validate_profile_descriptor(doc: dict, source: str) -> list[str]:
    """Enforce profile-descriptor IJB annotations per SPEC §6.1 / §10.2.

    The `[profile]` table is the singleton declaration about the named
    profile and is `(thing, structural)` — mirroring the `[kind]` block
    in a kind-descriptor (KD1).
    """
    errors: list[str] = []
    profile = doc.get("profile")
    if not isinstance(profile, dict):
        errors.append(
            f"{source}: profile-descriptor missing required `[profile]` table"
        )
        return errors

    errors.extend(
        _check_primitive_class(
            profile,
            f"{source}:[profile]",
            expected_primitive="thing",
            expected_class="structural",
            expected_constraint_type=None,
        )
    )
    return errors


def build_resolver(ontologies: list[tuple[str, dict]]) -> tuple[dict, list, dict]:
    """Build lookup tables for entity prefixes, id patterns, and relation predicates."""
    id_prefixes: dict[str, tuple[dict, str]] = {}
    id_patterns: list[tuple[re.Pattern, dict, str]] = []
    predicate_to_relation: dict[str, list[tuple[dict, str]]] = {}

    for source, doc in ontologies:
        for block in doc.get("entities", []):
            prefix = block.get("id_prefix")
            if isinstance(prefix, str) and prefix:
                id_prefixes[prefix] = (block, source)
            pattern = block.get("id_pattern")
            if isinstance(pattern, str) and pattern:
                # An un-compilable id_pattern is skipped here; pattern
                # validity is reported by the dedicated checks (py/empty-except).
                with contextlib.suppress(re.error):
                    id_patterns.append((re.compile(f"^{pattern}$"), block, source))
        for block in doc.get("relations", []):
            predicate = block.get("predicate")
            if isinstance(predicate, str) and predicate:
                predicate_to_relation.setdefault(predicate, []).append((block, source))

    return id_prefixes, id_patterns, predicate_to_relation


def looks_like_entity_ref(token: str) -> bool:
    """Decide whether a string is shaped like an entity reference.

    An entity reference is either:
    - `PREFIX:slug` where PREFIX is uppercase letters/digits/underscores, OR
    - a token that could match one of the bare-id patterns (handled by
      caller via id_patterns).
    """
    if ":" in token:
        prefix = token.split(":", 1)[0]
        return bool(UPPERCASE_PREFIX_RE.match(prefix))
    return False


def check_entity_ref(
    token: str,
    id_prefixes: dict,
    id_patterns: list,
) -> str | None:
    """Return an error string if `token` looks like an entity ref but
    does not resolve, else None."""
    if not isinstance(token, str) or not token:
        return None
    if ":" in token:
        prefix = token.split(":", 1)[0]
        if not UPPERCASE_PREFIX_RE.match(prefix):
            return None  # not entity-ref-shaped (e.g. "src/checkout::sym")
        if prefix in id_prefixes:
            return None
        return (
            f"entity prefix `{prefix}` in `{token}` does not resolve to a "
            f"declared `[[entities]].id_prefix` in the loaded ontologies"
        )
    for rx, _block, _src in id_patterns:
        if rx.match(token):
            return None
    return None


def validate_instance(
    doc: dict,
    source: str,
    id_prefixes: dict,
    id_patterns: list,
    predicate_to_relation: dict,
) -> list[str]:
    """Enforce rules 5–6 against an instance document."""
    errors: list[str] = []

    def walk(node: object, parent_key: str, path: str) -> None:
        if isinstance(node, str):
            if parent_key == "id" or parent_key in predicate_to_relation:
                err = check_entity_ref(node, id_prefixes, id_patterns)
                if err:
                    errors.append(f"{path}: {err}")
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(v, k, f"{path}.{k}" if path else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, parent_key, f"{path}[{i}]")

    for key, value in doc.items():
        walk(value, key, str(key))

    # Special case: implementation-DAG units are declared as
    # `[units.U01]` so the unit ID is the table key, not a value. Verify
    # each such key resolves through the declared id_patterns (the
    # closed `U\d+[a-z]?` pattern in core/ontology.toml).
    units = doc.get("units")
    if isinstance(units, dict):
        for unit_id in units.keys():
            matched = False
            for rx, _block, _src in id_patterns:
                if rx.match(unit_id):
                    matched = True
                    break
            if not matched:
                errors.append(
                    f"units.{unit_id}: identifier does not match any declared "
                    f"entity `id_pattern` in the loaded ontologies"
                )

    return errors


def resolve_profile_name(framework_profile: str) -> str:
    return FRAMEWORK_PROFILE_ALIASES.get(framework_profile, framework_profile)


def discover_profile_descriptors(repo_root: pathlib.Path) -> set[str]:
    """Return the set of profile names declared by `profiles/*/PROFILE.toml`.
    Used to enforce the SPEC §2.5 partition: an unprefixed `framework_profile`
    value MUST resolve to a loaded descriptor."""
    names: set[str] = set()
    profiles_dir = repo_root / "profiles"
    if not profiles_dir.is_dir():
        return names
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
        name = (doc.get("profile") or {}).get("name")
        if isinstance(name, str) and name:
            names.add(name)
    return names


def validate_meta_posture(
    doc: dict,
    source: str,
    repo_root: pathlib.Path | None,
) -> list[str]:
    """Enforce the SPEC §2.5 / §2.6 / §2.7 / §11.1 cross-field rules on
    instance files. Mirrors the Rust + Go primaries so all three
    validators agree on the same surface."""
    errors: list[str] = []
    meta = doc.get("meta")
    if not isinstance(meta, dict):
        return errors

    # §2.2 / §8 — version pin shapes.
    schema_version = meta.get("schema_version")
    if not isinstance(schema_version, str) or not SEMVER_RE.match(schema_version):
        errors.append(
            f"{source}: [meta].schema_version must be a semver string "
            f"`MAJOR.MINOR.PATCH` (got {schema_version!r})"
        )

    if "ontology_version" in meta:
        ontology_version = meta["ontology_version"]
        if (
            isinstance(ontology_version, bool)
            or not isinstance(ontology_version, int)
            or ontology_version < 1
        ):
            errors.append(
                f"{source}: [meta].ontology_version must be a positive integer "
                f"snapshot (got {ontology_version!r})"
            )

    # §2.6 — docs URL shape (https://, no query string).
    docs_url = meta.get("docs")
    if isinstance(docs_url, str):
        if not docs_url.startswith("https://"):
            errors.append(
                f"{source}: [meta].docs must start with `https://` (SPEC §2.6)"
            )
        stripped = docs_url.split("#", 1)[0]
        if "?" in stripped:
            errors.append(
                f"{source}: [meta].docs must not contain a query string (SPEC §2.6)"
            )

    # §2.7 — confidentiality closed set + embargo_until cross-field.
    if "confidentiality" in meta:
        conf = meta["confidentiality"]
        if not isinstance(conf, str):
            errors.append(
                f"{source}: [meta].confidentiality, when present, must be a "
                f"string (SPEC §2.7)"
            )
        else:
            if conf not in CONFIDENTIALITY_CLOSED:
                errors.append(
                    f"{source}: [meta].confidentiality = `{conf}` is not in the "
                    f"closed set {list(CONFIDENTIALITY_CLOSED)} (SPEC §2.7)"
                )
            embargo = meta.get("embargo_until")
            if conf == "embargoed":
                if not isinstance(embargo, str) or not embargo:
                    errors.append(
                        f"{source}: [meta].confidentiality = \"embargoed\" REQUIRES "
                        f"[meta].embargo_until (SPEC §2.7)"
                    )
                elif not _is_rfc3339_date_or_datetime(embargo):
                    errors.append(
                        f"{source}: [meta].embargo_until = `{embargo}` does not "
                        f"match RFC 3339 date or date-time syntax (SPEC §2.7)"
                    )
            elif isinstance(embargo, str) and not _is_rfc3339_date_or_datetime(embargo):
                # embargo_until is informational when confidentiality !=
                # "embargoed" but its syntax MUST still conform.
                errors.append(
                    f"{source}: [meta].embargo_until = `{embargo}` does not "
                    f"match RFC 3339 date or date-time syntax (SPEC §2.7)"
                )

    # §2.7 — license, when present, MUST be a non-empty string.
    if "license" in meta:
        lic = meta["license"]
        if not isinstance(lic, str):
            errors.append(
                f"{source}: [meta].license, when present, must be a string "
                f"(SPEC §2.7)"
            )
        elif not lic.strip():
            errors.append(
                f"{source}: [meta].license, when present, must be a non-empty string"
            )

    # §2.5 — framework_profile partition + descriptor resolution.
    fp = meta.get("framework_profile")
    if isinstance(fp, str) and fp:
        resolved = resolve_profile_name(fp)
        is_unprefixed = bool(UNPREFIXED_NAME_RE.match(resolved))
        is_reverse_dns = bool(REVERSE_DNS_NAME_RE.match(resolved))
        if not (is_unprefixed or is_reverse_dns):
            errors.append(
                f"{source}: [meta].framework_profile = `{fp}` does not match the "
                f"SPEC §2.5 namespacing partition (must be unprefixed kebab-case "
                f"or reverse-DNS)"
            )
        elif is_unprefixed and repo_root is not None:
            known = discover_profile_descriptors(repo_root)
            if resolved not in known:
                errors.append(
                    f"{source}: [meta].framework_profile = `{fp}` is an unprefixed "
                    f"(spec-reserved) name but no loaded profile-descriptor declares it "
                    f"(SPEC §2.5)"
                )

    # §11.1 — provenance.encryption sub-table shape (when present).
    prov = doc.get("provenance")
    if isinstance(prov, dict):
        enc = prov.get("encryption")
        if isinstance(enc, dict):
            sealed = enc.get("sealed")
            if sealed is None:
                errors.append(
                    f"{source}: [provenance.encryption].sealed is required "
                    f"(boolean) when the sub-table is present"
                )
            elif sealed is False:
                errors.append(
                    f"{source}: [provenance.encryption] is present but "
                    f"`sealed = false` — SPEC §11.1 forbids the sub-table in "
                    f"that case"
                )
            elif sealed is not True:
                errors.append(
                    f"{source}: [provenance.encryption].sealed must be a boolean"
                )
            hash_over = enc.get("hash_is_over")
            if hash_over is None:
                errors.append(
                    f"{source}: [provenance.encryption].hash_is_over is required "
                    f"(SPEC §11.1)"
                )
            elif hash_over not in HASH_IS_OVER_CLOSED:
                errors.append(
                    f"{source}: [provenance.encryption].hash_is_over = `{hash_over}` "
                    f"is not in {list(HASH_IS_OVER_CLOSED)}"
                )
            if "scheme_hint" in enc and not isinstance(enc["scheme_hint"], str):
                errors.append(
                    f"{source}: [provenance.encryption].scheme_hint, when present, "
                    f"must be a string (SPEC §11.1)"
                )

    return errors


def main() -> int:
    args = parse_args()
    path = pathlib.Path(args.file).resolve()
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    try:
        doc = load_toml(path)
    except tomllib.TOMLDecodeError as exc:
        print(f"error: TOML parse failure: {exc}", file=sys.stderr)
        return 2

    meta = doc.get("meta")
    if not isinstance(meta, dict):
        print("IJB CONFORMANCE VALIDATION FAILED")
        print(f"- file: {path}")
        print("- missing required `[meta]` table")
        return 1

    template_kind = meta.get("template_kind")
    framework_profile = meta.get("framework_profile")
    errors: list[str] = []

    # SPEC §2.5 + §2.6 + §2.7 + §11.1 cross-field semantics apply to
    # every file with a `[meta]` table — including ontology /
    # kind-descriptor / profile-descriptor — so the IJB validator
    # agrees with the Rust + Go primaries on the meta surface.
    repo_root_for_posture = None
    if args.repo_root:
        repo_root_for_posture = pathlib.Path(args.repo_root).resolve()
    errors.extend(validate_meta_posture(doc, str(path), repo_root_for_posture))

    if template_kind == "ontology":
        errors.extend(validate_ontology(doc, str(path)))
    elif template_kind == "kind-descriptor":
        errors.extend(validate_kind_descriptor(doc, str(path)))
    elif template_kind == "profile-descriptor":
        errors.extend(validate_profile_descriptor(doc, str(path)))
    else:
        if not args.repo_root:
            errors.append(
                "instance files require --repo-root so the core and (if "
                "applicable) profile ontologies can be loaded for "
                "resolution"
            )
        else:
            repo_root = pathlib.Path(args.repo_root).resolve()
            ontologies: list[tuple[str, dict]] = []

            core_path = repo_root / CORE_ONTOLOGY_RELPATH
            if not core_path.exists():
                errors.append(f"core ontology not found at {core_path}")
            else:
                try:
                    core_doc = load_toml(core_path)
                except tomllib.TOMLDecodeError as exc:
                    errors.append(f"core ontology parse failure ({core_path}): {exc}")
                else:
                    ontologies.append((str(core_path), core_doc))
                    errors.extend(validate_ontology(core_doc, str(core_path)))

            if isinstance(framework_profile, str) and framework_profile:
                profile = resolve_profile_name(framework_profile)
                profile_path = repo_root / PROFILE_ONTOLOGY_TEMPLATE.format(
                    profile=profile
                )
                if not profile_path.exists():
                    errors.append(
                        f"framework_profile = \"{framework_profile}\" but "
                        f"profile ontology not found at {profile_path}"
                    )
                else:
                    try:
                        profile_doc = load_toml(profile_path)
                    except tomllib.TOMLDecodeError as exc:
                        errors.append(
                            f"profile ontology parse failure ({profile_path}): {exc}"
                        )
                    else:
                        ontologies.append((str(profile_path), profile_doc))
                        errors.extend(validate_ontology(profile_doc, str(profile_path)))

            if not errors:
                id_prefixes, id_patterns, predicate_to_relation = build_resolver(
                    ontologies
                )
                errors.extend(
                    validate_instance(
                        doc,
                        str(path),
                        id_prefixes,
                        id_patterns,
                        predicate_to_relation,
                    )
                )

    if errors:
        print("IJB CONFORMANCE VALIDATION FAILED")
        print(f"- file: {path}")
        for err in errors:
            print(f"- {err}")
        return 1

    print("IJB CONFORMANCE VALIDATION PASSED")
    print(f"- file: {path}")
    print(f"- template_kind: {template_kind}")
    if framework_profile:
        print(f"- framework_profile: {framework_profile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
