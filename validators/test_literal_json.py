"""Independent JSON value, syntax, formatting and native-boundary controls."""

import hashlib
import _json
import sys
from decimal import Decimal
from io import StringIO

from _test_require import expect_raises, require
from _literal_json import InvalidJSON, dump, dumps, loads


def test_values():
    require(loads(' \t{"one": [true, null, 1.25, "a\\nb"]}\r\n') == {'one': [True, None, 1.25, 'a\nb']})
    require(loads(b'{"number": 1.20}', parse_float=Decimal) == {'number': Decimal('1.20')})
    require(loads('[[1]]', parse_int=Decimal) == [[Decimal(1)]])
    for source, expected in (
        ('null', None), ('true', True), ('false', False), ('0', 0), ('-0', 0),
        ('12', 12), ('-12', -12), ('1.25', 1.25), ('-0.25', -0.25),
        ('1e3', 1000.0), ('1E+3', 1000.0), ('1e-3', 0.001),
        ('[]', []), ('{}', {}), ('""', ''), ('{"":0}', {'': 0}),
        ('[[],{},[true,false]]', [[], {}, [True, False]]),
        ('{"a":{},"b":[]}', {'a': {}, 'b': []}), ('{"a":1,"a":2}', {'a': 2}),
        ('"\\u2603"', '☃'), ('"\\ud834\\udd1e"', '𝄞'),
        ('"\\ud800"', chr(0xd800)), ('"é"', 'é'),
        ('"\\\"\\\\\\/\\b\\f\\n\\r\\t"', '"\\/\b\f\n\r\t'),
    ):
        require(loads(source) == expected, 'declared JSON value differed: ' + source)
    require(loads('"control\x00byte"', strict=False) == 'control\x00byte')
    require(loads('Infinity') == float('inf'))
    require(loads('-Infinity') == -float('inf'))
    value = loads('NaN')
    require(value != value)
    require(loads('NaN', parse_constant=lambda value: value) == 'NaN')
    require(loads('{"a":1}', object_hook=lambda value: ('object', value)) == ('object', {'a': 1}))
    called = []
    require(loads('{"a":1,"a":2}', object_pairs_hook=lambda pairs: pairs,
                  object_hook=lambda value: called.append(value)) == [('a', 1), ('a', 2)])
    require(not called, 'object hook ran despite a declared pairs hook')


def test_ascii_escape_and_decimal_alphabets():
    accepted = {'"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f',
                'n': '\n', 'r': '\r', 't': '\t', 'u': chr(0)}
    required = {chr(value) for value in range(128)}
    visited = set()
    for character in sorted(required):
        source = '"\\' + character + ('0000' if character == 'u' else '') + '"'
        if character in accepted:
            require(loads(source) == accepted[character])
        else:
            expect_raises(InvalidJSON, lambda: loads(source), 'unsupported ASCII escape passed')
        visited.add(character)
    require(visited == required)
    for value in range(10):
        require(loads(str(value)) == value)
        require(loads('-' + str(value)) == -value)
    for value in range(16):
        require(loads('"\\u' + format(value, '04x') + '"') == chr(value))


def test_rejections():
    subjects = (
        '', ' ', '{}x', '[]\xa0', '{"x":}', '[1,]', '1 2', '[', '{',
        '{a:1}', '{"a" 1}', '{"a":1,}', '{"a":1 "b":2}', '[1 2]',
        '[,1]', '[1,,2]', '{"a"::1}', '[}', '{]', '+1', '-', '01', '-01',
        '.1', '1.', '1e', '1e+', '1e-', '1E-', '1e.2', '0x1', '١',
        'TRUE', 'False', 'NULL', 'nan', '-NaN', 'Infinityx',
        '"', '"open', '"\\', '"\\x20"', '"\\u12"', '"\\u12xy"',
        '"control\x00byte"', '"control\nbyte"', '"control\x1fbyte"',
    )
    require(subjects and len(set(subjects)) == len(subjects))
    visited = set()
    for source in subjects:
        try:
            loads(source)
        except InvalidJSON as error:
            require(error.source_sha256 == hashlib.sha256(source.encode()).hexdigest())
            start, end = error.byte_span
            require(0 <= start <= end <= len(source.encode()))
            require(not hasattr(error, 'lineno') and not hasattr(error, 'colno'))
            require(error.__context__ is None)
            visited.add(source)
            continue
        raise AssertionError('invalid JSON accepted')
    require(visited == set(subjects))
    expect_raises(TypeError, lambda: loads(None), 'non-text JSON input passed')
    expect_raises(TypeError, lambda: loads('{}', unsupported=True), 'unknown JSON option passed')
    expect_raises(TypeError, lambda: loads('1', parse_int=1), 'non-callable value hook passed')


def test_original_byte_diagnostics():
    source = '"é" x'
    try:
        loads(source)
    except InvalidJSON as error:
        require(error.byte_span == (5, 6))
        require(error.source_sha256 == hashlib.sha256(source.encode()).hexdigest())
    else:
        raise AssertionError('invalid Unicode-adjacent JSON passed')
    source = b'"\xc3"'
    try:
        loads(source)
    except InvalidJSON as error:
        require(error.byte_span == (1, 2))
        require(error.source_sha256 == hashlib.sha256(source).hexdigest())
        require(error.__context__ is None)
    else:
        raise AssertionError('invalid UTF-8 JSON passed')


