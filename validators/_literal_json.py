"""Decode JSON with explicit whitespace handling and the standard value scanner.

JSONDecoder.decode uses a regular expression for surrounding whitespace.
raw_decode delegates value parsing to the C scanner without that matcher.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, TextIO


WHITESPACE = " \t\n\r"


class InvalidJSON(ValueError):
    """A source identity and byte span without saved line coordinates."""

    def __init__(self, source: str, position: int) -> None:
        raw = source.encode("utf-8", errors="surrogatepass")
        start = len(source[:position].encode("utf-8", errors="surrogatepass"))
        end = min(len(raw), start + len(source[position:position + 1].encode("utf-8", errors="surrogatepass")))
        self.source_sha256 = hashlib.sha256(raw).hexdigest()
        self.byte_span = (start, end)
        super().__init__(f"invalid JSON (source sha256 {self.source_sha256}, bytes {start}:{end})")


def loads(source: str | bytes, **options: Any) -> Any:
    value_scanner = getattr(json.scanner, "c_make_scanner", None)
    string_scanner = getattr(json.decoder, "c_scanstring", None)
    if (value_scanner is None or json.scanner.make_scanner is not value_scanner
            or string_scanner is None or json.decoder.scanstring is not string_scanner):
        raise RuntimeError("regex-free JSON scanner is unavailable")
    if isinstance(source, bytes):
        source = source.decode("utf-8")
    if not isinstance(source, str):
        raise TypeError("JSON source must be text or UTF-8 bytes")
    start = 0
    while start < len(source) and source[start] in WHITESPACE:
        start += 1
    try:
        value, end = json.JSONDecoder(**options).raw_decode(source, start)
    except json.JSONDecodeError as exc:
        failure = exc.pos
    else:
        failure = None
    if failure is not None:
        raise InvalidJSON(source, failure)
    while end < len(source) and source[end] in WHITESPACE:
        end += 1
    if end != len(source):
        raise InvalidJSON(source, end)
    return value


def _require_c_encoder() -> None:
    text_encoder = getattr(json.encoder, "c_encode_basestring", None)
    ascii_encoder = getattr(json.encoder, "c_encode_basestring_ascii", None)
    if (
        text_encoder is None
        or ascii_encoder is None
        or json.encoder.encode_basestring is not text_encoder
        or json.encoder.encode_basestring_ascii is not ascii_encoder
    ):
        raise RuntimeError("regex-free JSON string encoder is unavailable")


def dumps(value: Any, **options: Any) -> str:
    _require_c_encoder()
    return json.dumps(value, **options)


def dump(value: Any, output: TextIO, **options: Any) -> None:
    _require_c_encoder()
    json.dump(value, output, **options)
