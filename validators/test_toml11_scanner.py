"""Independent TOML 1.1 examples for the vendored token scanners."""
from _test_require import require
import hashlib
import io
import pathlib
import tempfile
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
    source = 'value = @\n'
    error = rejected(source)
    require(error.byte_span == (8, 9))
    require(error.source_sha256 == hashlib.sha256(source.encode()).hexdigest())
    require(error.source_sha256 in str(error))
    require('bytes 8:9' in str(error))
    require(not hasattr(error, 'lineno'))
    require(not hasattr(error, 'colno'))
    require(not hasattr(error, 'pos'))

def test_original_byte_evidence() -> None:
    for source in (b'a = 1\r\nb = 2\r\nc = @\r\n', 'name = "值"\r\nbad = @\r\n'.encode()):
        try:
            tomllib.load(io.BytesIO(source))
        except tomllib.TOMLDecodeError as error:
            expected = source.index(b'@')
            require(error.byte_span == (expected, expected + 1))
            require(error.source_sha256 == hashlib.sha256(source).hexdigest())
            require(f'bytes {expected}:{expected + 1}' in str(error))
        else:
            raise AssertionError('invalid TOML was accepted')
    require(tomllib.loads('a = 1\r\nb = 2\r\n') == {'a': 1, 'b': 2})

def test_invalid_utf8_uses_original_byte_evidence() -> None:
    source = b'name = "valid\xff"\n'
    try:
        tomllib.load(io.BytesIO(source))
    except tomllib.TOMLDecodeError as error:
        require(error.byte_span == (13, 14))
        require(error.source_sha256 == hashlib.sha256(source).hexdigest())
        require('invalid UTF-8' in str(error))
        require('line' not in str(error) and 'column' not in str(error))
    else:
        raise AssertionError('invalid UTF-8 was accepted')
    from validate_traceability import load_toml
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / 'invalid.toml'
        path.write_bytes(source)
        try:
            load_toml(path)
        except tomllib.TOMLDecodeError as error:
            require(error.byte_span == (13, 14))
        else:
            raise AssertionError('traceability validator accepted invalid UTF-8')

def test_validator_file_reads_preserve_original_bytes() -> None:
    from validate_gate_decision import validate_one
    from validate_closure_root import validate as validate_closure_root

    raw = b'a = 1\r\nb = 2\r\nbad = @\r\n'
    expected = raw.index(b'@')
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / 'gate.toml'
        path.write_bytes(raw)
        gate_errors = validate_one(path, pathlib.Path(directory))
        closure_errors = validate_closure_root(path)
    for errors in (gate_errors, closure_errors):
        require(len(errors) == 1)
        require(hashlib.sha256(raw).hexdigest() in errors[0])
        require(f'bytes {expected}:{expected + 1}' in errors[0])

def test_caller_float_error_is_not_rewritten() -> None:
    caller_error = tomllib.TOMLDecodeError('caller rejected float', '', 0)

    def reject_float(_: str) -> float:
        raise caller_error

    try:
        tomllib.loads('a = 1.5\r\n', parse_float=reject_float)
    except tomllib.TOMLDecodeError as error:
        require(error is caller_error)
        require(error.source_sha256 == hashlib.sha256(b'').hexdigest())
    else:
        raise AssertionError('caller float error was ignored')

if __name__ == '__main__':
    test_skip_chars_boundaries()
    test_numbers_and_times()
    test_invalid_token_boundaries()
    test_error_uses_digest_and_byte_span()
    test_original_byte_evidence()
    test_invalid_utf8_uses_original_byte_evidence()
    test_validator_file_reads_preserve_original_bytes()
    test_caller_float_error_is_not_rewritten()
    print('TOML token scanner: 8 test groups passed')
