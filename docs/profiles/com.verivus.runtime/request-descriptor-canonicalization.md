# Canonical request descriptor (com.verivus.runtime / api-snapshot)

Normative basis for hard invariant **RKV02** of the `api-snapshot` kind
(`profiles/com.verivus.runtime/api-snapshot-kind.toml`). It defines the exact
byte form whose SHA-256 is `snapshot.request.descriptor_sha256`, so a verifier
can recompute that digest and a producer cannot smuggle a raw header value into
the document.

## Why a canonical descriptor

An api-snapshot publishes only digests, never payloads. The request is one of
those payloads: its method, URL, and the values of its significant headers
(some of which — `authorization`, `cookie`, … — are secrets) MUST NOT appear
raw in the document. RKV02 makes that mechanical: the document carries
`descriptor_sha256` (a digest scalar), and header values live *inside* the
hashed descriptor as digests, never as cleartext. A document that inlines a raw
secret-bearing header, or writes a header value where a digest is required,
fails `validators/validate_api_snapshot.py`.

## Canonical form (schema_version 0.1.0)

The canonical request descriptor is UTF-8 text, LF (`\n`)-terminated lines, in
this exact order:

```
method: <UPPERCASE-HTTP-METHOD>\n
url: <effective-request-URL, query parameters sorted bytewise by raw key>\n
header: <lowercase-header-name> sha256:<hex-digest-of-the-header-value>\n   (zero or more, see below)
```

Rules:

1. **method** — the HTTP method, uppercased (`GET`, `POST`, …).
2. **url** — the effective request URL. Query parameters are sorted in
   ascending bytewise order of their raw (percent-encoded) key; the path and
   scheme/host are left as observed. Sorting makes the descriptor independent of
   the order in which a client happened to emit query parameters.
3. **header lines** — one line per header named in
   `snapshot.request.significant_headers`, sorted bytewise by the lowercased
   header name. Each line carries the lowercased header name and
   `sha256:<hex>`, the SHA-256 of the header **value** bytes (UTF-8). The value
   itself never appears. Headers not listed in `significant_headers` are out of
   scope and contribute nothing.
4. Every line, including the last, ends with a single `\n`. The descriptor is
   the exact concatenation of these lines, with no leading/trailing whitespace
   and no blank lines.

`descriptor_sha256 = "sha256:" + hex(SHA-256(descriptor-bytes))`.

## Worked example (matches `examples/minimal-api-snapshot.toml`)

For `method = GET`, the sorted-query URL
`https://api.exchange.example/v1/quotes/USD-AUD?asof=2026-06-17T09:14:00Z&pair=USD-AUD`,
and one significant header `accept` whose value is `application/json`, the
descriptor bytes are:

```
method: GET
url: https://api.exchange.example/v1/quotes/USD-AUD?asof=2026-06-17T09:14:00Z&pair=USD-AUD
header: accept sha256:<sha256("application/json")>
```

(each line LF-terminated). The committed capture artefact
`examples/captures/2026-06-17T091402Z-usd-aud.capture` embeds these exact bytes;
`descriptor_sha256` in the example instance is the SHA-256 of them, and the
reproducible builder `docs/reviews/2026-06-17-com-verivus-runtime-api-snapshot/build_api_snapshot_digests.py` regenerates the
value from first principles.

## Capture artefact format `DAGTOML-API-CAPTURE/1` (the basis for RKV01)

The bytes at `provenance.source_path` are producer-defined in general, but this
profile ships one documented, self-describing form so the sub-part digests can
be verified mechanically. A `DAGTOML-API-CAPTURE/1` capture is UTF-8, LF-line
framed:

```
DAGTOML-API-CAPTURE/1\n
captured-at: <rfc3339>\n
source-id: <url>\n
request-descriptor-sha256: <sha256:hex>\n
request-descriptor:\n
<canonical request descriptor bytes, exactly as defined above>
response-status: <int>\n
response-body-sha256: <sha256:hex>\n
response-body:\n
<response body bytes to EOF>
```

The **request-descriptor sub-part** is the bytes between the line
`request-descriptor:\n` and the line `response-status:`; the **response-body
sub-part** is the bytes after `response-body:\n` to end-of-file.
`validators/validate_api_snapshot.py` (RKV01) recomputes the SHA-256 of each
sub-part and requires it to equal `snapshot.request.descriptor_sha256` and
`snapshot.response.body_sha256` respectively. A capture in any other format is
not parsed, and its sub-part consistency is a RUNTIME-SPEC producer obligation.

## Out of scope (RUNTIME-SPEC)

This addendum fixes the SPEC-layer byte form only. Re-issuing the request,
verifying TLS, resolving header-value digests back to plaintext, and checking
that the descriptor matches what a server actually received are runtime
concerns, outside the api-snapshot document's envelope (which denies all I/O).
