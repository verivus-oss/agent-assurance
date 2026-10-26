"""Accepted and rejected JSON boundaries for the explicit decoder."""
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
if __name__ == '__main__':
    test_values()
    test_rejections()
    print('literal JSON decoder: accepted and rejected cases passed')
