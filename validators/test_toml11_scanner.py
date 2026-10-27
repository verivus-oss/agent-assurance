#!/usr/bin/env python3
"""Independent TOML 1.1 examples for the vendored token scanners."""

import unittest
from datetime import date, datetime, time, timedelta, timezone

import _toml11 as tomllib
from _toml11_vendor._parser import skip_chars


class ParserTests(unittest.TestCase):
    def test_skip_chars_stops_at_boundary_and_nonmatching_char(self) -> None:
        self.assertEqual(skip_chars(" \tkey", 0, frozenset(" \t")), 2)
        self.assertEqual(skip_chars(" \t", 0, frozenset(" \t")), 2)
        self.assertEqual(skip_chars("", 0, frozenset(" \t")), 0)
        self.assertEqual(skip_chars("key", 0, frozenset(" \t")), 0)
        self.assertEqual(skip_chars("key", 3, frozenset(" \t")), 3)

    def test_skip_chars_does_not_wrap_negative_position(self) -> None:
        self.assertEqual(skip_chars("key ", -1, frozenset(" \t")), -1)

    def test_whitespace_endings_and_trailing_junk(self) -> None:
        for source, expected in (("", {}), (" \t", {}), ("value = 1 \t", {"value": 1})):
            with self.subTest(source=source):
                self.assertEqual(tomllib.loads(source), expected)
        with self.assertRaises(tomllib.TOMLDecodeError):
            tomllib.loads("value = 1 \tjunk")

    def test_numbers_and_times(self) -> None:
        document = tomllib.loads(
            "hex = 0xF_F\n"
            "binary = 0b1_0\n"
            "octal = 0o7_0\n"
            "decimal = -1_000\n"
            "fraction = 1_000.25e-2\n"
            "day = 2026-10-27\n"
            "clock = 12:34\n"
            "stamp = 2026-10-27T12:34:56.123456789+10:00\n"
        )
        self.assertEqual(document["hex"], 255)
        self.assertEqual(document["binary"], 2)
        self.assertEqual(document["octal"], 56)
        self.assertEqual(document["decimal"], -1000)
        self.assertEqual(document["fraction"], 10.0025)
        self.assertEqual(document["day"], date(2026, 10, 27))
        self.assertEqual(document["clock"], time(12, 34))
        self.assertEqual(
            document["stamp"],
            datetime(2026, 10, 27, 12, 34, 56, 123456,
                     tzinfo=timezone(timedelta(hours=10))),
        )

    def test_invalid_token_boundaries(self) -> None:
        for value in ("0x", "1_", "1e+", "24:00", "2026-13-27", "2026-10-27T12:34+24:00"):
            with self.subTest(value=value), self.assertRaises(tomllib.TOMLDecodeError):
                tomllib.loads(f"value = {value}\n")

    def test_error_uses_digest_and_byte_span(self) -> None:
        source = "value = @\n"
        with self.assertRaises(tomllib.TOMLDecodeError) as result:
            tomllib.loads(source)
        error = result.exception
        self.assertEqual(str(error), "Invalid value")
        self.assertEqual(error.byte_span, (8, 9))
        self.assertEqual(len(error.source_sha256), 64)
        self.assertFalse(hasattr(error, "lineno"))
        self.assertFalse(hasattr(error, "colno"))
        self.assertFalse(hasattr(error, "pos"))


if __name__ == "__main__":
    unittest.main()
