#!/usr/bin/env bash
# Prove that the two closed state-mutation vocabularies are loadable and
# queryable in every shipped SQL mirror. This is intentionally a focused
# integration check, not a general SQL-schema membership validator: it covers
# the eight values introduced with the state-mutation kind and nothing else.

set -euo pipefail

REPO_ROOT=${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
DUCKDB_CLI=${DUCKDB_CLI:-duckdb}
POSTGRES_IMAGE=${POSTGRES_IMAGE:-postgres:16}

EXPECTED_ROWS=$(python3 - "$REPO_ROOT" <<'PY'
import pathlib
import sys

repo = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(repo / "validators"))
import _toml11 as tomllib

ontology = tomllib.loads(
    (repo / "profiles/com.verivus.runtime/ontology.toml").read_text()
)
vocabularies = {
    vocabulary["attribute"]: vocabulary.get("values", [])
    for vocabulary in ontology.get("attribute_vocabularies", [])
}
for attribute in ("execution_proof_scheme", "finality_basis"):
    if attribute not in vocabularies:
        raise SystemExit(f"missing {attribute} from the runtime ontology")
    for value in sorted(vocabularies[attribute]):
        print(f"{attribute}|{value}")
PY
)

assert_rows() {
    local engine=$1 actual=$2
    if [ "$actual" = "$EXPECTED_ROWS" ]; then
        printf 'OK — %s accepted all eight state-mutation vocabulary values\n' "$engine"
        return
    fi
    printf 'FAIL — %s returned a different state-mutation vocabulary set\n' "$engine" >&2
    diff -u <(printf '%s\n' "$EXPECTED_ROWS") <(printf '%s\n' "$actual") >&2 || true
    exit 1
}

run_sqlite() {
    local actual
    actual=$(python3 - "$REPO_ROOT" <<'PY'
import pathlib
import sqlite3
import sys

repo = pathlib.Path(sys.argv[1])
conn = sqlite3.connect(":memory:")
conn.executescript((repo / "reference/database/sqlite/schema.sql").read_text())
conn.executescript((repo / "reference/database/sqlite/seed.sql").read_text())
rows = conn.execute(
    """
    SELECT attribute || '|' || value
    FROM dagtoml_attribute_value_allowed
    WHERE attribute IN ('execution_proof_scheme', 'finality_basis')
    ORDER BY attribute, value
    """
).fetchall()
print("\n".join(row[0] for row in rows))
PY
)
    assert_rows "sqlite" "$actual"
}

run_duckdb_tool() {
    local implementation=$1 database=$2 actual
    case "$implementation" in
        rust)
            cargo run --quiet --release --locked \
                --manifest-path "$REPO_ROOT/tools/dagtoml-duckdb/Cargo.toml" -- \
                --repo-root "$REPO_ROOT" -o "$database" --duckdb "$DUCKDB_CLI"
            ;;
        go)
            (
                cd "$REPO_ROOT/tools/dagtoml-duckdb-go"
                go run . --repo-root "$REPO_ROOT" -o "$database" --duckdb "$DUCKDB_CLI"
            )
            ;;
        *)
            printf 'unknown DuckDB implementation: %s\n' "$implementation" >&2
            exit 2
            ;;
    esac

    actual=$("$DUCKDB_CLI" "$database" -noheader -list -c "
        SELECT attribute || '|' || value
        FROM dagtoml.attribute_value_allowed
        WHERE attribute IN ('execution_proof_scheme', 'finality_basis')
        ORDER BY attribute, value;
    ")
    assert_rows "duckdb ($implementation tool)" "$actual"
}

run_postgres() {
    local runtime container actual attempt
    if [ -n "${CONTAINER_RUNTIME:-}" ]; then
        runtime=$CONTAINER_RUNTIME
    elif command -v podman >/dev/null 2>&1; then
        runtime=podman
    elif command -v docker >/dev/null 2>&1; then
        runtime=docker
    else
        printf 'need podman or docker for PostgreSQL round-trip check\n' >&2
        exit 2
    fi

    container="dagtoml-state-mutation-seed-$$"
    cleanup_postgres() {
        "$runtime" rm --force "$container" >/dev/null 2>&1 || true
    }
    trap cleanup_postgres RETURN

    "$runtime" run --detach --name "$container" \
        --env POSTGRES_PASSWORD=postgres \
        "$POSTGRES_IMAGE" >/dev/null
    for attempt in $(seq 1 30); do
        if "$runtime" exec "$container" pg_isready -U postgres -d postgres >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    if [ "$attempt" -eq 30 ] && ! "$runtime" exec "$container" pg_isready -U postgres -d postgres >/dev/null 2>&1; then
        printf 'PostgreSQL container did not become ready\n' >&2
        exit 1
    fi

    "$runtime" cp "$REPO_ROOT/reference/database/postgres/schema.sql" "$container:/tmp/schema.sql"
    "$runtime" cp "$REPO_ROOT/reference/database/postgres/seed.sql" "$container:/tmp/seed.sql"
    "$runtime" exec "$container" psql -U postgres -d postgres -v ON_ERROR_STOP=1 -f /tmp/schema.sql >/dev/null
    "$runtime" exec "$container" psql -U postgres -d postgres -v ON_ERROR_STOP=1 -f /tmp/seed.sql >/dev/null
    actual=$("$runtime" exec "$container" psql -U postgres -d postgres -At -F '|' -c "
        SELECT attribute, value
        FROM dagtoml.attribute_value_allowed
        WHERE attribute IN ('execution_proof_scheme', 'finality_basis')
        ORDER BY attribute, value;
    ")
    assert_rows "postgres" "$actual"
}

if ! command -v "$DUCKDB_CLI" >/dev/null 2>&1; then
    printf 'need DuckDB CLI at %s\n' "$DUCKDB_CLI" >&2
    exit 2
fi

tmp_dir=$(mktemp -d)
cleanup_tmp() {
    rm -rf -- "${tmp_dir:?}"
}
trap cleanup_tmp EXIT

run_sqlite
run_duckdb_tool rust "$tmp_dir/rust.duckdb"
run_duckdb_tool go "$tmp_dir/go.duckdb"
run_postgres
