"""Reference boundary controls, with explicit current-artifact execution mode."""

from datetime import date, datetime, time, timedelta, timezone
from _decimal import Decimal
import sys

from _literal_path import Path
from _literal_json import dumps
from _test_require import expect_raises, require
from _duckdb_guard import Boundary, BoundaryError, FORBIDDEN, expected_proof
from _random_id import random_id_hex
from _credential_test_support import TemporaryTree

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
    class List(list):
        def __iter__(self):
            raise AssertionError('identity sequence subclass iteration executed')

    good = [{'path': 'source/input.cpp', 'sha256': 'a' * 64}]
    require(client._roster(good) == good)
    for bad in ([], good * 2, [{'path': '../outside', 'sha256': 'a' * 64}],
                [{'path': 'source/input.cpp', 'sha256': 'g' * 64}],
                [{'path': 'source/input.cpp', 'sha256': 'a' * 64, 'ignored': True}]):
        expect_raises(client.ArtifactError, lambda: client._roster(bad), 'invalid identity roster was accepted')
    require(client.inventory('control-v1', good) != client.inventory('control-v1', [], good))
    require(client.inventory('control-v1', good) != client.inventory('control-v2', good))
    for invalid in ('source', b'source', None, tuple(good), {'source': good}, List(good)):
        error = expect_raises(client.ArtifactError, lambda: client.inventory('control-v1', invalid),
                              'a non-list identity population was accepted')
        require('requires a plain list' in str(error), 'identity population failed during unrelated setup')
    require(client._kernel_path('/private/path\\040with\\134escape') == '/private/path with\\escape')
    require(client._kernel_path('/private/literal\\04x') == '/private/literal\\04x')


def test_artifact_file_readers_refuse_linked_parent_paths():
    with TemporaryTree() as directory:
        root = Path(directory)
        (root / 'actual').mkdir()
        (root / 'actual/member').write_bytes(b'accepted bytes')
        require(client._file(root, 'actual/member') == b'accepted bytes')
        (root / 'alias').symlink_to(root / 'actual', target_is_directory=True)
        (root / 'plain').write_bytes(b'not a directory')
        for relative in ('alias/member', 'plain/member'):
            error = expect_raises(client.ArtifactError, lambda: client._file(root, relative),
                                  'linked or non-directory artifact parent was followed')
            require('linked or non-directory parent' in str(error))
        require(client._recipe(root, 'actual') == [{'path': 'member', 'sha256': client.hashlib.sha256(b'accepted bytes').hexdigest()}])
        error = expect_raises(client.ArtifactError, lambda: client._recipe(root, 'alias'),
                              'linked prepared source root was followed')
        require('not a regular directory' in str(error))


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


def exercise_native_paths(owned):
    """Exercise both supplier consumers of the maintained path conversion."""
    class Text(str):
        def __str__(self):
            raise AssertionError('native path invoked a display override')

    class TextPath:
        def __init__(self, value):
            self.value = value

        def __fspath__(self):
            return self.value

        def __str__(self):
            raise AssertionError('native path invoked a display override')

    directory = ROOT / '.local/database-checks/native-path-controls'
    directory.mkdir(parents=True, exist_ok=True)
    fixture = directory / (random_id_hex() + '.csv')
    fixture.write_bytes(b'value\n7\n')
    accepted, rejected = set(), set()
    try:
        for consumer in ('connect', 'read_csv'):
            destination = ':memory:' if consumer == 'connect' else str(fixture)
            cases = (('text', destination), ('text-subclass', Text(destination)),
                     ('filesystem-protocol', TextPath(Text(destination))))
            for name, value in cases:
                if consumer == 'connect':
                    with owned._module.connect(value) as connection:
                        require(connection.execute('SELECT 7').fetchone() == (7,))
                else:
                    require(owned._connection.read_csv(value).fetchall() == [(7,)])
                accepted.add((consumer, name))
            cases = (('text', destination + '\0ignored'), ('text-subclass', Text(destination + '\0ignored')),
                     ('filesystem-protocol', TextPath(Text(destination + '\0ignored'))))
            for name, value in cases:
                operation = ((lambda: owned._module.connect(value)) if consumer == 'connect'
                             else (lambda: owned._connection.read_csv(value)))
                error = expect_raises(owned._module.InvalidInputException, operation, 'native consumer accepted a NUL path')
                require('NUL bytes' in str(error), 'native NUL path failed during unrelated setup')
                rejected.add((consumer, name))
        expected = {(consumer, name) for consumer in ('connect', 'read_csv')
                    for name in ('text', 'text-subclass', 'filesystem-protocol')}
        require(len(expected) == 6 and accepted == rejected == expected, 'native path consumer population changed')
    finally:
        fixture.unlink()


