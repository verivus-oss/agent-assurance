#!/usr/bin/env bash
# Compare parsed declarations and selected executed receipts from the repo root.
# Python and the pinned TOML parser are required. SQL is available only for
# opaque artifact hashing inside this checker; engines interpret its semantics.
set -euo pipefail
REPO_ROOT=${REPO_ROOT:-$(pwd)}
exec python3 "$REPO_ROOT/validators/check_sql_source_access.py" --repo-root "$REPO_ROOT" "$@"
