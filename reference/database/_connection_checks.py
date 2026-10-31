"""Executed connection preconditions, using only private test destinations."""

from contextlib import closing

from _storage import StorageError, connect, connect_postgres

CHECKS = {"sqlite": {"foreign-keys-enabled-and-read-back", "disabled-checks-refused"},
          "postgres": {"native-execution-without-driver-text-matchers", "non-utf8-client-refused",
                       "non-utf8-server-refused", "aborted-caller-transaction-preserved",
                       "text-connection-parameters", "invalid-connection-parameters-refused"},
          "duckdb": {"idle-connection-precondition", "text-path-destinations",
                     "nul-text-destinations-refused", "nontext-destinations-refused"}}


class _ConnectionText(str):
    def encode(self, *_args, **_kwargs):
        raise AssertionError("connection text encoding override was executed")

    def __contains__(self, _value):
        raise AssertionError("connection text containment override was executed")


def exercise_rejected_postgres_parameters(destination):
    """Reject invalid input before driver loading or network connection."""
    nul_cases = ((destination + "\0ignored", None),
                 (_ConnectionText(destination + "\0ignored"), None),
                 (destination, "bad\0name"),
                 (destination, _ConnectionText("bad\0name")))
    rejected = 0
    for value, name in nul_cases:
        try:
            unexpected = connect_postgres(value, dbname=name)
        except StorageError as exc:
            if exc.code != "setup" or "NUL bytes" not in str(exc):
                raise AssertionError("NUL connection failed for an unrelated reason") from exc
        else:
            unexpected.close()
            raise AssertionError("NUL connection parameter was accepted or truncated")
        rejected += 1
    if rejected != 4:
        raise AssertionError("NUL connection rejection population changed")
    rejected = 0
    for value in (b"not-text", 7, object()):
        for connection_text, name in ((value, None), (destination, value)):
            try:
                unexpected = connect_postgres(connection_text, dbname=name)
            except TypeError as exc:
                if "must be text" not in str(exc):
                    raise AssertionError("nontext connection failed for an unrelated reason") from exc
            else:
                unexpected.close()
                raise AssertionError("nontext connection parameter was accepted")
            rejected += 1
    if rejected != 6:
        raise AssertionError("nontext connection rejection population changed")


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
        from _postgres_checks import exercise_postgres
        checks.extend(exercise_postgres(store, destination, refused,
                                        exercise_rejected_postgres_parameters, _ConnectionText))
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
            with closing(connect("duckdb", value)) as connection:
                if connection.execute("SELECT 7").fetchone() != (7,):
                    raise AssertionError("accepted destination changed the connected query result")
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