def exercise_prepared_core_population(proof, directory):
    source = directory / 'core-sources'
    expected = {'NOTICE', 'prepared.cpp', 'static_extensions.cpp'}
    require({path.name for path in source.iterdir()} == expected)
    exercised = set()
    for name in sorted(expected):
        path = source / name
        original = path.read_bytes()
        parked = directory / ('parked-' + name)
        try:
            path.write_bytes(original + b'\nchanged prepared core subject\n')
            error = expect_raises(client.ArtifactError, lambda: client.build_identity(ROOT),
                                  'changed actual core source was accepted')
            require('core prepared source differs' in str(error))
            path.unlink()
            error = expect_raises(client.ArtifactError, lambda: client.build_identity(ROOT),
                                  'missing actual core source was accepted')
            require('core prepared source differs' in str(error))
            parked.write_bytes(original)
            path.symlink_to(parked)
            error = expect_raises(client.ArtifactError, lambda: client.build_identity(ROOT),
                                  'linked actual core source was accepted')
            require('nonregular file' in str(error))
        finally:
            if path.is_symlink():
                path.unlink()
            path.write_bytes(original)
            if parked.exists():
                parked.unlink()
        require(client.build_identity(ROOT) == proof)
        exercised.add(name)
    require(exercised == expected)
    extra = source / 'unexpected-source'
    try:
        extra.write_bytes(b'extra native source')
        error = expect_raises(client.ArtifactError, lambda: client.build_identity(ROOT),
                              'extra actual core source was accepted')
        require('core prepared source differs' in str(error))
    finally:
        extra.unlink()
    require(client.build_identity(ROOT) == proof)


def exercise_native_sql_states(connection):
    cases = (
        ("SELECT 1 /* outer /* nested */ tail */ + 2", (3,)),
        ("SELECT 'a''b'", ("a'b",)),
        ("SELECT 'one'\n 'two'", ('onetwo',)),
        ("SELECT 'one' -- join\n 'two'", ('onetwo',)),
        ("SELECT E'line\\nend'", ('line\nend',)),
        ("SELECT $tag$dollar $ inside$tag$", ('dollar $ inside',)),
        ("SELECT 'ü😀'", ('ü😀',)),
        ('SELECT "ü" FROM (SELECT 7 AS "ü")', (7,)),
        ("SELECT 1_234, 2147483648, .5, 1.2e-3", (1234, 2147483648, Decimal('0.5'), 0.0012)),
        ("SELECT 1 NOT /* gap */ IN (2,3)", (True,)),
        ("SELECT value FROM (VALUES (NULL), (1)) AS rows(value) ORDER BY value NULLS FIRST LIMIT 1", (None,)),
    )
    visited = set()
    for sql, expected in cases:
        require(connection.execute(sql).fetchone() == expected, 'SQL byte state changed its independently expected value')
        visited.add(sql)
    require(visited == {sql for sql, _expected in cases})
    for sql, values in (("SELECT $1", [7]), ("SELECT ?2, ?1", [7, 8])):
        expected = (7,) if len(values) == 1 else (8, 7)
        require(connection.execute(sql, values).fetchone() == expected)
    refused = (
        ('SELECT ""', 'zero length SQL identifier'),
        ("SELECT 'unfinished", 'unterminated SQL quoted value'),
        ('SELECT 1 /* unfinished', 'unterminated SQL block comment'),
        ('SELECT $tag$unfinished', 'unterminated SQL dollar quoted string'),
        ("SELECT E'\\u0041'", 'Unicode escape conversion is unsupported'),
        ("SELECT U&'d\\0061t'", 'Unicode escape conversion is unsupported'),
        ('SELECT $2147483648', 'SQL parameter number exceeds parser bound'),
        ('SELECT 1 ' + '!' * 64 + ' 2', 'SQL operator exceeds parser byte bound'),
        ("SELECT 'one' /* block\n gap */ 'two'", 'syntax error'),
    )
    rejected = set()
    for sql, reason in refused:
        error = expect_raises(connection._module.ParserException, lambda: connection.execute(sql),
                              'invalid or unsupported SQL state was accepted')
        require(reason in str(error), 'SQL state failed outside its declared refusal property')
        rejected.add(sql)
    require(rejected == {sql for sql, _reason in refused})


