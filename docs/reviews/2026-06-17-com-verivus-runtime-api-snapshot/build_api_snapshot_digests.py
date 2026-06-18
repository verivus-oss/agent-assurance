#!/usr/bin/env python3
"""Deterministically build the api-snapshot capture + attestation artefacts and
compute every digest the fixtures cite. Reproducible builder (lives under the review dir,
regenerates the committed artefacts). Run from repo root:

    python3 docs/reviews/2026-06-17-com-verivus-runtime-api-snapshot/build_api_snapshot_digests.py

It writes:
  examples/captures/2026-06-17T091402Z-usd-aud.capture
  examples/captures/2026-06-17T091402Z-usd-aud.attestation
and prints the digest block to paste into the TOML fixtures.

Every value is a real SHA-256 over real bytes, so a reviewer with shell access
can recompute all of them.
"""
from __future__ import annotations

import hashlib
import pathlib

LF = b"\n"


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def digest(b: bytes) -> str:
    return "sha256:" + sha256_hex(b)


# --- response body (exact bytes the server returned) ------------------------
body = b'{"pair":"USD-AUD","rate":1.5217,"asof":"2026-06-17T09:14:00Z"}\n'
body_d = digest(body)

# --- canonical request descriptor (RKV02 normative form) --------------------
# Rules (see docs/.../request-descriptor canonicalization addendum):
#   * line 1: "method: <UPPERCASE-METHOD>"
#   * line 2: "url: <url with query parameters sorted bytewise by raw key>"
#   * one "header: <lowercase-name> sha256:<digest-of-value>" line per
#     significant header, sorted bytewise by header name. Header VALUES never
#     appear raw — only the digest of the value — which is what makes RKV02
#     ("no inlined secrets; header values carried as digests") mechanical.
#   * every line LF-terminated; UTF-8.
accept_value = b"application/json"
descriptor = (
    b"method: GET" + LF
    + b"url: https://api.exchange.example/v1/quotes/USD-AUD"
      b"?asof=2026-06-17T09:14:00Z&pair=USD-AUD" + LF
    + b"header: accept " + digest(accept_value).encode() + LF
)
descriptor_d = digest(descriptor)

# --- capture artefact (what provenance.source_sha256 pins) ------------------
# A single framed file holding the canonical request descriptor and the
# response body as literal sub-byte-ranges, so descriptor_sha256 / body_sha256
# are genuine digests of sub-parts of these exact bytes.
capture = (
    b"DAGTOML-API-CAPTURE/1" + LF
    + b"captured-at: 2026-06-17T09:14:02.481Z" + LF
    + b"source-id: https://api.exchange.example/v1/quotes/USD-AUD" + LF
    + b"request-descriptor-sha256: " + descriptor_d.encode() + LF
    + b"request-descriptor:" + LF
    + descriptor
    + b"response-status: 200" + LF
    + b"response-body-sha256: " + body_d.encode() + LF
    + b"response-body:" + LF
    + body
)
source_d = digest(capture)
source_bytes = len(capture)

# --- witness attestation artefact (separate; NOT folded into closure) -------
attestation = (
    b"DAGTOML-API-ATTESTATION/1" + LF
    + b"scheme: tls-notary" + LF
    + b"observed: both" + LF
    + b"attester: notary.example/ed25519:9f86d0818411" + LF
    + b"capture-sha256: " + source_d.encode() + LF
)
attestation_d = digest(attestation)

# --- closure roots ----------------------------------------------------------
# Source-only (the shipped SPEC 12.8 fold, byte-identical across py/rs/go):
#   records = ["provenance.source_sha256 <src>\n"], sorted, joined, hashed.
closure_source_only = digest(
    f"provenance.source_sha256 {source_d}\n".encode()
)

# Four-input (the profile-PROPOSED, NOT-YET-PROMOTED fold) — the value the
# bad-closure negative carries so the source-only validator rejects it.
four_records = sorted([
    f"provenance.source_sha256 {source_d}\n",
    f"snapshot.request.descriptor_sha256 {descriptor_d}\n",
    f"snapshot.response.body_sha256 {body_d}\n",
    f"snapshot.witness.attestation_sha256 {attestation_d}\n",
])
closure_four_input = digest("".join(four_records).encode())

EMPTY_SENTINEL = "sha256:" + sha256_hex(b"")

# --- write artefacts --------------------------------------------------------
cap_dir = pathlib.Path("examples/captures")
cap_dir.mkdir(parents=True, exist_ok=True)
cap_path = cap_dir / "2026-06-17T091402Z-usd-aud.capture"
att_path = cap_dir / "2026-06-17T091402Z-usd-aud.attestation"
cap_path.write_bytes(capture)
att_path.write_bytes(attestation)

# round-trip check
rt_d, rt_n = hashlib.sha256(cap_path.read_bytes()).hexdigest(), cap_path.stat().st_size
assert "sha256:" + rt_d == source_d, "capture digest drift"
assert rt_n == source_bytes, "capture byte drift"

print("=== ARTEFACTS WRITTEN ===")
print(f"{cap_path}  ({source_bytes} bytes)")
print(f"{att_path}  ({len(attestation)} bytes)")
print()
print("=== DIGEST BLOCK (paste into fixtures) ===")
print(f"source_path           = \"{cap_path.as_posix()}\"")
print(f"source_sha256         = \"{source_d}\"")
print(f"source_bytes          = {source_bytes}")
print(f"descriptor_sha256     = \"{descriptor_d}\"")
print(f"body_sha256           = \"{body_d}\"")
print(f"attestation_sha256    = \"{attestation_d}\"")
print()
print(f"closure_root (source-only, POSITIVE instance) = \"{closure_source_only}\"")
print(f"closure_root (4-input,  NEGATIVE bad-closure) = \"{closure_four_input}\"")
print(f"empty sentinel (descriptors/ontology/PROFILE) = \"{EMPTY_SENTINEL}\"")
