"""Native libpq execution for the reference store's buffered SQL operations."""

import psycopg
from psycopg.adapt import PyFormat, Transformer
from psycopg.types.json import set_json_loads

from _json_decode import loads


def require_compiled_adapters():
    if (psycopg.pq.__impl__ not in ("binary", "c")
            or Transformer.__module__ not in ("psycopg_binary._psycopg", "psycopg_c._psycopg")):
        raise RuntimeError("PostgreSQL mirror requires compiled psycopg adapters")


class _Rows:
    def __init__(self, result, transformer):
        self._result = result
        self._transformer = transformer
        self._position = 0
        if result.status == psycopg.pq.ExecStatus.TUPLES_OK:
            transformer.set_pgresult(result)

    def _require_rows(self):
        if self._result.status != psycopg.pq.ExecStatus.TUPLES_OK:
            raise psycopg.ProgrammingError("PostgreSQL command did not return rows")

    def fetchone(self):
        self._require_rows()
        if self._position == self._result.ntuples:
            return None
        row = self._transformer.load_row(self._position, tuple)
        self._position += 1
        return row

    def fetchall(self):
        self._require_rows()
        rows = self._transformer.load_rows(self._position, self._result.ntuples, tuple)
        self._position = self._result.ntuples
        return rows


class NativeConnection:
    """Keep driver adaptation while bypassing its SQL and error text matchers."""

    __slots__ = ("_connection",)

    def __init__(self, connection):
        require_compiled_adapters()
        object.__setattr__(self, "_connection", connection)
        connection.cursor_factory = psycopg.RawCursor
        connection.prepare_threshold = None
        set_json_loads(loads, connection)

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def __setattr__(self, name, value):
        setattr(self._connection, name, value)

    def __enter__(self):
        return self

    def __exit__(self, *_exception):
        self._connection.close()
        return False

    def execute(self, sql, parameters=()):
        connection = self._connection
        with connection.lock:
            pgconn = connection.pgconn
            if pgconn.status != psycopg.pq.ConnStatus.OK:
                raise psycopg.OperationalError("PostgreSQL connection is not open")
            encoding = connection.info.encoding
            query = sql.encode(encoding) if isinstance(sql, str) else sql.as_bytes(connection)
            transformer = Transformer(connection)
            if parameters:
                values = transformer.dump_sequence(parameters, [PyFormat.AUTO] * len(parameters))
                result = pgconn.exec_params(query, values, param_types=transformer.types,
                                            param_formats=transformer.formats)
            else:
                result = pgconn.exec_(query)
            if result.status == psycopg.pq.ExecStatus.FATAL_ERROR:
                # Use structured fields, never the driver's severity-prefix
                # matcher or rendered SQL with source coordinates.
                state = (result.error_field(psycopg.pq.DiagnosticField.SQLSTATE) or b"").decode("ascii", "replace")
                message = result.error_field(psycopg.pq.DiagnosticField.MESSAGE_PRIMARY)
                detail = message.decode(encoding, "replace") if message else "PostgreSQL command failed"
                try:
                    error_class = psycopg.errors.lookup(state)
                except KeyError:
                    error_class = (psycopg.OperationalError if pgconn.status == psycopg.pq.ConnStatus.BAD
                                   else psycopg.DatabaseError)
                error = error_class(detail)
                error.sqlstate = state or None
                raise error
            if result.status not in (psycopg.pq.ExecStatus.TUPLES_OK, psycopg.pq.ExecStatus.COMMAND_OK,
                                     psycopg.pq.ExecStatus.EMPTY_QUERY):
                raise psycopg.NotSupportedError("unsupported PostgreSQL result status")
            return _Rows(result, transformer)


def native_connection(connection):
    # Preserve fault-injection wrappers, whose delegate is already configured.
    return NativeConnection(connection) if isinstance(connection, psycopg.Connection) else connection
