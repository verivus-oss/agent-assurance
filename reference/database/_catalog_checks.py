"""Real-engine rejection controls for the complete vocabulary metadata mirror."""

from _storage import StorageError
from _instrument import require

CHECKS = frozenset({"false-backing-hint-rejected", "missing-backing-hint-rejected"})


def exercise_catalog_metadata(store):
    store.verify_catalog()
    column = "backing_check_constraint" if store.engine == "sqlite" else "backing_enum_type"
    before = {row["attribute"]: row[column] for row in store.rows("attribute_vocabulary", ("attribute", column))}
    checks = []
    for name, attribute, value in (("false-backing-hint-rejected", "smoke.decision", "smoke_status" if store.engine == "sqlite" else "smoke_decision"),
                                  ("missing-backing-hint-rejected", "runtime_kind", None)):
        require(before[attribute] != value)
        try:
            with store.transaction():
                store.execute(f"UPDATE {store.table('attribute_vocabulary')} SET {column} = ? WHERE attribute = ?", (value, attribute))  # nosec B608 # noqa: S608
                store.verify_catalog()
        except StorageError as exc:
            require(exc.code == "catalog-mismatch" and "backing hints differ" in str(exc), str(exc))
        else:
            raise AssertionError("metadata mutation survived: " + name)
        restored = {row["attribute"]: row[column] for row in store.rows("attribute_vocabulary", ("attribute", column))}
        require(restored == before, "metadata rejection did not roll back")
        store.verify_catalog()
        checks.append(name)
    require(len(checks) == len(CHECKS) and set(checks) == CHECKS)
    return checks
