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

REQUIRED_PROOF_KEYS = (
    "scheme",
    "finality_basis",
    "proof_sha256",
    "binds_sha256",
    "proof_locator",
)

# Value grammars for the non-digest bound fields. Defence in depth behind the
# prehashed encoding: control characters can no longer forge a tuple, but a
# field that accepts arbitrary text is still a place to smuggle a payload.
# ASCII digits explicitly: `\d` on a str pattern also matches Unicode decimal
# digits, so `\d{4}` accepts `٢026` while the Rust and Go primaries reject it.
# Differential testing found that divergence.
RFC3339_UTC_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,9})?Z\Z"
)
OPERATION_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}\Z")
# A locator is a URI-shaped reference, never a payload. Bounded, no
# whitespace, no control characters.
LOCATOR_RE = re.compile(r"^[a-z][a-z0-9+.-]*:[^\s\x00-\x1f\x7f]{1,480}\Z")
# `target_id` is a URI or URN naming the mutated resource.
TARGET_ID_RE = re.compile(r"^[a-z][a-z0-9+.-]*:[^\s\x00-\x1f\x7f]{1,480}\Z")

# RKM06: a scheme may only claim durability its own evidence class can carry.
# A counterparty receipt cannot assert ledger finality; a TEE quote attests an
# execution environment, not durability of the effect.
SCHEME_FINALITY = {
    "ledger-transaction": {"none", "ledger-confirmed", "ledger-final"},
    "zk-receipt": {"none", "ledger-confirmed", "ledger-final"},
    "provider-receipt": {"none", "provider-acknowledged"},
    "tee-quote": {"none"},
}


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
    """The SPEC 12.8.2 bound-tuple digest over the five bound fields.

    Each field emits `<field> sha256:<64 lowercase hex>\\n`, where the digest
    is taken over the UTF-8 bytes of the field's VALUE. Records are sorted
    bytewise and concatenated, and the tuple digest is the SHA-256 of that
    stream.

    The values are PREHASHED rather than inlined, which is the whole point of
    this function. Inlining
    raw values makes the encoding non-injective: a value containing a newline
    can forge a different field/value assignment with an identical digest, so
    one `binds_sha256` could bind two distinct mutations. That was demonstrated
    against the first implementation, with a newline-bearing
    `operation` and a newline-bearing `performed_at` colliding.

    Prehashing removes the class of attack rather than filtering for it: every
    record is now a fixed-width digest scalar with no attacker-controlled
    bytes in delimiter position, and the record type contract becomes
    identical to the SPEC 12.8.1 pinned records (digest-only). The value
    grammars enforced in `validate_one` are defence in depth, not the primary
    control.
    """
    records = []
    for dotted in BOUND_TUPLE_FIELDS:
        table, key = dotted.split(".", 1)
        value = doc.get(table, {}).get(key)
        value_digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
        records.append(f"{dotted} sha256:{value_digest}\n".encode())
    records.sort()
    return "sha256:" + hashlib.sha256(b"".join(records)).hexdigest()


def check_keys(table: dict, allowed: frozenset, dotted: str, errors: list[str]) -> None:
    for key in sorted(set(table) - allowed):
        errors.append(
            f"{dotted}.{key} is not a permitted key (RKM03 closed key set; "
            f"payloads, credentials and proof bodies have no field to live in)"
        )


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    return 30 if month in (4, 6, 9, 11) else 31


def is_rfc3339_utc(value: str) -> bool:
    """Shape AND calendar validity.

    The shape check alone accepts `2026-99-26T10:15:00Z`: it constrains digit
    positions, not what those digits can mean. `performed_at` is a member of
    the RKM04 bound tuple and carries the freshness claim, so a timestamp that
    cannot correspond to any instant is worth rejecting rather than binding.
    """
    if not RFC3339_UTC_RE.match(value):
        return False
    year, month, day = int(value[0:4]), int(value[5:7]), int(value[8:10])
    hour, minute, second = int(value[11:13]), int(value[14:16]), int(value[17:19])
    if not 1 <= month <= 12 or not 1 <= day <= _days_in_month(year, month):
        return False
    # Second 60 is a leap second, which RFC3339 5.6 permits.
    return hour <= 23 and minute <= 59 and second <= 60


