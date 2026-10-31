"""Current PostgreSQL connection controls against a private native session."""

from _random_id import random_id_hex
from _postgres import (DivisionByZero, OperationalError, PROTOCOL, TransactionStatus, identifier)
from _storage import Store, StorageError, connect_postgres


def exercise_postgres(store, destination, refused, reject_parameters, connection_text):
    checks = []
    if store.connection.reference_protocol != PROTOCOL or any(
            len(value) != 64 or any(character not in '0123456789abcdef' for character in value)
            for value in (store.connection.source_sha256, store.connection.dependencies_sha256,
                          store.connection.binary_sha256)):
        raise AssertionError('PostgreSQL connection lacks its current native build identity')
    reject_parameters(destination)
    checks.append('invalid-connection-parameters-refused')
    database = store.execute('SELECT current_database()').fetchone()[0]
    with connect_postgres(connection_text(destination), dbname=connection_text(database)) as fresh:
        if fresh.execute('SELECT current_database(), 7').fetchone() != (database, 7):
            raise AssertionError('text connection parameters changed their native values')
    checks.append('text-connection-parameters')
    with connect_postgres(destination) as fresh:
        if fresh.execute('SELECT 7').fetchone() != (7,):
            raise AssertionError('native PostgreSQL connection changed its result')
        backend = fresh.execute('SELECT pg_backend_pid()').fetchone()[0]
        if store.execute('SELECT pg_terminate_backend(?::integer)', (backend,)).fetchone() != (True,):
            raise AssertionError('private connection-loss control did not terminate its backend')
        try:
            fresh.execute('SELECT 7')
        except OperationalError:
            if not fresh.closed:
                raise AssertionError('connection-loss control did not close its terminated session')
        else:
            raise AssertionError('terminated PostgreSQL connection was accepted')
    for _ in range(8):
        if store.execute('SELECT 7').fetchone() != (7,):
            raise AssertionError('repeated PostgreSQL query changed its result')
    if store.execute('SELECT ?::integer + ?::integer', (3, 4)).fetchone() != (7,):
        raise AssertionError('native PostgreSQL parameters changed their result')
    value = "Unicode ü, quote ', slash \\, and SQL ? %s $1"
    if store.execute('SELECT ?::text', (value,)).fetchone() != (value,):
        raise AssertionError('document-authored PostgreSQL value was not preserved')
    if store.execute('SELECT ?::jsonb', ('{"value": 7}',)).fetchone() != ({'value': 7},):
        raise AssertionError('PostgreSQL JSON adaptation changed its result')
    rows = store.execute('SELECT generate_series(1, 3)')
    if rows.fetchone() != (1,) or rows.fetchall() != [(2,), (3,)] or rows.fetchone() is not None:
        raise AssertionError('buffered PostgreSQL row consumption changed')
    try:
        store.execute('SELECT 1 / 0')
    except DivisionByZero as exc:
        if exc.sqlstate != '22012' or set(vars(exc)) != {'sqlstate'} or 'LINE ' in str(exc):
            raise AssertionError('PostgreSQL error lost its SQLSTATE or retained source coordinates') from exc
    else:
        raise AssertionError('invalid PostgreSQL arithmetic was accepted')
    try:
        missing = connect_postgres(destination, dbname='dagtoml_missing_' + random_id_hex())
    except OperationalError:
        if store.execute('SELECT 7').fetchone() != (7,):
            raise AssertionError('failed connection damaged the active connection')
    else:
        missing.close()
        raise AssertionError('missing PostgreSQL database was accepted')
    for query, parameters in (('SELECT ?::integer', ()), ('SELECT 7', (7,))):
        try:
            store.execute(query, parameters)
        except StorageError as exc:
            if exc.code != 'sql-parameters':
                raise AssertionError('marker mismatch failed for an unrelated reason') from exc
        else:
            raise AssertionError('PostgreSQL marker mismatch was accepted')
    checks.append('native-execution-without-driver-text-matchers')
    store.execute("SET client_encoding = 'SQL_ASCII'")
    try:
        refused(store, 'setup')
    finally:
        store.execute("SET client_encoding = 'UTF8'")
    checks.append('non-utf8-client-refused')
    name = 'dagtoml_encoding_' + random_id_hex() + "'\\ space"
    store.connection.execute('CREATE DATABASE ' + identifier(name) + " ENCODING 'SQL_ASCII' TEMPLATE template0")
    try:
        with connect_postgres(destination, dbname=name) as connection:
            refused(Store('postgres', connection, store.root), 'setup')
    finally:
        store.connection.execute('DROP DATABASE ' + identifier(name))
    checks.append('non-utf8-server-refused')
    store.execute('BEGIN')
    try:
        try:
            store.execute('SELECT 1 / 0')
        except DivisionByZero:
            if store.connection.info.transaction_status != TransactionStatus.INERROR:
                raise AssertionError('SQL failure did not abort the caller transaction')
        else:
            raise AssertionError('division-by-zero control unexpectedly succeeded')
        refused(store, 'active-caller-transaction')
        if store.connection.info.transaction_status != TransactionStatus.INERROR:
            raise AssertionError('helper changed the caller aborted transaction')
    finally:
        store.execute('ROLLBACK')
    checks.append('aborted-caller-transaction-preserved')
    return checks
