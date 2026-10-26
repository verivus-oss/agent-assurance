#!/usr/bin/env python3
"""Independent TOML 1.1 examples for the vendored token scanners."""

import unittest
from datetime import date, datetime, time, timedelta, timezone

import _toml11 as tomllib


class ParserTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
