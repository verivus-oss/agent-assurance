#!/usr/bin/env python3
"""Validate `state-mutation` instances against the com.verivus.runtime kind's
producer obligations RKM02 (mandatory, complete execution proof), RKM03 (no
inlined secrets or payloads) and RKM04 (bound-tuple consistency).

This is the profile-layer mechanical checker referenced by
`profiles/com.verivus.runtime/state-mutation-kind.toml`. The SPEC-layer
invariants are enforced elsewhere and are NOT duplicated here:

  * five-record closure (RKM01)      -> validators/validate_closure_root.py
  * provenance source-byte binding   -> validators/validate_provenance.py
  * RKM05 (ontology resolution)      -> validators/validate_ijb_conformance.py

What this validator enforces, per the kind descriptor:

  RKM02  `[execution_proof]` is present and carries all of `scheme`,
         `finality_basis`, `proof_sha256`, `binds_sha256`. `scheme` and
         `finality_basis` are drawn from the closed profile vocabularies.
         There is no producer-attested tier: an absent proof is an error,
         never a downgrade.

  RKM03  `[mutation]` and `[execution_proof]` carry closed key sets. Any
         unknown key is rejected, which is what makes "no inlined payload
         or credential" mechanical rather than aspirational: there is no
         field for a secret to live in.

  RKM04  `execution_proof.binds_sha256` equals the SHA-256 of the canonical
         bound tuple recomputed from the document's own fields, in the SPEC
         12.8 record form (`<field> <value>\\n`, bytewise sorted,
         concatenated).

What this validator deliberately does NOT do, per the kind descriptor: it
does not fetch `proof_locator`, does not open or verify the proof artefact,
does not resolve ledger inclusion, and does not treat `finality_basis` as
anything but a recorded producer claim. Those are RUNTIME-SPEC.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys

import _toml11 as tomllib  # TOML 1.1 reference shim; see validators/_toml11.py

DIGEST_RE = re.compile(r"^(sha256:[0-9a-f]{64}|sha384:[0-9a-f]{96}|sha512:[0-9a-f]{128})\Z")

# The tuple RKM04 binds, in the order the kind descriptor names them. The
# canonical form sorts bytewise, so this list is documentation, not ordering.
BOUND_TUPLE_FIELDS = (
    "mutation.target_id",
    "mutation.operation",
    "mutation.authorization_sha256",
    "mutation.effect_sha256",
    "mutation.performed_at",
)

ALLOWED_MUTATION_KEYS = frozenset(
    {
        "performed_at",
        "target_id",
        "operation",
        "authorization_sha256",
        "effect_sha256",
    }
)

ALLOWED_PROOF_KEYS = frozenset(
    {
        "scheme",
        "finality_basis",
        "proof_sha256",
        "binds_sha256",
        "proof_locator",
    }
)

REQUIRED_PROOF_KEYS = ("scheme", "finality_basis", "proof_sha256", "binds_sha256")


def is_digest(value: object) -> bool:
    return isinstance(value, str) and bool(DIGEST_RE.match(value))


def load_vocabulary(repo_root: pathlib.Path, attribute: str) -> set[str]:
    """Read a closed vocabulary from the profile ontology.

    Loaded rather than duplicated, so the validator cannot drift from the
    ontology the way a hard-coded list would.
    """
    ont = repo_root / "profiles" / "com.verivus.runtime" / "ontology.toml"
    data = tomllib.loads(ont.read_text())
    for entry in data.get("attribute_vocabularies", []):
        if entry.get("attribute") == attribute:
            return {str(v) for v in entry.get("values", []) if isinstance(v, str)}
    raise SystemExit(
        f"profile ontology is missing the `{attribute}` vocabulary (looked in {ont})"
    )


def canonical_bound_tuple(doc: dict) -> str:
    """The SPEC 12.8 record form over the five bound fields.

    One `<field> <value>\\n` record per field, bytewise sorted, concatenated.
    Identical in shape to the closure stream, deliberately: a producer that
    can emit a closure root can emit this with the same code path.
    """
    records = []
    for dotted in BOUND_TUPLE_FIELDS:
        table, key = dotted.split(".", 1)
        value = doc.get(table, {}).get(key)
        records.append(f"{dotted} {value}\n".encode())
    records.sort()
    return "sha256:" + hashlib.sha256(b"".join(records)).hexdigest()


def check_keys(table: dict, allowed: frozenset, dotted: str, errors: list[str]) -> None:
    for key in sorted(set(table) - allowed):
        errors.append(
            f"{dotted}.{key} is not a permitted key (RKM03 closed key set; "
            f"payloads, credentials and proof bodies have no field to live in)"
        )


def validate_one(path: pathlib.Path, repo_root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    doc = tomllib.loads(path.read_text())

    if doc.get("meta", {}).get("template_kind") != "state-mutation":
        return errors  # not our kind; the discovery caller decides what that means

    mutation = doc.get("mutation")
    if not isinstance(mutation, dict):
        errors.append(f"{path}: missing required `[mutation]` table")
        mutation = {}
    else:
        check_keys(mutation, ALLOWED_MUTATION_KEYS, "mutation", errors)

    for key in ("authorization_sha256", "effect_sha256"):
        value = mutation.get(key)
        if value is None:
            errors.append(f"{path}: mutation.{key} is required")
        elif not is_digest(value):
            errors.append(
                f"{path}: mutation.{key} {value!r} is not a digest scalar "
                f"(RKM03: this field carries a digest, never a payload)"
            )

    for key in ("performed_at", "target_id", "operation"):
        if not isinstance(mutation.get(key), str) or not mutation.get(key):
            errors.append(f"{path}: mutation.{key} is required and MUST be a non-empty string")

    # RKM02: the proof is mandatory and complete. An absent table is an
    # error, never a producer-attested downgrade.
    proof = doc.get("execution_proof")
    if not isinstance(proof, dict):
        errors.append(
            f"{path}: missing required `[execution_proof]` table (RKM02). A record of an "
            f"irreversible state change with no execution proof is not a state-mutation; "
            f"use an observation-shaped or intent-shaped kind instead"
        )
        proof = {}
    else:
        check_keys(proof, ALLOWED_PROOF_KEYS, "execution_proof", errors)

    for key in REQUIRED_PROOF_KEYS:
        if key not in proof:
            errors.append(f"{path}: execution_proof.{key} is required (RKM02)")

    for key in ("proof_sha256", "binds_sha256"):
        value = proof.get(key)
        if value is not None and not is_digest(value):
            errors.append(f"{path}: execution_proof.{key} {value!r} is not a digest scalar")

    schemes = load_vocabulary(repo_root, "execution_proof_scheme")
    finalities = load_vocabulary(repo_root, "finality_basis")
    scheme = proof.get("scheme")
    if scheme is not None and scheme not in schemes:
        errors.append(
            f"{path}: execution_proof.scheme {scheme!r} is not in the closed "
            f"`execution_proof_scheme` vocabulary {sorted(schemes)}"
        )
    finality = proof.get("finality_basis")
    if finality is not None and finality not in finalities:
        errors.append(
            f"{path}: execution_proof.finality_basis {finality!r} is not in the closed "
            f"`finality_basis` vocabulary {sorted(finalities)}"
        )

    # RKM04: the proof must be bound to THIS mutation, not merely exist.
    declared = proof.get("binds_sha256")
    if is_digest(declared) and all(
        isinstance(mutation.get(f.split(".", 1)[1]), str) for f in BOUND_TUPLE_FIELDS
    ):
        expected = canonical_bound_tuple(doc)
        if declared != expected:
            errors.append(
                f"{path}: execution_proof.binds_sha256 {declared} does not equal the digest of "
                f"the canonical bound tuple recomputed from this document ({expected}) "
                f"(RKM04 bound-tuple consistency). The proof does not commit to this mutation."
            )

    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate `state-mutation` instances (RKM02, RKM03, RKM04)."
    )
    parser.add_argument("files", nargs="+", help="TOML files to inspect.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to load the profile ontology vocabularies.",
    )
    args = parser.parse_args(argv)
    repo_root = pathlib.Path(args.repo_root).resolve()

    errors: list[str] = []
    inspected = 0
    instances = 0
    for name in args.files:
        path = pathlib.Path(name)
        inspected += 1
        try:
            doc = tomllib.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001 - report, do not crash the sweep
            errors.append(f"{path}: could not parse: {exc}")
            continue
        if doc.get("meta", {}).get("template_kind") == "state-mutation":
            instances += 1
        errors.extend(validate_one(path, repo_root))

    if errors:
        print("STATE-MUTATION VALIDATION FAILED")
        print(f"- files inspected: {inspected}")
        print(f"- state-mutation instances: {instances}")
        for err in errors:
            print(f"- ERROR: {err}")
        return 1

    print("STATE-MUTATION VALIDATION PASSED")
    print(f"- files inspected: {inspected}")
    print(f"- state-mutation instances: {instances}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
