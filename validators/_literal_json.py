"""Decode JSON with explicit whitespace handling and the standard value scanner.

JSONDecoder.decode uses a regular expression for surrounding whitespace.
raw_decode delegates value parsing to the C scanner without that matcher.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


WHITESPACE = " \t\n\r"


class InvalidJSON(ValueError):
    """A source identity and byte span without saved line coordinates."""

    def __init__(self, source: str, position: int) -> None:
        raw = source.encode("utf-8", errors="surrogatepass")
        start = len(source[:position].encode("utf-8", errors="surrogatepass"))
        end = min(len(raw), start + len(source[position:position + 1].encode("utf-8", errors="surrogatepass")))
        self.source_sha256 = hashlib.sha256(raw).hexdigest()
        self.byte_span = (start, end)
        super().__init__("invalid JSON at source sha256:" + self.source_sha256 + " byte span " + str(self.byte_span))


def loads(source: str | bytes, **options: Any) -> Any:
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
