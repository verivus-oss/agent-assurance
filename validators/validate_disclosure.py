#!/usr/bin/env python3
"""Validate disclosure-profile instance files.

Implements the hard invariants declared in the three disclosure
kind-descriptors:

  disclosure-attestation:
    INV01 — each attestation's `disclosure_posture` is drawn from the
            closed vocabulary in profiles/disclosure/ontology.toml.
    INV02 — `disclosure_posture = "partial"` requires at least one
            `covered_by` entry referencing a `RED:` id.
    INV03 — `disclosure_posture = "embargoed"` requires
            `[meta].embargo_until` (SPEC §2.7 cross-field rule).

  redaction-manifest:
    INV01 — `redaction_method` drawn from the (extensible) vocabulary.
    INV02 — `redaction_reason` drawn from the (extensible) vocabulary.
    INV03 — `redaction_reason = "other"` requires a non-empty `notes`.

  selective-disclosure-proof:
    INV01 — `bound_source` matches `^sha256:[0-9a-f]{64}$`.
    INV02 — `proof_scheme` drawn from the (extensible) vocabulary.
    INV03 — every `covers` entry starts with the `RED:` prefix.

The validator loads `profiles/disclosure/ontology.toml` to pull the
declared closed value sets, so any future change to the ontology is
picked up without editing this file.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py


SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate disclosure-profile instance files.",
    )
    parser.add_argument("files", nargs="+", help="disclosure instance TOML files")
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Repository root (used to load the disclosure profile ontology).",
    )
    return parser.parse_args()


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_vocabularies(repo_root: pathlib.Path) -> dict[str, dict]:
    """Return {attribute_name: {values: [...], extensible: bool}} from
    the disclosure profile ontology."""
    ontology_path = repo_root / "profiles" / "disclosure" / "ontology.toml"
    out: dict[str, dict] = {}
    if not ontology_path.is_file():
        return out
    try:
        doc = load_toml(ontology_path)
    except tomllib.TOMLDecodeError:
        return out
    for entry in doc.get("attribute_vocabularies", []) or []:
        attr = entry.get("attribute")
        if not isinstance(attr, str):
            continue
        out[attr] = {
            "values": list(entry.get("values") or []),
            "extensible": bool(entry.get("extensible", False)),
        }
    return out


def _check_vocab(
    attribute: str,
    value: object,
    vocabs: dict[str, dict],
    location: str,
) -> list[str]:
    spec = vocabs.get(attribute)
    if spec is None:
        return [
            f"{location}: ontology missing attribute_vocabulary `{attribute}` "
            f"(cannot enforce closure)"
        ]
    if not isinstance(value, str):
        return [f"{location}: `{attribute}` must be a string"]
    if value in spec["values"]:
        return []
    if spec["extensible"]:
        # extensible vocabularies accept new values silently — SPEC layer
        # only enforces shape (string), not membership.
        return []
    return [
        f"{location}: `{attribute} = \"{value}\"` is not in the closed "
        f"vocabulary {spec['values']}"
    ]


def validate_attestation(doc: dict, source: str, vocabs: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    meta = doc.get("meta") or {}
    embargo_until = meta.get("embargo_until")

    attestations = doc.get("attestations")
    if not isinstance(attestations, list) or not attestations:
        errors.append(f"{source}: at least one `[[attestations]]` entry required")
        return errors

    for idx, entry in enumerate(attestations):
        if not isinstance(entry, dict):
            errors.append(f"{source}:attestations[{idx}]: must be a table")
            continue
        loc = f"{source}:attestations[{idx}]"
        ent_id = entry.get("id")
        if not isinstance(ent_id, str) or not ent_id.startswith("DISC:"):
            errors.append(f"{loc}: `id` must start with `DISC:`")

        posture = entry.get("disclosure_posture")
        errors.extend(_check_vocab(
            "disclosure_posture", posture, vocabs, f"{loc}.disclosure_posture"
        ))

        # INV02 — partial requires covered_by RED:* entries
        if posture == "partial":
            covered_by = entry.get("covered_by") or []
            if not isinstance(covered_by, list) or not any(
                isinstance(v, str) and v.startswith("RED:") for v in covered_by
            ):
                errors.append(
                    f"{loc}: `disclosure_posture = \"partial\"` requires at "
                    f"least one `covered_by` entry referencing a `RED:` id"
                )

        # INV03 — embargoed requires meta.embargo_until
        if posture == "embargoed":
            if not isinstance(embargo_until, str) or not embargo_until:
                errors.append(
                    f"{loc}: `disclosure_posture = \"embargoed\"` requires "
                    f"`[meta].embargo_until` to be set (SPEC §2.7)"
                )

    return errors


def validate_redaction_manifest(
    doc: dict, source: str, vocabs: dict[str, dict]
) -> list[str]:
    errors: list[str] = []
    redactions = doc.get("redactions")
    if not isinstance(redactions, list) or not redactions:
        errors.append(f"{source}: at least one `[[redactions]]` entry required")
        return errors

    for idx, entry in enumerate(redactions):
        if not isinstance(entry, dict):
            errors.append(f"{source}:redactions[{idx}]: must be a table")
            continue
        loc = f"{source}:redactions[{idx}]"
        ent_id = entry.get("id")
        if not isinstance(ent_id, str) or not ent_id.startswith("RED:"):
            errors.append(f"{loc}: `id` must start with `RED:`")

        method = entry.get("redaction_method")
        errors.extend(_check_vocab(
            "redaction_method", method, vocabs, f"{loc}.redaction_method"
        ))
        reason = entry.get("redaction_reason")
        errors.extend(_check_vocab(
            "redaction_reason", reason, vocabs, f"{loc}.redaction_reason"
        ))

        # INV03 — reason="other" requires notes
        if reason == "other":
            notes = entry.get("notes")
            if not isinstance(notes, str) or not notes.strip():
                errors.append(
                    f"{loc}: `redaction_reason = \"other\"` requires a "
                    f"non-empty `notes` field justifying the use of the "
                    f"open reason"
                )

    return errors


def validate_proof(doc: dict, source: str, vocabs: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    proofs = doc.get("proofs")
    if not isinstance(proofs, list) or not proofs:
        errors.append(f"{source}: at least one `[[proofs]]` entry required")
        return errors

    for idx, entry in enumerate(proofs):
        if not isinstance(entry, dict):
            errors.append(f"{source}:proofs[{idx}]: must be a table")
            continue
        loc = f"{source}:proofs[{idx}]"
        ent_id = entry.get("id")
        if not isinstance(ent_id, str) or not ent_id.startswith("SDP:"):
            errors.append(f"{loc}: `id` must start with `SDP:`")

        bound = entry.get("bound_source")
        if not isinstance(bound, str) or not SHA256_RE.match(bound):
            errors.append(
                f"{loc}: `bound_source` must match `^sha256:[0-9a-f]{{64}}$` "
                f"(got {bound!r})"
            )

        scheme = entry.get("proof_scheme")
        errors.extend(_check_vocab(
            "proof_scheme", scheme, vocabs, f"{loc}.proof_scheme"
        ))

        covers = entry.get("covers") or []
        if isinstance(covers, list):
            for cidx, cov in enumerate(covers):
                if not isinstance(cov, str) or not cov.startswith("RED:"):
                    errors.append(
                        f"{loc}.covers[{cidx}]: every entry must start with "
                        f"`RED:` (got {cov!r})"
                    )

    return errors


def validate_one(path: pathlib.Path, vocabs: dict[str, dict]) -> list[str]:
    try:
        doc = load_toml(path)
    except FileNotFoundError:
        return [f"{path}: file not found"]
    except tomllib.TOMLDecodeError as exc:
        return [f"{path}: invalid TOML: {exc}"]

    meta = doc.get("meta") or {}
    tk = meta.get("template_kind")
    if tk == "disclosure-attestation":
        return validate_attestation(doc, str(path), vocabs)
    if tk == "redaction-manifest":
        return validate_redaction_manifest(doc, str(path), vocabs)
    if tk == "selective-disclosure-proof":
        return validate_proof(doc, str(path), vocabs)
    return [
        f"{path}: template_kind `{tk!r}` is not a disclosure-profile kind "
        f"(expected disclosure-attestation, redaction-manifest, or "
        f"selective-disclosure-proof)"
    ]


def main() -> int:
    args = parse_args()
    repo_root = pathlib.Path(args.repo_root).resolve()
    vocabs = load_vocabularies(repo_root)

    all_errors: list[str] = []
    for raw in args.files:
        path = pathlib.Path(raw).resolve()
        errs = validate_one(path, vocabs)
        if errs:
            all_errors.append(f"--- {path} ---")
            all_errors.extend(errs)

    if all_errors:
        print("DISCLOSURE VALIDATION FAILED")
        for line in all_errors:
            print(f"- {line}")
        return 1
    print("DISCLOSURE VALIDATION PASSED")
    print(f"- files validated: {len(args.files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
