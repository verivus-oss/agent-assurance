"""Executed connection preconditions, using only private test destinations."""

import uuid

from _storage import Store, StorageError

CHECKS = {"sqlite": {"foreign-keys-enabled-and-read-back", "disabled-checks-refused"},
          "postgres": {"non-utf8-client-refused", "non-utf8-server-refused", "aborted-caller-transaction-preserved"},
          "duckdb": {"idle-connection-precondition"}}


def exercise_connection(store, destination):
    checks = []

    def refused(candidate, code):
        try:
            candidate.prepare()
        except StorageError as exc:
            if exc.code != code:
                raise AssertionError("connection failed for an unrelated reason: " + str(exc)) from exc
        else:
            raise AssertionError("invalid connection precondition was accepted")

    if store.engine == "sqlite":
        store.execute("PRAGMA foreign_keys = OFF")
        store.prepare()
        if store.execute("PRAGMA foreign_keys").fetchone() != (1,):
            raise AssertionError("SQLite foreign-key preparation did not take effect")
        checks.append("foreign-keys-enabled-and-read-back")
        store.execute("PRAGMA ignore_check_constraints = ON")
        try:
            refused(store, "setup")
        finally:
            store.execute("PRAGMA ignore_check_constraints = OFF")
        checks.append("disabled-checks-refused")
    elif store.engine == "postgres":
        import psycopg
        from psycopg.pq import TransactionStatus
        store.execute("SET client_encoding = 'SQL_ASCII'")
        try:
            refused(store, "setup")
        finally:
            store.execute("SET client_encoding = 'UTF8'")
        checks.append("non-utf8-client-refused")
        # The runner owns a private server. A distinct encoding needs a
        # distinct database, not a mocked SHOW response.
        name = "dagtoml_encoding_" + uuid.uuid4().hex
        store.connection.execute(psycopg.sql.SQL("CREATE DATABASE {} ENCODING 'SQL_ASCII' TEMPLATE template0").format(psycopg.sql.Identifier(name)))
        try:
            connection = psycopg.connect(destination, dbname=name, autocommit=True)
            try:
                refused(Store("postgres", connection, store.root), "setup")
            finally:
                connection.close()
        finally:
            store.connection.execute(psycopg.sql.SQL("DROP DATABASE {}").format(psycopg.sql.Identifier(name)))
        checks.append("non-utf8-server-refused")
        store.execute("BEGIN")
        try:
            try:
                store.execute("SELECT 1 / 0")
            except psycopg.errors.DivisionByZero:
                pass
            if store.connection.info.transaction_status != TransactionStatus.INERROR:
                raise AssertionError("aborted-transaction positive setup did not run")
            refused(store, "active-caller-transaction")
            if store.connection.info.transaction_status != TransactionStatus.INERROR:
                raise AssertionError("helper changed the caller's aborted transaction")
        finally:
            store.execute("ROLLBACK")
        checks.append("aborted-caller-transaction-preserved")
    else:
        store.prepare()
        checks.append("idle-connection-precondition")
    if len(checks) != len(CHECKS[store.engine]) or set(checks) != CHECKS[store.engine]:
        raise AssertionError("connection precondition population changed")
    if any(store.counts()[name] for name in ("instance_file", "runtime_document", "reference_contract")):
        raise AssertionError("connection setup controls wrote document or initialization rows")
    return checks
