"""Executed connection preconditions, using only private test destinations."""

from _random_id import random_id_hex

from _storage import Store, StorageError, connect, connect_postgres

CHECKS = {"sqlite": {"foreign-keys-enabled-and-read-back", "disabled-checks-refused"},
          "postgres": {"native-execution-without-driver-text-matchers", "non-utf8-client-refused",
                       "non-utf8-server-refused", "aborted-caller-transaction-preserved"},
          "duckdb": {"idle-connection-precondition", "text-path-destinations",
                     "nul-text-destinations-refused", "nontext-destinations-refused"}}


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
        from psycopg._queries import PostgresQuery
        from psycopg.pq import TransactionStatus
        from _postgres import require_compiled_adapters
        if store.connection.cursor_factory is not psycopg.RawCursor:
            raise AssertionError("PostgreSQL store did not select the raw cursor")
        if store.connection.prepare_threshold is not None:
            raise AssertionError("PostgreSQL statement preparation was not disabled")
        previous_implementation = psycopg.pq.__impl__
        psycopg.pq.__impl__ = "python"
        try:
            try:
                require_compiled_adapters()
            except RuntimeError as exc:
                if "requires compiled psycopg adapters" not in str(exc):
                    raise AssertionError("adapter guard failed for an unrelated reason") from exc
            else:
                raise AssertionError("pure Python PostgreSQL adapters were accepted")
        finally:
            psycopg.pq.__impl__ = previous_implementation
        import _postgres as native_postgres
        previous_transformer = native_postgres.Transformer
        class PythonTransformer:
            """An unsupported adapter implementation for the guard control."""
        native_postgres.Transformer = PythonTransformer
        try:
            try:
                require_compiled_adapters()
            except RuntimeError as exc:
                if "requires compiled psycopg adapters" not in str(exc):
                    raise AssertionError("transformer guard failed for an unrelated reason") from exc
            else:
                raise AssertionError("pure Python PostgreSQL transformer was accepted")
        finally:
            native_postgres.Transformer = previous_transformer
        old_convert = PostgresQuery.convert
        old_escape = psycopg.conninfo._param_escape
        from psycopg.pq import misc
        old_severity = misc.strip_severity

        def forbidden_placeholder_conversion(*_args, **_kwargs):
            raise AssertionError("PostgreSQL standard placeholder parser was reached")

        PostgresQuery.convert = forbidden_placeholder_conversion
        psycopg.conninfo._param_escape = forbidden_placeholder_conversion
        misc.strip_severity = forbidden_placeholder_conversion
        try:
            for bad_destination, bad_name in ((destination + "\0ignored", None), (destination, "bad\0name")):
                try:
                    unexpected = connect_postgres(bad_destination, dbname=bad_name)
                except psycopg.ProgrammingError as exc:
                    if "NUL bytes" not in str(exc):
                        raise AssertionError("invalid connection failed for an unrelated reason") from exc
                else:
                    unexpected.close()
                    raise AssertionError("NUL connection parameter was truncated instead of rejected")
            with connect_postgres(destination) as fresh:
                if fresh.execute("SELECT 7").fetchone() != (7,):
                    raise AssertionError("native PostgreSQL connection changed its result")
                backend = fresh.execute("SELECT pg_backend_pid()").fetchone()[0]
                if store.execute("SELECT pg_terminate_backend(?::integer)", (backend,)).fetchone() != (True,):
                    raise AssertionError("private connection-loss control did not terminate its backend")
                try:
                    fresh.execute("SELECT 7")
                except psycopg.OperationalError:
                    # The command failed on the deliberately terminated backend.
                    if not fresh.closed and fresh.pgconn.status != psycopg.pq.ConnStatus.BAD:
                        raise AssertionError("connection-loss control failed for an unrelated reason")
                else:
                    raise AssertionError("terminated PostgreSQL connection was accepted")
            # Cross the driver's default automatic-preparation threshold.
            for _ in range(8):
                if store.execute("SELECT 7").fetchone() != (7,):
                    raise AssertionError("fixed PostgreSQL query changed its result")
            if store.execute("SELECT ?::integer + ?::integer", (3, 4)).fetchone() != (7,):
                raise AssertionError("native PostgreSQL parameters changed their result")
            value = "Unicode ü, quote ', slash \\, and SQL ? %s $1"
            if store.execute("SELECT ?::text", (value,)).fetchone() != (value,):
                raise AssertionError("document-authored PostgreSQL value was not preserved")
            if store.execute("SELECT ?::jsonb", ('{"value": 7}',)).fetchone() != ({"value": 7},):
                raise AssertionError("PostgreSQL JSON adaptation changed its result")
            rows = store.execute("SELECT generate_series(1, 3)")
            if rows.fetchone() != (1,) or rows.fetchall() != [(2,), (3,)] or rows.fetchone() is not None:
                raise AssertionError("buffered PostgreSQL row consumption changed")
            try:
                store.execute("SELECT 1 / 0")
            except psycopg.errors.DivisionByZero as exc:
                if exc.sqlstate != "22012" or exc.diag.statement_position is not None or "LINE " in str(exc):
                    raise AssertionError("PostgreSQL error lost its SQLSTATE or exposed source coordinates") from exc
            else:
                raise AssertionError("invalid PostgreSQL arithmetic was accepted")
            try:
                missing = connect_postgres(destination, dbname="dagtoml_missing_" + random_id_hex())
            except psycopg.OperationalError:
                # This private database name was never created.
                if store.execute("SELECT 7").fetchone() != (7,):
                    raise AssertionError("failed connection damaged the active connection")
            else:
                missing.close()
                raise AssertionError("missing PostgreSQL database was accepted")
        finally:
            PostgresQuery.convert = old_convert
            psycopg.conninfo._param_escape = old_escape
            misc.strip_severity = old_severity
        for query, parameters in (("SELECT ?::integer", ()), ("SELECT 7", (7,))):
            try:
                store.execute(query, parameters)
            except StorageError as exc:
                if exc.code != "sql-parameters":
                    raise AssertionError("marker mismatch failed for an unrelated reason") from exc
            else:
                raise AssertionError("PostgreSQL marker mismatch was accepted")
        checks.append("native-execution-without-driver-text-matchers")
        store.execute("SET client_encoding = 'SQL_ASCII'")
        try:
            refused(store, "setup")
        finally:
            store.execute("SET client_encoding = 'UTF8'")
        checks.append("non-utf8-client-refused")
        # The runner owns a private server. A distinct encoding needs a
        # distinct database, not a mocked SHOW response.
        name = "dagtoml_encoding_" + random_id_hex() + "'\\ space"
        store.connection.execute(psycopg.sql.SQL("CREATE DATABASE {} ENCODING 'SQL_ASCII' TEMPLATE template0").format(psycopg.sql.Identifier(name)))
        try:
            connection = connect_postgres(destination, dbname=name)
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
                # The deliberate SQL failure leaves the caller transaction
                # aborted; the assertions below verify it remains untouched.
                if store.connection.info.transaction_status != TransactionStatus.INERROR:
                    raise AssertionError("SQL failure did not abort the caller transaction")
            else:
                raise AssertionError("division-by-zero control unexpectedly succeeded")
            refused(store, "active-caller-transaction")
            if store.connection.info.transaction_status != TransactionStatus.INERROR:
                raise AssertionError("helper changed the caller's aborted transaction")
        finally:
            store.execute("ROLLBACK")
        checks.append("aborted-caller-transaction-preserved")
    else:
        class Text(str):
            def __str__(self):
                raise AssertionError("destination string override was executed")

            def __contains__(self, _value):
                raise AssertionError("destination containment override was executed")

        class TextPath:
            def __init__(self, value):
                self.value = value

            def __fspath__(self):
                return self.value

            def __str__(self):
                raise AssertionError("destination display conversion was executed")

        accepted = []
        for name, value in (("text", destination), ("text-subclass", Text(destination)),
                            ("filesystem-protocol", TextPath(Text(destination)))):
            connection = connect("duckdb", value)
            try:
                if connection.execute("SELECT 7").fetchone() != (7,):
                    raise AssertionError("accepted destination changed the connected query result")
            finally:
                connection.close()
            accepted.append(name)
        if len(accepted) != 3 or set(accepted) != {"text", "text-subclass", "filesystem-protocol"}:
            raise AssertionError("accepted text destination population changed")
        checks.append("text-path-destinations")
        rejected = []
        for name, value in (("text", destination + "\0ignored"),
                            ("text-subclass", Text(destination + "\0ignored")),
                            ("filesystem-protocol", TextPath(Text(destination + "\0ignored")))):
            try:
                unexpected = connect("duckdb", value)
            except StorageError as exc:
                if exc.code != "setup" or "NUL bytes" not in str(exc):
                    raise AssertionError("NUL destination failed for an unrelated reason") from exc
            else:
                unexpected.close()
                raise AssertionError("NUL destination was accepted or truncated")
            rejected.append(name)
        if len(rejected) != 3 or set(rejected) != {"text", "text-subclass", "filesystem-protocol"}:
            raise AssertionError("rejected NUL destination population changed")
        checks.append("nul-text-destinations-refused")
        rejected = []
        for name, value in (("bytes", destination.encode("utf-8")),
                            ("protocol-bytes", TextPath(destination.encode("utf-8"))),
                            ("protocol-integer", TextPath(7))):
            try:
                unexpected = connect("duckdb", value)
            except TypeError:
                rejected.append(name)
            else:
                unexpected.close()
                raise AssertionError("nontext destination was accepted")
        if len(rejected) != 3 or set(rejected) != {"bytes", "protocol-bytes", "protocol-integer"}:
            raise AssertionError("rejected nontext destination population changed")
        checks.append("nontext-destinations-refused")
        store.prepare()
        checks.append("idle-connection-precondition")
    if len(checks) != len(CHECKS[store.engine]) or set(checks) != CHECKS[store.engine]:
        raise AssertionError("connection precondition population changed")
    if any(store.counts()[name] for name in ("instance_file", "runtime_document", "reference_contract")):
        raise AssertionError("connection setup controls wrote document or initialization rows")
    return checks
