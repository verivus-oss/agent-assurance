"""Independent expected values for the reference PostgreSQL bridge."""

import sys
import os
from datetime import date, datetime, timezone
from _decimal import Decimal

from _literal_path import Path
from _literal_json import InvalidJSON
from _test_require import expect_raises, require

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reference/database'))
from _postgres_client import (NativeConnection, OperationalError, ParameterEncodingError, ProgrammingError,
                              array_value, bytea_value, identifier, parameter, result_value, source_identity)  # noqa: E402
from _owned_session import Session  # noqa: E402
from _sql_probes import constraint_failure  # noqa: E402


def test_parameters_preserve_text_bytes_arrays_and_scalars():
    class Text(str):
        def __str__(self):
            raise AssertionError('parameter display override executed')

        def __contains__(self, _value):
            raise AssertionError('parameter containment override executed')

    class List(list):
        def __iter__(self):
            raise AssertionError('sequence subclass iteration executed')

    class Tuple(tuple):
        def __iter__(self):
            raise AssertionError('sequence subclass iteration executed')

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
    for value in (object(), {'unsupported': 7}, {1, 2}, List([7]), Tuple((7,))):
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


def test_malformed_json_reply_abandons_its_actual_owned_child():
    # Exercise the post-handshake reply path with a live framed producer.
    # Native handshake and server behavior have separate producer/lane controls.
    program = ("import os,sys,time; size=int.from_bytes(sys.stdin.buffer.read(4),'big'); "
               "data=sys.stdin.buffer.read(size); value=b'not-json'; "
               "os.write(1,len(value).to_bytes(4,'big')+value); time.sleep(5)")
    session = Session([sys.executable, '-B', '-S', '-c', program])
    descriptors = tuple(session.descriptors)
    connection = NativeConnection.__new__(NativeConnection)
    connection._session, connection._sequence, connection._closed = session, 0, False
    connection._source_root = Path(__file__).resolve().parents[1] / 'tools/dagtoml-postgres-go'
    connection.source_sha256 = source_identity(connection._source_root)[0]
    connection._binary = sys.executable
    metadata = os.stat(sys.executable)
    connection._binary_identity = (metadata.st_dev, metadata.st_ino, metadata.st_size,
                                   metadata.st_mtime_ns, metadata.st_ctime_ns)
    try:
        error = expect_raises(OperationalError, lambda: connection._request({'operation': 'close'}),
                              'malformed JSON reply yielded a successful result')
        require(isinstance(error.__cause__, InvalidJSON), 'malformed JSON control failed during unrelated setup')
        require(connection.closed and session.status is not None and not session.descriptors,
                'malformed JSON reply left its owned producer or descriptors live')
        expect_raises(ChildProcessError, lambda: os.waitpid(session.pid, os.WNOHANG), 'malformed reply child was not reaped')
        for descriptor in descriptors:
            expect_raises(OSError, lambda: os.fstat(descriptor), 'malformed reply retained a descriptor')
    finally:
        session.close()


if __name__ == '__main__':
    controls = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(controls)
    executed = set()
    for name, control in sorted(controls.items()):
        control()
        executed.add(name)
    require(executed == set(controls))
    print('PostgreSQL bridge: independent typed parameter/result answers, malformed input and encoding-witness controls, live framed decoder-failure cleanup; live server, packaging and mutation checks skipped')