def exercise_external_extension_refusals(connection):
    loaded = {row[0] for row in connection.execute(
        "SELECT extension_name FROM duckdb_extensions() WHERE loaded").fetchall()}
    require(loaded == {'core_functions', 'json'}, 'required static extension population changed')
    operations = (
        lambda: connection.execute("INSTALL dagtoml_refusal_probe"),
        lambda: connection.execute("LOAD dagtoml_refusal_probe"),
        lambda: connection._connection.install_extension('dagtoml_refusal_probe'),
        lambda: connection._connection.load_extension('dagtoml_refusal_probe'),
    )
    reached = 0
    for operation in operations:
        error = expect_raises(connection._module.PermissionException, operation,
                              'external extension code could restore a retired dependency')
        require('external extensions is disabled through a compile time flag' in str(error),
                'external extension control failed during unrelated setup')
        reached += 1
    require(reached == len(operations))
    require(connection.execute("SELECT '{}'::JSON, 7 + 1").fetchone() == ('{}', 8))


def exercise_retired_matching(connection):
    named_functions = {'regexp_escape', 'regexp_extract', 'regexp_extract_all', 'regexp_full_match',
                       'regexp_matches', 'regexp_replace', 'regexp_split_to_array', 'regexp_split_to_table',
                       'str_split_regex', 'string_split_regex'}
    declared = {row[0] for row in connection.execute(
        "SELECT DISTINCT function_name FROM duckdb_functions() WHERE contains(function_name, 'regex')").fetchall()}
    require(declared == named_functions, 'registered pattern function population changed')
    operations = (
        "SELECT regexp_matches('a', 'a')",
        "SELECT regexp_full_match('a', 'a')",
        "SELECT regexp_replace('abc', 'b', 'X')",
        "SELECT regexp_extract('abc', '(.)', 1)",
        "SELECT regexp_extract_all('abc', '(.)', 1)",
        "SELECT regexp_split_to_array('a,b', ',')",
        "SELECT regexp_split_to_table('a,b', ',')",
        "SELECT str_split_regex('a,b', ',')",
        "SELECT string_split_regex('a,b', ',')",
        "SELECT 'a' ~ 'a'",
        "SELECT 'a' !~ 'b'",
        "SELECT regexp_matches('a', '[')",
        "SELECT regexp_escape('a.b')",
        "SELECT 'a' SIMILAR TO 'a'",
        "SELECT COLUMNS('^a') FROM (SELECT 1 AS a)",
    )
    executed = set()
    for sql in operations:
        error = expect_raises(connection._module.Error, lambda: connection.execute(sql),
                              'retired SQL pattern execution was accepted')
        require('pattern execution is retired' in str(error), 'pattern refusal failed outside its declared property')
        executed.add(sql)
    require(executed == set(operations))
    require(connection.execute("SELECT value FROM (VALUES ('a'), ('b')) AS rows(value) WHERE value = 'a'").fetchall() == [('a',)])