def _validate_mutation_table(doc: dict, path: pathlib.Path) -> list[str]:
    """The `[mutation]` checks shared by state-mutation and mutation-claim.

    Both kinds carry an identical table by design, so a claim can be promoted
    to a proved record without rewriting any of it. Sharing the code is what
    keeps that promise true rather than aspirational.
    """
    errors: list[str] = []
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

    for key, accepts, shape in (
        (
            "performed_at",
            is_rfc3339_utc,
            "an RFC3339 UTC timestamp ending in Z, naming a real instant",
        ),
        ("operation", OPERATION_RE.match, "a bare lowercase token, at most 64 characters"),
        ("target_id", TARGET_ID_RE.match, "a URI or URN, no whitespace or control characters"),
    ):
        value = mutation.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"{path}: mutation.{key} is required and MUST be a non-empty string")
        elif not accepts(value):
            errors.append(
                f"{path}: mutation.{key} {value!r} must be {shape}. Unconstrained text here is "
                f"both a payload-smuggling surface (RKM03) and, before the SPEC 12.8.2 prehashed "
                f"encoding, was a bound-tuple forgery surface (RKM04)"
            )

    # RKM04 depends on `provenance.source_sha256` being present and pinned; the
    # kind declares it required, so check it rather than assuming the closure
    # layer covers every case (a document with no [provenance] at all reaches
    # here).
    provenance = doc.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(
            f"{path}: missing required `[provenance]` table. "
            f"`provenance.source_sha256` is a required field of this kind"
        )
    elif not is_digest(provenance.get("source_sha256")):
        errors.append(
            f"{path}: provenance.source_sha256 {provenance.get('source_sha256')!r} "
            f"is required and MUST be a digest scalar"
        )

    return errors


def validate_one(path: pathlib.Path, repo_root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    doc = tomllib.loads(path.read_text())

    kind = doc.get("meta", {}).get("template_kind")
    if kind not in ("state-mutation", "mutation-claim"):
        return errors  # not our kind; the discovery caller decides what that means

    # `mutation-claim` shares the `[mutation]` table and its grammars, so
    # promoting a claim to a proved record is mechanical. What it must NOT
    # carry is a proof: RKC02. Checked first so the message is the useful one
    # rather than a cascade of missing-proof errors from the RKM02 path.
    if kind == "mutation-claim":
        if "execution_proof" in doc:
            errors.append(
                f"{path}: a mutation-claim MUST NOT carry `[execution_proof]` (RKC02). "
                f"A document with a proof is a state-mutation and MUST declare "
                f"`template_kind = \"state-mutation\"`, so that RKM02, RKM04 and RKM06 apply "
                f"to it rather than proof-shaped fields no invariant governs"
            )
        errors.extend(_validate_mutation_table(doc, path))
        return errors

    errors.extend(_validate_mutation_table(doc, path))

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

    # RKM06: scheme and finality must be coherent.
    if scheme in SCHEME_FINALITY and finality in finalities:
        allowed = SCHEME_FINALITY[scheme]
        if finality not in allowed:
            errors.append(
                f"{path}: execution_proof scheme {scheme!r} cannot claim "
                f"finality_basis {finality!r} (RKM06). A {scheme} carries evidence for "
                f"{sorted(allowed)} only: a counterparty receipt cannot assert ledger "
                f"finality, and a TEE quote attests an execution environment rather than "
                f"the durability of the effect"
            )

    locator = proof.get("proof_locator")
    if locator is not None and (not isinstance(locator, str) or not LOCATOR_RE.match(locator)):
        errors.append(
            f"{path}: execution_proof.proof_locator {locator!r} must be a URI-shaped "
            f"reference (scheme:rest, no whitespace or control characters, at most 480 "
            f"characters after the scheme). A locator names where the proof can be "
            f"fetched; it is not a place to inline the proof itself (RKM03)"
        )

    # RKM04: the proof must be bound to THIS mutation, not merely exist.
    mutation = doc.get("mutation") if isinstance(doc.get("mutation"), dict) else {}
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
