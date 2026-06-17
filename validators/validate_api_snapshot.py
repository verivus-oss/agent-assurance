#!/usr/bin/env python3
"""Validate `api-snapshot` instances against the com.verivus.runtime kind's
producer obligations RKV01 (sub-part consistency), RKV02 (no inlined secrets /
raw header values) and RKV03 (witness conditional).

This is the profile-layer mechanical checker referenced by
`profiles/com.verivus.runtime/api-snapshot-kind.toml`. The SPEC-layer
invariants are enforced elsewhere and are NOT duplicated here —

  * source-hash closure (RKV01 outer digest) -> validators/validate_closure_root.py
  * provenance source-byte binding            -> validators/validate_provenance.py
  * RKV04 (ontology resolution)               -> validators/validate_ijb_conformance.py

What this validator enforces, per the kind descriptor:

  RKV02  No secret AND no raw header value is inlined. `[snapshot.request]`,
         `[snapshot.response]`, `[snapshot.witness]`, and `[snapshot]` admit a
         CLOSED set of keys; any other key is a raw payload/header field and is
         rejected (so `accept = "application/json"` or `authorization = "…"`
         under `[snapshot.request]` both fail). Significant headers are named
         (bare lowercase tokens), never `name: value` pairs. The request is
         pinned by `descriptor_sha256` — a digest over the canonical request
         descriptor (see request-descriptor-canonicalization.md), never by
         inlined header values.

  RKV01  Sub-part consistency. When `[provenance].source_path` resolves (under
         --repo-root) to a capture in the profile's `DAGTOML-API-CAPTURE/1`
         form, `snapshot.request.descriptor_sha256` and
         `snapshot.response.body_sha256` MUST equal the SHA-256 of the
         request-descriptor and response-body sub-parts embedded in that
         capture. (For a foreign, producer-defined capture format the
         validator cannot parse, sub-part consistency is a RUNTIME-SPEC
         producer obligation, exactly like re-fetching the URL.)

  RKV03  Witness conditional. When `snapshot.witness.present = true`, the block
         MUST carry `scheme` (witness_scheme vocabulary), `attester_id`,
         `attestation_sha256`, and `observed` (attester_observed vocabulary).

It also confirms the structural required fields (`captured_at`, `source_id`,
`request.method`, `request.descriptor_sha256`, `response.body_sha256`) are
present and that every digest-typed field is a well-formed `<algo>:<hex>`
scalar. It does NOT re-fetch the URL, verify the witness, or resolve the
attester — those are RUNTIME-SPEC.

Files whose `[meta].template_kind` is not `api-snapshot` PASS silently.

Usage:
    python3 validators/validate_api_snapshot.py <file.toml> [...] [--repo-root .]
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _toml11 as tomllib  # noqa: E402  (TOML 1.1 reference shim)

# Closed vocabularies — mirror profiles/com.verivus.runtime/ontology.toml
# [[attribute_vocabularies]]. Drift is caught by validate_ijb_conformance.py
# on the ontology itself.
WITNESS_SCHEMES = frozenset({"tls-notary", "provider-signature", "tee-quote"})
ATTESTER_OBSERVED = frozenset({"request", "response", "both"})

DIGEST_HEX_LEN = {"sha256": 64, "sha384": 96, "sha512": 128}
_DIGEST_RE = re.compile(r"^(sha256|sha384|sha512):([0-9a-f]+)$")

# Closed key sets per table. Any other key inlines a raw payload/header value,
# which RKV02 forbids (the document carries only digests).
ALLOWED_SNAPSHOT_KEYS = frozenset({"captured_at", "source_id", "request", "response", "witness"})
ALLOWED_REQUEST_KEYS = frozenset({"method", "url", "significant_headers", "descriptor_sha256", "auth_context"})
ALLOWED_RESPONSE_KEYS = frozenset({"status", "body_sha256"})
ALLOWED_WITNESS_KEYS = frozenset({"present", "scheme", "observed", "attester_id", "attestation_sha256"})

# Header names that carry credentials/session material — flagged with a
# secret-specific message even though the closed key sets already reject them.
SECRET_HEADER_NAMES = frozenset({
    "authorization", "proxy-authorization", "cookie", "set-cookie",
    "x-api-key", "api-key", "apikey", "x-auth-token",
    "x-amz-security-token", "authentication",
})

CAPTURE_MAGIC = b"DAGTOML-API-CAPTURE/1\n"


def is_digest(value: object) -> bool:
    if not isinstance(value, str):
        return False
    m = _DIGEST_RE.match(value)
    return bool(m) and len(m.group(2)) == DIGEST_HEX_LEN[m.group(1)]


def _sha256_digest(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def _check_keys(table: dict, allowed: frozenset, dotted: str, toml_path, errors: list[str]) -> None:
    for k in table:
        if k in allowed:
            continue
        kl = str(k).lower()
        if kl in SECRET_HEADER_NAMES:
            errors.append(
                f"{toml_path}: {dotted}.{k} inlines a secret-bearing header; "
                f"RKV02 forbids raw header values — pin them via the canonical "
                f"request descriptor digest instead"
            )
        else:
            errors.append(
                f"{toml_path}: {dotted}.{k} is not an allowed field; a raw "
                f"header/payload value MUST NOT be inlined — the document carries "
                f"only digests (RKV02). Allowed keys: {sorted(allowed)}"
            )


def verify_subparts(doc: dict, repo_root: pathlib.Path, toml_path, errors: list[str]) -> None:
    """RKV01 sub-part consistency for the profile's DAGTOML-API-CAPTURE/1 form."""
    prov = doc.get("provenance")
    if not isinstance(prov, dict):
        return
    sp = prov.get("source_path")
    if not isinstance(sp, str) or not sp.strip() or pathlib.PurePath(sp).is_absolute():
        return  # absent / absolute -> validate_provenance.py owns the binding
    cap = (repo_root / sp).resolve()
    if not cap.is_file():
        return  # missing -> validate_provenance.py reports it
    data = cap.read_bytes()
    if not data.startswith(CAPTURE_MAGIC):
        return  # foreign capture format -> sub-part consistency is RUNTIME-SPEC
    snap = doc.get("snapshot", {})
    req = snap.get("request", {}) if isinstance(snap, dict) else {}
    resp = snap.get("response", {}) if isinstance(snap, dict) else {}

    dmark, smark = b"request-descriptor:\n", b"response-status:"
    if dmark in data and smark in data:
        desc_bytes = data.split(dmark, 1)[1].split(smark, 1)[0]
        actual = _sha256_digest(desc_bytes)
        declared = req.get("descriptor_sha256")
        if declared != actual:
            errors.append(
                f"{toml_path}: snapshot.request.descriptor_sha256 {declared!r} does "
                f"not equal the SHA-256 of the request-descriptor sub-part of the "
                f"capture ({actual}) (RKV01 sub-part consistency)"
            )
    bmark = b"response-body:\n"
    if bmark in data:
        body_bytes = data.split(bmark, 1)[1]
        actual = _sha256_digest(body_bytes)
        declared = resp.get("body_sha256")
        if declared != actual:
            errors.append(
                f"{toml_path}: snapshot.response.body_sha256 {declared!r} does not "
                f"equal the SHA-256 of the response-body sub-part of the capture "
                f"({actual}) (RKV01 sub-part consistency)"
            )


