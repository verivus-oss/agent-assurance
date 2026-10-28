"""Exercise SQLite outcomes and PostgreSQL input rejection before driver loading."""

import sys


if __name__ == '__main__':
    if sys.implementation.name != 'cpython' or not sys.flags.no_site:
        raise RuntimeError('reference-store cold controls require CPython with -S')
    retired = {'re', 'regex', '_sre', 'pathlib', 'fnmatch', 'glob', 'urllib', 'dataclasses', 'json', 'uuid', 'platform', 'typing',
               'psycopg', 'psycopg_binary', 'psycopg_c'}
    observed = set()
    attempted_imports = set()

    def audit(event, arguments):
        if event == 'import' and arguments[0].split('.')[0] in retired:
            attempted_imports.add(arguments[0])
            raise RuntimeError('reference-store cold operation attempted a retired import: ' + arguments[0])

    def profile(frame, event, argument):
        if event == 'c_call' and type(getattr(argument, '__self__', None)).__name__ == 'Pattern':
            if getattr(argument, '__name__', '') in ('match', 'search', 'fullmatch', 'findall', 'finditer', 'split', 'sub', 'subn'):
                observed.add((frame.f_code.co_name, argument.__name__))

    sys.addaudithook(audit)
    sys.setprofile(profile)
    from _literal_path import Path
    from _test_require import expect_raises, require
    import test_random_id

    identifier_controls = {name for name, value in vars(test_random_id).items() if name.startswith('test_') and callable(value)}
    require(identifier_controls, 'random identifier controls are absent')
    executed = set()
    for name in sorted(identifier_controls):
        getattr(test_random_id, name)()
        executed.add(name)
    require(executed == identifier_controls)

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'reference/database'))
    import sqlite3
    from _storage import Store, StorageError, connect
    from _connection_checks import exercise_rejected_postgres_parameters
    from _runtime_document_vocab import KINDS

    exercise_rejected_postgres_parameters('host=127.0.0.1 port=1 dbname=unreachable')
    required = {'adapter-contract', 'adapter-registry-binding', 'gate-decision'}
    require(set(KINDS) == required, 'cold store kind population changed')
    connection = connect('sqlite', ':memory:')
    store = Store('sqlite', connection, root)
    try:
        for name in ('schema', 'seed'):
            connection.executescript((root / ('reference/database/sqlite/' + name + '.sql')).read_text(encoding='utf-8'))
        version = store.execute('SELECT sqlite_version()').fetchone()[0]
        require(version == sqlite3.sqlite_version)
        expect_raises(StorageError, lambda: store.initialize(), 'initialization without ownership passed')
        require(store.initialize(exclusive_unpublished=True)['status'] == 'initialized')
        documents = [('examples/minimal-' + kind + '.toml', (root / ('examples/minimal-' + kind + '.toml')).read_bytes())
                     for kind in sorted(required)]
        require(len(documents) == len(required))
        require(store.ingest(documents)['status'] == 'committed')
        before = store.counts()
        require(before['runtime_document'] == len(required))
        require(store.ingest(documents)['status'] == 'committed' and store.counts() == before)
        expect_raises(ValueError, lambda: store.ingest([]), 'empty ingestion passed')
        expect_raises(ValueError, lambda: store.ingest([('malformed.toml', b'not a TOML document')]), 'malformed captured document passed')
        require(store.counts() == before, 'rejected input changed committed populations')
        expect_raises(sqlite3.OperationalError, lambda: store.execute('SELECT missing_cold_control_column'), 'invalid SQL passed')
        result = store.audit()
        require(result['status'] == 'consistent' and result['checked_documents'] == len(required) and not result['failures'])
    finally:
        connection.close()
    sys.setprofile(None)
    require(not attempted_imports, 'reference store suppressed forbidden import attempts: ' + repr(sorted(attempted_imports)))
    require(not observed and not (retired & set(sys.modules)))
    print('reference store cold control: SQLite initialization, complete supported-kind ingest, idempotency, rejection, SQL error and audit; four NUL and six nontext PostgreSQL parameter rejections executed')
    print('scope: local SQLite ' + version + '; persistent connection-loss/concurrency, accepted PostgreSQL connections, DuckDB, native driver internals and other verification entry points skipped')
