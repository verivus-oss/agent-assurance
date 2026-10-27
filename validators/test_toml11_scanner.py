"""Independent TOML 1.1 examples for the vendored token scanners."""
from _test_require import require
from datetime import date, datetime, time, timedelta, timezone
import _toml11 as tomllib
from _toml11_vendor._parser import skip_chars

def rejected(source: str) -> tomllib.TOMLDecodeError:
    try:
        tomllib.loads(source)
    except tomllib.TOMLDecodeError as exc:
        return exc
    raise AssertionError('invalid TOML was accepted')

def test_skip_chars_boundaries() -> None:
    require(skip_chars(' \tkey', 0, frozenset(' \t')) == 2)
    require(skip_chars(' \t', 0, frozenset(' \t')) == 2)
    require(skip_chars('', 0, frozenset(' \t')) == 0)
    require(skip_chars('key', 0, frozenset(' \t')) == 0)
    require(skip_chars('key', 3, frozenset(' \t')) == 3)
    require(skip_chars('key ', -1, frozenset(' \t')) == -1)
    for source, expected in (('', {}), (' \t', {}), ('value = 1 \t', {'value': 1})):
        require(tomllib.loads(source) == expected)
    rejected('value = 1 \tjunk')

def test_numbers_and_times() -> None:
    document = tomllib.loads('hex = 0xF_F\nbinary = 0b1_0\noctal = 0o7_0\ndecimal = -1_000\nfraction = 1_000.25e-2\nday = 2026-10-27\nclock = 12:34\nstamp = 2026-10-27T12:34:56.123456789+10:00\n')
    require(document['hex'] == 255)
    require(document['binary'] == 2)
    require(document['octal'] == 56)
    require(document['decimal'] == -1000)
    require(document['fraction'] == 10.0025)
    require(document['day'] == date(2026, 10, 27))
    require(document['clock'] == time(12, 34))
    require(document['stamp'] == datetime(2026, 10, 27, 12, 34, 56, 123456, tzinfo=timezone(timedelta(hours=10))))

def test_invalid_token_boundaries() -> None:
    for value in ('0x', '1_', '1e+', '24:00', '2026-13-27', '2026-10-27T12:34+24:00'):
        rejected(f'value = {value}\n')

def test_error_uses_digest_and_byte_span() -> None:
    error = rejected('value = @\n')
    require(str(error) == 'Invalid value')
    require(error.byte_span == (8, 9))
    require(len(error.source_sha256) == 64)
    require(not hasattr(error, 'lineno'))
    require(not hasattr(error, 'colno'))
    require(not hasattr(error, 'pos'))
if __name__ == '__main__':
    test_skip_chars_boundaries()
    test_numbers_and_times()
    test_invalid_token_boundaries()
    test_error_uses_digest_and_byte_span()
    print('TOML token scanner: 4 test groups passed')