def validate_one(toml_path: pathlib.Path, repo_root: pathlib.Path) -> list[str]:
    try:
        with toml_path.open("rb") as handle:
            doc = tomllib.load(handle)
    except FileNotFoundError:
        return [f"{toml_path}: file not found"]
    except tomllib.TOMLDecodeError as exc:
        return [f"{toml_path}: invalid TOML: {exc}"]

    meta = doc.get("meta")
    if not isinstance(meta, dict) or meta.get("template_kind") != "api-snapshot":
        return []  # not an api-snapshot — silently PASS

    errors: list[str] = []
    snapshot = doc.get("snapshot")
    if not isinstance(snapshot, dict):
        return [f"{toml_path}: [snapshot] table is required for an api-snapshot"]

    # --- RKV02: closed key sets (no inlined raw header/payload values) -------
    _check_keys(snapshot, ALLOWED_SNAPSHOT_KEYS, "snapshot", toml_path, errors)

    # --- structural required fields -----------------------------------------
    if not isinstance(snapshot.get("captured_at"), str) or not snapshot.get("captured_at", "").strip():
        errors.append(f"{toml_path}: snapshot.captured_at is required (RFC3339 string)")
    if not isinstance(snapshot.get("source_id"), str) or not snapshot.get("source_id", "").strip():
        errors.append(f"{toml_path}: snapshot.source_id is required (string)")

    request = snapshot.get("request")
    if not isinstance(request, dict):
        errors.append(f"{toml_path}: [snapshot.request] table is required")
        request = {}
    else:
        _check_keys(request, ALLOWED_REQUEST_KEYS, "snapshot.request", toml_path, errors)
        if not isinstance(request.get("method"), str):
            errors.append(f"{toml_path}: snapshot.request.method is required (string)")
        if not is_digest(request.get("descriptor_sha256")):
            errors.append(
                f"{toml_path}: snapshot.request.descriptor_sha256 must be a digest "
                f"scalar (<algo>:<hex>); got {request.get('descriptor_sha256')!r} "
                f"(RKV02: header values are carried in the canonical descriptor as digests)"
            )

    response = snapshot.get("response")
    if not isinstance(response, dict):
        errors.append(f"{toml_path}: [snapshot.response] table is required")
    else:
        _check_keys(response, ALLOWED_RESPONSE_KEYS, "snapshot.response", toml_path, errors)
        if not is_digest(response.get("body_sha256")):
            errors.append(
                f"{toml_path}: snapshot.response.body_sha256 must be a digest "
                f"scalar (<algo>:<hex>); got {response.get('body_sha256')!r}"
            )

    # significant_headers: bare lowercase header-name tokens only.
    sig = request.get("significant_headers")
    if sig is not None:
        if not isinstance(sig, list):
            errors.append(f"{toml_path}: snapshot.request.significant_headers must be an array of header-name strings")
        else:
            for h in sig:
                if not isinstance(h, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", h):
                    errors.append(
                        f"{toml_path}: snapshot.request.significant_headers entry {h!r} "
                        f"must be a bare lowercase header name; a ':' or whitespace means "
                        f"a header VALUE was inlined (RKV02)"
                    )

    # --- RKV03: witness conditional -----------------------------------------
    witness = snapshot.get("witness")
    if isinstance(witness, dict):
        _check_keys(witness, ALLOWED_WITNESS_KEYS, "snapshot.witness", toml_path, errors)
        present = witness.get("present")
        if not isinstance(present, bool):
            errors.append(f"{toml_path}: snapshot.witness.present must be a boolean")
        elif present:
            if witness.get("scheme") not in WITNESS_SCHEMES:
                errors.append(
                    f"{toml_path}: snapshot.witness.scheme must be one of "
                    f"{sorted(WITNESS_SCHEMES)} when present=true; got {witness.get('scheme')!r} (RKV03)"
                )
            if not isinstance(witness.get("attester_id"), str) or not witness.get("attester_id", "").strip():
                errors.append(f"{toml_path}: snapshot.witness.attester_id is required when present=true (RKV03)")
            if not is_digest(witness.get("attestation_sha256")):
                errors.append(
                    f"{toml_path}: snapshot.witness.attestation_sha256 must be a digest "
                    f"scalar when present=true; got {witness.get('attestation_sha256')!r} (RKV03)"
                )
            if witness.get("observed") not in ATTESTER_OBSERVED:
                errors.append(
                    f"{toml_path}: snapshot.witness.observed must be one of "
                    f"{sorted(ATTESTER_OBSERVED)} when present=true; got {witness.get('observed')!r} (RKV03)"
                )

    # --- RKV01: sub-part consistency against the capture --------------------
    verify_subparts(doc, repo_root, toml_path, errors)
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate api-snapshot instances (RKV01 / RKV02 / RKV03).")
    parser.add_argument("files", nargs="+", help="TOML files to inspect.")
    parser.add_argument("--repo-root", default=".", help="Repo root used to resolve [provenance].source_path.")
    args = parser.parse_args(argv)
    repo_root = pathlib.Path(args.repo_root).resolve()

    all_errors: list[str] = []
    checked = 0
    snapshots = 0
    for raw in args.files:
        path = pathlib.Path(raw)
        checked += 1
        try:
            with path.open("rb") as h:
                d = tomllib.load(h)
            if isinstance(d.get("meta"), dict) and d["meta"].get("template_kind") == "api-snapshot":
                snapshots += 1
        except Exception:
            pass
        all_errors.extend(validate_one(path, repo_root))

    if all_errors:
        print("API-SNAPSHOT VALIDATION FAILED")
        print(f"- files inspected: {checked}")
        print(f"- api-snapshot instances: {snapshots}")
        for err in all_errors:
            print(f"- ERROR: {err}")
        return 1

    print("API-SNAPSHOT VALIDATION PASSED")
    print(f"- files inspected: {checked}")
    print(f"- api-snapshot instances: {snapshots}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
