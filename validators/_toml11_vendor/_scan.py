# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Adapted with explicit token scanners for agent-assurance.

"""TOML number, date, and time scanners without pattern matching engines."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone, tzinfo
from functools import lru_cache
from typing import Any

from ._types import ParseFloat


class ScanMatch:
    def __init__(
        self, source: str, start: int, end: int, groups: tuple[str | None, ...] = (),
    ) -> None:
        self.source = source
        self.start = start
        self.stop = end
        self.captures = groups

    def end(self) -> int:
        return self.stop

    def group(self, name: str | None = None) -> str | None:
        if name == "floatpart":
            return self.captures[0]
        if name is not None:
            raise IndexError(name)
        return self.source[self.start:self.stop]

    def groups(self) -> tuple[str | None, ...]:
        return self.captures


def _ascii_digit(char: str) -> bool:
    return "0" <= char <= "9"


def _digits(source: str, pos: int, alphabet: str, underscores: bool = False) -> int:
    while pos < len(source):
        if source[pos] in alphabet:
            pos += 1
        elif underscores and source[pos] == "_" and pos + 1 < len(source) and source[pos + 1] in alphabet:
            pos += 2
        else:
            break
    return pos


def scan_number(source: str, start: int) -> ScanMatch | None:
    pos = start
    if pos >= len(source):
        return None
    if source[pos] == "0" and pos + 1 < len(source):
        alphabets = {
            "x": "0123456789abcdefABCDEF",
            "b": "01",
            "o": "01234567",
        }
        alphabet = alphabets.get(source[pos + 1])
        if alphabet is not None and pos + 2 < len(source) and source[pos + 2] in alphabet:
            end = _digits(source, pos + 3, alphabet, underscores=True)
            return ScanMatch(source, start, end, (None,))

    if source[pos] in "+-":
        pos += 1
    if pos >= len(source) or not _ascii_digit(source[pos]):
        return None
    if source[pos] == "0":
        pos += 1
    else:
        pos = _digits(source, pos + 1, "0123456789", underscores=True)
    integer_end = pos
    if pos + 1 < len(source) and source[pos] == "." and _ascii_digit(source[pos + 1]):
        pos = _digits(source, pos + 2, "0123456789", underscores=True)
    if pos < len(source) and source[pos] in "eE":
        exponent = pos + 1
        if exponent < len(source) and source[exponent] in "+-":
            exponent += 1
        if exponent < len(source) and _ascii_digit(source[exponent]):
            pos = _digits(source, exponent + 1, "0123456789", underscores=True)
    return ScanMatch(source, start, pos, (source[integer_end:pos],))


def _two_digits(source: str, pos: int, limit: int) -> str | None:
    pair = source[pos:pos + 2]
    if len(pair) == 2 and all(_ascii_digit(char) for char in pair) and int(pair) <= limit:
        return pair
    return None


def _scan_time(source: str, start: int) -> tuple[int, tuple[str | None, ...]] | None:
    hour = _two_digits(source, start, 23)
    minute = _two_digits(source, start + 3, 59)
    if hour is None or source[start + 2:start + 3] != ":" or minute is None:
        return None
    pos = start + 5
    second: str | None = None
    fraction: str | None = None
    if source[pos:pos + 1] == ":":
        candidate = _two_digits(source, pos + 1, 59)
        if candidate is not None:
            second = candidate
            pos += 3
            if source[pos:pos + 1] == "." and pos + 1 < len(source) and _ascii_digit(source[pos + 1]):
                end = _digits(source, pos + 1, "0123456789")
                fraction = source[pos + 1:min(end, pos + 7)]
                pos = end
    return pos, (hour, minute, second, fraction)


def scan_localtime(source: str, start: int) -> ScanMatch | None:
    result = _scan_time(source, start)
    if result is None:
        return None
    end, groups = result
    return ScanMatch(source, start, end, groups)


def scan_datetime(source: str, start: int) -> ScanMatch | None:
    year = source[start:start + 4]
    month = source[start + 5:start + 7]
    day = source[start + 8:start + 10]
    if (
        len(year) != 4 or not all(_ascii_digit(char) for char in year)
        or source[start + 4:start + 5] != "-"
        or month is None or _two_digits(source, start + 5, 12) != month or int(month) < 1
        or source[start + 7:start + 8] != "-"
        or day is None or _two_digits(source, start + 8, 31) != day or int(day) < 1
    ):
        return None
    pos = start + 10
    groups: tuple[str | None, ...] = (year, month, day, None, None, None, None, None, None, None, None)
    if source[pos:pos + 1] in ("T", "t", " "):
        time_result = _scan_time(source, pos + 1)
        if time_result is not None:
            pos, time_groups = time_result
            zulu: str | None = None
            sign: str | None = None
            offset_hour: str | None = None
            offset_minute: str | None = None
            if source[pos:pos + 1] in ("Z", "z"):
                zulu = source[pos]
                pos += 1
            elif source[pos:pos + 1] in ("+", "-"):
                oh = _two_digits(source, pos + 1, 23)
                om = _two_digits(source, pos + 4, 59)
                if oh is not None and source[pos + 3:pos + 4] == ":" and om is not None:
                    sign, offset_hour, offset_minute = source[pos], oh, om
                    pos += 6
            groups = (year, month, day, *time_groups, zulu, sign, offset_hour, offset_minute)
    return ScanMatch(source, start, pos, groups)


class Scanner:
    def __init__(self, scan: Any) -> None:
        self.scan = scan

    def match(self, source: str, pos: int) -> ScanMatch | None:
        return self.scan(source, pos)


SCAN_NUMBER = Scanner(scan_number)
SCAN_LOCALTIME = Scanner(scan_localtime)
SCAN_DATETIME = Scanner(scan_datetime)


def match_to_datetime(match: ScanMatch) -> datetime | date:
    (
        year_str, month_str, day_str, hour_str, minute_str, sec_str, micros_str,
        zulu_time, offset_sign_str, offset_hour_str, offset_minute_str,
    ) = match.groups()
    year, month, day = int(year_str), int(month_str), int(day_str)
    if hour_str is None:
        return date(year, month, day)
    sec = int(sec_str) if sec_str else 0
    micros = int(micros_str.ljust(6, "0")) if micros_str else 0
    if offset_sign_str:
        tz: tzinfo | None = cached_tz(offset_hour_str, offset_minute_str, offset_sign_str)
    elif zulu_time:
        tz = timezone.utc
    else:
        tz = None
    return datetime(year, month, day, int(hour_str), int(minute_str), sec, micros, tzinfo=tz)


@lru_cache(maxsize=None)
def cached_tz(hour_str: str, minute_str: str, sign_str: str) -> timezone:
    sign = 1 if sign_str == "+" else -1
    return timezone(timedelta(hours=sign * int(hour_str), minutes=sign * int(minute_str)))


def match_to_localtime(match: ScanMatch) -> time:
    hour_str, minute_str, sec_str, micros_str = match.groups()
    sec = int(sec_str) if sec_str else 0
    micros = int(micros_str.ljust(6, "0")) if micros_str else 0
    return time(int(hour_str), int(minute_str), sec, micros)


def match_to_number(match: ScanMatch, parse_float: ParseFloat) -> Any:
    value = match.group()
    if match.group("floatpart"):
        return parse_float(value)
    return int(value, 0)
