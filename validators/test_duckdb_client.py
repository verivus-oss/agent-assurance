"""Reference boundary controls, with explicit current-artifact execution mode."""

from datetime import date, datetime, time, timedelta, timezone
from _decimal import Decimal
import sys

from _literal_path import Path
from _literal_json import dumps
from _test_require import expect_raises, require
from _duckdb_guard import Boundary, BoundaryError, FORBIDDEN, expected_proof

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reference/database'))
import _duckdb_client as client  # noqa: E402


def test_parameters_have_independent_expected_values():
    class Text(str):
        def __str__(self):
            raise AssertionError('parameter display override executed')

    class List(list):
        def __iter__(self):
            raise AssertionError('sequence subclass iteration executed')

    class Tuple(tuple):
        def __iter__(self):
            raise AssertionError('sequence subclass iteration executed')

    cases = ((None, None), (True, True), (7, 7), (1.25, 1.25), (Decimal('1.250'), Decimal('1.250')),
             (Text('text\0ü'), 'text\0ü'), (bytearray(b'\0\xff'), b'\0\xff'),
             (memoryview(b'bytes'), b'bytes'), ((7, Text('value')), [7, 'value']),
             ({Text('key'): (7, None)}, {'key': [7, None]}),
             (date(2026, 10, 29), date(2026, 10, 29)),
             (datetime(2026, 10, 29, tzinfo=timezone.utc), datetime(2026, 10, 29, tzinfo=timezone.utc)),
             (time(12, 34, 56), time(12, 34, 56)), (timedelta(days=2), timedelta(days=2)))
    for value, expected in cases:
        actual = client.parameter(value)
        require(actual == expected and type(actual) is type(expected), 'parameter changed its independent value/type')
    for value in (object(), {1: 'nontext'}, {1, 2}, List([7]), Tuple((7,))):
        expect_raises(TypeError, lambda: client.parameter(value), 'unsupported parameter was accepted')
    expect_raises(TypeError, lambda: client.native_connection(object()), 'unbound connection was accepted')


def test_inventory_refuses_ambiguous_rosters_and_binds_populations():
    good = [{'path': 'source/input.cpp', 'sha256': 'a' * 64}]
    require(client._roster(good) == good)
    for bad in ([], good * 2, [{'path': '../outside', 'sha256': 'a' * 64}],
                [{'path': 'source/input.cpp', 'sha256': 'g' * 64}],
                [{'path': 'source/input.cpp', 'sha256': 'a' * 64, 'ignored': True}]):
        expect_raises(client.ArtifactError, lambda: client._roster(bad), 'invalid identity roster was accepted')
    require(client.inventory('control-v1', good) != client.inventory('control-v1', [], good))
    require(client.inventory('control-v1', good) != client.inventory('control-v2', good))
    require(client._kernel_path('/private/path\\040with\\134escape') == '/private/path with\\escape')
    require(client._kernel_path('/private/literal\\04x') == '/private/literal\\04x')


def test_advisory_origins_cover_each_declared_native_input():
    spec = client.loads((ROOT / 'tools/dagtoml-duckdb-native-go/data/inputs.json').read_bytes())
    import _toml11 as toml
    lock = toml.loads_bytes((ROOT / 'reference/database/engine-lock.toml').read_bytes())
    lanes = [lane for lane in lock['lanes'] if lane['engine'] == 'duckdb']
    require(len(lanes) == len(spec['versions']) == 2 and {lane['version'] for lane in lanes} == set(spec['versions']))
    for lane in lanes:
        require(lane.get('driver_module') == 'tools/dagtoml-duckdb-native-go/go.mod')
        version = lane['version']
        suffix = '-floor' if lane['id'] == 'duckdb-floor' else ''
        path = ROOT / ('requirements/database' + suffix + '.txt')
        lines = [line for line in path.read_text().splitlines() if line and not line.startswith('#')]
        require(lines == ['duckdb==' + version + ' \\', '    --hash=sha256:' + spec['versions'][version]['sdk_sha256'],
                          'pybind11==' + spec['pybind']['version'] + ' \\', '    --hash=sha256:' + spec['pybind']['sha256']],
                'native supplier origins lost advisory matching or differ from their pinned build inputs')


