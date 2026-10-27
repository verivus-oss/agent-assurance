#!/usr/bin/env bash
# Verify both RDF generators keep malformed kind declarations out of the graph.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: check_rdf_descriptor_guards.sh <rust-rdf> <go-rdf>" >&2
  exit 2
fi

RS="$1"
GO="$2"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp -a "$REPO/core" "$REPO/profiles" "$TMP/"
KIND="$TMP/core/implementation-dag-kind.toml"
fail=0

expect() {
  local label="$1" want="$2"
  shift 2
  local got=0
  "$@" >/dev/null 2>&1 || got=1
  if [ "$got" != "$want" ]; then
    echo "RDF GUARD FAILED: $label (want $want, got $got)"
    fail=1
  else
    echo "  ok: $label"
  fi
}

check_pair() {
  local label="$1" want="$2"
  expect "rust $label" "$want" "$RS" --repo-root "$TMP"
  expect "go $label" "$want" "$GO" -repo-root "$TMP"
}

check_pair "intact descriptors" 0
for defect in wrong-template-kind mismatched-kind missing-kind; do
  cp "$REPO/core/implementation-dag-kind.toml" "$KIND"
  python3 - "$KIND" "$defect" <<'PYEOF'
import pathlib, sys
path = pathlib.Path(sys.argv[1])
source = path.read_text()
old, replacement = {
    "wrong-template-kind": ('template_kind     = "kind-descriptor"', 'template_kind     = "implementation-dag"'),
    "mismatched-kind": ('describes_kind    = "implementation-dag"', 'describes_kind    = "other"'),
    "missing-kind": ('name    = "implementation-dag"', 'name    = ""'),
}[sys.argv[2]]
assert source.count(old) == 1
path.write_text(source.replace(old, replacement))
PYEOF
  check_pair "$defect" 1
done
cp "$REPO/core/implementation-dag-kind.toml" "$KIND"
mkdir "$TMP/profiles/cost/rogue-kind.toml"
check_pair "directory named as a descriptor" 1

if [ "$fail" -ne 0 ]; then
  exit 1
fi
echo "RDF DESCRIPTOR GUARDS PASSED"