def test_source_subclass_methods_cannot_split_the_two_readers():
    def forbidden(*_arguments, **_options):
        raise AssertionError('source subclass method was executed')

    class Text(str):
        __str__ = __getitem__ = __len__ = startswith = encode = forbidden

    class Bytes(bytes):
        __bytes__ = __getitem__ = __len__ = decode = forbidden

    require(loads(Text('{"a":1}')) == {'a': 1})
    require(loads(Bytes(b'{"a":1}')) == {'a': 1})
    expect_raises(InvalidJSON, lambda: loads(Text('[1,]')), 'subclass syntax bypassed validation')
    expect_raises(InvalidJSON, lambda: loads(Bytes(b'[1,]')), 'byte subclass syntax bypassed validation')


def test_hook_rejections_and_nested_values():
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result

    def finite(_value):
        raise ValueError('nonfinite JSON')

    require(loads('{"a":1}', object_pairs_hook=unique) == {'a': 1})
    expect_raises(ValueError, lambda: loads('{"a":1,"a":2}', object_pairs_hook=unique), 'duplicate key hook was bypassed')
    expect_raises(ValueError, lambda: loads('[NaN]', parse_constant=finite), 'constant rejection was bypassed')
    depth = 100
    result = loads('[' * depth + '0' + ']' * depth)
    for _ in range(depth):
        require(isinstance(result, list) and len(result) == 1)
        result = result[0]
    require(result == 0)
    expect_raises(RecursionError, lambda: loads('[' * 10000 + '0' + ']' * 10000), 'native depth failure was hidden')


def test_encoder_values_and_formatting():
    require(dumps({'text': '☃'}) == '{"text": "\\u2603"}')
    require(dumps({'text': '☃'}, ensure_ascii=False) == '{"text": "☃"}')
    value = {'b': [True, False], 'a': {}}
    require(dumps(value, sort_keys=True, separators=(',', ':')) == '{"a":{},"b":[true,false]}')
    expected = '{\n  "a": {},\n  "b": [\n    true,\n    false\n  ]\n}'
    require(dumps(value, sort_keys=True, indent=2) == expected)
    require(dumps([[], {}], indent=0) == '[\n[],\n{}\n]')
    require(dumps([[], {}], indent=-2) == '[\n[],\n{}\n]')
    require(dumps([1, 2], indent='\t') == '[\n\t1,\n\t2\n]')
    require(dumps({'a': [1, 2]}, indent=1, separators=(', ', ':')) == '{\n "a":[\n  1, \n  2\n ]\n}')
    text = 'braces {} [] comma , colon : quote " slash \\ end'
    require(loads(dumps([text], indent=2)) == [text])
    require(dumps({None: 1, True: 2, 3: 4}) == '{"null": 1, "true": 2, "3": 4}')
    require(dumps({(1,): 2, 'keep': 1}, skipkeys=True) == '{"keep": 1}')
    require(dumps(object(), default=lambda _: {'a': 1}) == '{"a": 1}')
    require(dumps(float('inf')) == 'Infinity')
    output = StringIO()
    dump(value, output, indent=2, sort_keys=True)
    require(output.getvalue() == expected)
    shared = []
    require(dumps([shared, shared]) == '[[], []]')


def test_encoder_rejections():
    expect_raises(ValueError, lambda: dumps(float('nan'), allow_nan=False), 'nonfinite output was accepted')
    expect_raises(TypeError, lambda: dumps(object()), 'unsupported output value was accepted')
    expect_raises(TypeError, lambda: dumps({(1,): 1}), 'unsupported output key was accepted')
    expect_raises(TypeError, lambda: dumps({}, unsupported=True), 'unknown output option was accepted')
    expect_raises(TypeError, lambda: dumps({}, indent=1.5), 'invalid indent was accepted')
    expect_raises(TypeError, lambda: dumps({}, separators=(',',)), 'incomplete separators were accepted')
    expect_raises(TypeError, lambda: dumps({}, separators=(',', 1)), 'non-text separator was accepted')
    expect_raises(TypeError, lambda: dumps({}, default=1), 'non-callable output hook was accepted')
    value = []
    value.append(value)
    expect_raises(ValueError, lambda: dumps(value), 'circular output was accepted')


def test_native_boundary():
    def unavailable(*_arguments, **_options):
        raise AssertionError('substituted native JSON primitive was executed')

    for name in ('make_scanner', 'make_encoder', 'encode_basestring', 'encode_basestring_ascii'):
        original = getattr(_json, name)
        try:
            setattr(_json, name, unavailable)
            expect_raises(RuntimeError, lambda: loads('{}'), 'substituted decoder primitive was accepted')
            expect_raises(RuntimeError, lambda: dumps({}), 'substituted encoder primitive was accepted')
        finally:
            setattr(_json, name, original)
    require(loads('{}') == {} and dumps({}) == '{}')
    original = sys.implementation
    try:
        sys.implementation = type('UnsupportedImplementation', (), {'name': 'unsupported'})()
        expect_raises(RuntimeError, lambda: loads('{}'), 'unsupported interpreter was accepted')
        expect_raises(RuntimeError, lambda: dumps({}), 'unsupported encoder interpreter was accepted')
    finally:
        sys.implementation = original


if __name__ == '__main__':
    tests = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(tests)
    executed = set()
    for name, test in sorted(tests.items()):
        test()
        executed.add(name)
    require(executed == set(tests))
    print('literal JSON codec: complete declared value, syntax, formatting and native-boundary controls executed')