def test_guard_refuses_swallowed_ecosystem_imports():
    require({'duckdb', 'pytz', 'pandas', 'numpy'} <= FORBIDDEN)
    for name in ('duckdb', 'pytz', 'pandas', 'numpy'):
        with Boundary() as boundary:
            error = expect_raises(BoundaryError, lambda: __import__(name), 'retired ecosystem import was admitted')
            require('forbidden import' in str(error) and boundary.attempted == {name})
            expect_raises(BoundaryError, boundary.proof, 'swallowed import attempt produced a successful guard')
    with Boundary() as boundary:
        require(boundary.proof() == expected_proof())


def exercise_native():
    proof = client.build_identity(ROOT)
    directory = (ROOT / proof['binary']).parent
    record_path = directory / 'binding-build.json'
    original = record_path.read_bytes()
    original_record = client.loads(original)
    try:
        for name in ('owned_sources', 'prepared_sources', 'pybind_headers', 'python_headers', 'core_files'):
            changed = dict(original_record)
            changed[name] = changed[name][1:]
            record_path.write_text(dumps(changed))
            error = expect_raises(client.ArtifactError, lambda: client.build_identity(ROOT),
                                  'an incomplete prepared population was accepted')
            require(any(text in str(error) for text in ('absent', 'differs', 'incomplete')),
                    'inventory omission failed for an unrelated reason')
    finally:
        record_path.write_bytes(original)
    require(client.build_identity(ROOT) == proof)
    with Boundary() as boundary:
        with client.connect(':memory:') as connection:
            require(connection.driver_identity == proof)
            values = ([7, 8], {'name': 'value'}, date(2026, 10, 29), Decimal('1.250'),
                      datetime(2026, 10, 29, 12, 34, 56, tzinfo=timezone.utc), b'\0\xff', 'text\0ü')
            require(connection.execute('SELECT ?,?,?,?,?,?,?', values).fetchone() == values,
                    'actual native values differ from independently supplied expected values')
            require(connection.execute("SELECT CAST('00112233-4455-6677-8899-aabbccddeeff' AS UUID)").fetchone()
                    == ('00112233-4455-6677-8899-aabbccddeeff',), 'native UUID result is not canonical text')
            error = expect_raises(connection._module.ParserException,
                                  lambda: connection.execute('SELECT FROM'), 'invalid SQL was accepted')
            require('syntax error' in str(error) and '\n' not in str(error), 'primary native error retained rendered context')
            expect_raises(TypeError, lambda: connection.execute('SELECT ?', [object()]), 'unsupported object reached native code')
        require(connection.closed)
        expect_raises(client.ArtifactError, lambda: connection.execute('SELECT 7'), 'closed native connection was reused')
        # Delete the bound executable while a real connection owns the native handle.
        # Restore the exact inode so already loaded handles remain independently checkable.
        with client.connect(':memory:') as active:
            binary = ROOT / proof['binary']
            parked = directory / '_duckdb.parked'
            binary.rename(parked)
            try:
                expect_raises(OSError, lambda: active.execute('SELECT 7'), 'missing artifact was ignored')
                require(active.closed, 'artifact-check failure leaked the actual native connection')
            finally:
                parked.rename(binary)
        require(boundary.proof() == expected_proof())
    require(client.build_identity(ROOT) == proof)
    print('Native DuckDB: exact typed values, canonical UUID and primary errors, five population omissions, real closed/missing-artifact cleanup; no boundary attempts; full SQL lane and core/compiler audit skipped')


if __name__ == '__main__':
    if not sys.flags.no_site:
        from _posix_process import run
        code, output, errors = run([sys.executable, '-B', *(['-O'] if sys.flags.optimize else []), '-S',
                                    str(Path(__file__).resolve()), *sys.argv[1:]])
        require(code == 0 and not errors, 'isolated DuckDB controls failed: ' + errors.decode())
        print(output.decode(), end='')
        raise SystemExit(0)
    require(sys.argv[1:] in ([], ['--native']), 'unsupported DuckDB control selection')
    controls = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(controls)
    executed = set()
    for name, control in sorted(controls.items()):
        control()
        executed.add(name)
    require(executed == set(controls))
    if sys.argv[1:]:
        exercise_native()
    else:
        print('DuckDB boundary: independent typed parameters, connection admission, identity framing/rosters, complete declared advisory origins and four swallowed-import controls; native artifacts, live lanes and core/compiler audit skipped')
