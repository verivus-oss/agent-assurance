"""Accepted and rejected JSON boundaries for the explicit decoder."""
import json
from _test_require import require
from decimal import Decimal
from _literal_json import InvalidJSON, loads

def test_values() -> None:
    require(loads(' \t{"one": [true, null, 1.25, "a\\nb"]}\r\n') == {'one': [True, None, 1.25, 'a\nb']})
    require(loads(b'{"number": 1.20}', parse_float=Decimal) == {'number': Decimal('1.20')})
    require(loads('[[1]]', parse_int=Decimal) == [[Decimal(1)]])

def test_rejections() -> None:
    for value in ('', ' ', '{}x', '[]\xa0', '{"x":}', '[1,]', '1 2'):
        try:
            loads(value)
        except InvalidJSON as exc:
            require(len(exc.source_sha256) == 64)
            require(isinstance(exc.byte_span, tuple) and len(exc.byte_span) == 2)
            require(not hasattr(exc, 'lineno') and not hasattr(exc, 'colno'))
            require(exc.__context__ is None)
            continue
        raise AssertionError('invalid JSON accepted')

def test_scanner_boundary() -> None:
    original_value = json.scanner.make_scanner
    original_string = json.decoder.scanstring
    try:
        json.scanner.make_scanner = json.scanner.py_make_scanner
        try:
            loads('{}')
        except RuntimeError as exc:
            require('regex-free JSON scanner is unavailable' in str(exc))
        else:
            raise AssertionError('Python value scanner was accepted')
    finally:
        json.scanner.make_scanner = original_value
    try:
        json.decoder.scanstring = json.decoder.py_scanstring
        try:
            loads('{}')
        except RuntimeError as exc:
            require('regex-free JSON scanner is unavailable' in str(exc))
        else:
            raise AssertionError('Python string scanner was accepted')
    finally:
        json.decoder.scanstring = original_string
if __name__ == '__main__':
    test_values()
    test_rejections()
    test_scanner_boundary()
    print('literal JSON decoder: accepted and rejected cases passed')