def exercise_primary_native_errors(connection):
    cases = (
        ('SELECT dagtoml_missing_function(1)', connection._module.CatalogException, 'Scalar Function'),
        ('SELECT * FROM dagtoml_missing_table', connection._module.CatalogException, 'Table with name'),
        ('SET python_enable_replacements=true; SELECT * FROM dagtoml_missing_table',
         connection._module.CatalogException, 'Table with name'),
        ('SELECT dagtoml_missing_column FROM (SELECT 1 AS present)', connection._module.BinderException,
         'Referenced column'),
        ("SELECT CAST('not-an-integer' AS INTEGER)", connection._module.ConversionException, 'Could not convert'),
        ("SELECT regexp_matches('a','a')", connection._module.Error, 'pattern execution is retired'),
    )
    reached = set()
    for sql, kind, expected in cases:
        error = expect_raises(kind, lambda: connection.execute(sql), 'native error was accepted')
        require(expected in str(error), 'native error changed its declared primary message')
        require('\nLINE ' not in str(error) and 'SELECT ' not in str(error),
                'native error retained rendered query context')
        require(error.__context__ is None and error.__cause__ is None,
                'native error retained an original exception through its context')
        reached.add(sql)
    require(reached == {sql for sql, _kind, _expected in cases})
    connection.execute('BEGIN')
    require(connection.execute('SELECT 7').fetchone() == (7,), 'structured mode disturbed an accepted transaction')
    connection.execute('COMMIT')
    connection.execute('SET errors_as_json=false')
    for sql in ('SELECT dagtoml_missing_function(1)', 'SELECT * FROM dagtoml_missing_table'):
        error = expect_raises(connection._module.CatalogException, lambda: connection.execute(sql),
                              'unstructured native error was accepted')
        require(str(error) == 'native DuckDB operation failed without a structured primary message',
                'unstructured native error retained query or source context')
        require(error.__context__ is None and error.__cause__ is None,
                'unstructured native error retained its original exception')
    connection.execute('SET errors_as_json=true')
    error = expect_raises(connection._module.CatalogException,
                          lambda: connection.execute('SELECT dagtoml_missing_function(1)'),
                          'restored structured error was accepted')
    require('Scalar Function' in str(error) and '\nLINE ' not in str(error),
            'restored structured primary error is unavailable')
    require(connection.execute('SELECT 7').fetchone() == (7,), 'structured error mode did not recover')


def exercise_native():
    proof = client.build_identity(ROOT)
    directory = (ROOT / proof['binary']).parent
    record_path = directory / 'binding-build.json'
    original = record_path.read_bytes()
    original_record = client.loads(original)
    try:
        for name in ('owned_sources', 'prepared_sources', 'pybind_headers', 'python_headers', 'core_files', 'native_core_sources'):
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
    exercise_prepared_core_population(proof, directory)
    with Boundary() as boundary:
        module = client._module(ROOT, proof)
        for attribute, wrong in (('__file__', str(directory / 'unexpected.so')),
                                 ('__dagtoml_binding_identity__', '0' * 64), ('__version__', 'unsupported')):
            original_value = getattr(module, attribute)
            client._MODULE, client._BOUND = None, None
            setattr(module, attribute, wrong)
            try:
                error = expect_raises(client.ArtifactError, lambda: client._module(ROOT, proof),
                                      'preloaded native module with a changed identity was accepted')
                require('loaded native DuckDB module or core differs' in str(error) and client._MODULE is None,
                        'native module mismatch failed during unrelated setup or was retained')
            finally:
                setattr(module, attribute, original_value)
            require(client._module(ROOT, proof) is module)
        with client.connect(':memory:') as connection:
            require(connection.driver_identity == proof)
            exercise_native_paths(connection)
            exercise_retired_matching(connection)
            exercise_primary_native_errors(connection)
            exercise_external_extension_refusals(connection)
            exercise_native_sql_states(connection)
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
    print('Native DuckDB: exact typed values, canonical UUID and structured primary errors with unstructured refusal, both native path consumers with six accepted and six NUL-rejected cases, six population omissions, complete actual prepared core source/notice tamper refusals, retired matching operations, three actual loaded-module identity mismatches, real closed/missing-artifact cleanup; no boundary attempts; full SQL lane and core/compiler audit skipped')


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
