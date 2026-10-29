"""Independent expected values for the reference PostgreSQL bridge."""

import sys
from datetime import date, datetime, timezone
from _decimal import Decimal

from _literal_path import Path
from _test_require import expect_raises, require

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reference/database'))
from _postgres_client import (ParameterEncodingError, ProgrammingError, array_value, bytea_value,
                              identifier, parameter, result_value)  # noqa: E402
from _sql_probes import constraint_failure  # noqa: E402


def test_parameters_preserve_text_bytes_arrays_and_scalars():
    class Text(str):
        def __str__(self):
            raise AssertionError('parameter display override executed')

        def __contains__(self, _value):
            raise AssertionError('parameter containment override executed')

    cases = ((None, None), (True, 'true'), (False, 'false'), (7, '7'), (1.25, '1.25'),
             (Decimal('1.25'), '1.25'), (b'\0\xff', '\\x00ff'),
             (Text('Unicode ü, quote ", slash \\, SQL $1 ? %s'), 'Unicode ü, quote ", slash \\, SQL $1 ? %s'),
             (date(2026, 10, 29), '2026-10-29'),
             (datetime(2026, 10, 29, tzinfo=timezone.utc), '2026-10-29T00:00:00+00:00'),
             (['NULL', None, 'a,b', 'q"', '\\'], '{"NULL",NULL,"a,b","q\\"","\\\\"}'),
             ([[1, 2], [3, 4]], '{{"1","2"},{"3","4"}}'))
    for value, expected in cases:
        require(parameter(value) == expected, 'PostgreSQL parameter changed its independent expected representation')
    for value in ('nul\0text', Text('nul\0text'), ['nul\0text']):
        error = expect_raises(ParameterEncodingError, lambda: parameter(value), 'NUL text was accepted')
        require(error.sqlstate is None and constraint_failure('postgres', error, 'encoding'))
        require(not constraint_failure('postgres', error, 'value'))
    for value in (object(), {'unsupported': 7}, {1, 2}):
        expect_raises(TypeError, lambda: parameter(value), 'unsupported parameter was accepted')
    require(identifier('quoted"name') == '"quoted""name"')
    expect_raises(TypeError, lambda: identifier('nul\0name'), 'NUL identifier was accepted')


def test_results_preserve_native_reference_types():
    cases = ((16, 't', True), (16, 'f', False), (23, '7', 7), (20, '9223372036854775807', 9223372036854775807),
             (701, '1.25', 1.25), (1700, '1.2500', Decimal('1.2500')),
             (3802, '{"value":7}', {'value': 7}), (17, '\\x00ff', b'\0\xff'),
             (1082, '2026-10-29', date(2026, 10, 29)),
             (1184, '2026-10-29 00:00:00+00', datetime(2026, 10, 29, tzinfo=timezone.utc)),
             (1009, '{"NULL",NULL,"a,b","q\\"","\\\\"}', ['NULL', None, 'a,b', 'q"', '\\']),
             (1007, '{{1,2},{3,4}}', [[1, 2], [3, 4]]), (1009, '{}', []), (25, None, None))
    for oid, value, expected in cases:
        require(result_value(oid, value) == expected, 'PostgreSQL native result changed its expected reference type')
    require(bytea_value('plain\\000\\377\\\\') == b'plain\0\xff\\')
    for value in ('\\xgg', '\\12', '\\777', '\\q'):
        expect_raises(ProgrammingError, lambda: bytea_value(value), 'invalid bytea text was accepted')
    for value in ('', '{', '{"unclosed}', '{one}tail', '{one;two}', '{one,'):
        if value == '{one;two}':
            require(array_value(value, str) == ['one;two'])
        else:
            expect_raises(ProgrammingError, lambda: array_value(value, str), 'malformed array was accepted')
    expect_raises(ProgrammingError, lambda: result_value(16, 'invalid'), 'invalid boolean text was accepted')


def test_only_typed_encoding_refusals_count_as_driver_witnesses():
    class DataError(Exception):
        pass

    require(not constraint_failure('postgres', DataError('cannot contain NUL'), 'encoding'),
            'an exception name/message was mistaken for the current driver refusal')
    require(not constraint_failure('postgres', RuntimeError('infrastructure failed'), 'encoding'),
            'setup failure was mistaken for a constraint rejection')


if __name__ == '__main__':
    controls = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(controls)
    executed = set()
    for name, control in sorted(controls.items()):
        control()
        executed.add(name)
    require(executed == set(controls))
    print('PostgreSQL bridge: independent typed parameter/result answers, malformed input and encoding-witness controls; live server, packaging and mutation checks skipped')
