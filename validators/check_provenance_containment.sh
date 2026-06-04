#!/usr/bin/env bash
# check_provenance_containment.sh
#
# Behavioural regression guard for the provenance source_path containment
# invariant (SPEC §11: source_path resolves to a file UNDER repo root).
#
# A static corpus fixture cannot isolate this defect: an escaping
# source_path that points at a nonexistent file is rejected by a plain
# read error, and one that points at an existing out-of-repo file is
# rejected by a digest mismatch — both BEFORE any containment check. The
# defect is only observable when the attacker controls the out-of-repo
# file's bytes so the declared source_sha256/source_bytes MATCH it. This
# script constructs exactly that adversarial case and asserts every
# primary + reference validator REJECTS it.
#
# Before the containment fix, the Rust and Go primaries READ the
# out-of-repo file and (digest matching) ACCEPTED the attestation —
# binding provenance to a file outside the repo, weaker than the Python
# cross-check. See docs/reviews/2026-05-30-wp1-falsification/.
#
# Usage: check_provenance_containment.sh <rust-bin> <go-bin>
# Repo root is the current working directory.

set -euo pipefail

RS_BIN="${1:?usage: check_provenance_containment.sh <rust-bin> <go-bin>}"
GO_BIN="${2:?usage: check_provenance_containment.sh <rust-bin> <go-bin>}"
REPO_ROOT="$(pwd)"

work="$(mktemp -d)"
cleanup() { rm -rf "$work"; }
trap cleanup EXIT

# 1. An out-of-repo "secret" the attacker wants to bind provenance to.
secret="$work/secret.txt"
printf 'out-of-repo secret bytes\n' > "$secret"
sha="sha256:$(sha256sum "$secret" | cut -d' ' -f1)"
bytes="$(wc -c < "$secret" | tr -d ' ')"

# 2. A relative source_path that ESCAPES repo root to reach the secret.
rel="$(realpath --relative-to="$REPO_ROOT" "$secret")"
case "$rel" in
  ../*) : ;;  # expected: traversal escapes the repo
  *) echo "FATAL: computed source_path '$rel' does not escape repo root" >&2; exit 2 ;;
esac

# 3. A well-formed provenance attestation whose declared digest/bytes
#    MATCH the out-of-repo secret. Only the containment check stands
#    between this file and acceptance.
fixture="$work/provenance-escape.toml"
cat > "$fixture" <<EOF
# Adversarial: source_path escapes repo root but source_sha256/bytes
# match the out-of-repo target. Containment MUST reject this.
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

[meta]
schema_version  = "0.1.0"
template_kind   = "implementation-dag"
docs            = "https://github.com/verivus-oss/agent-assurance/blob/main/spec.md"
confidentiality = "public"
license         = "Apache-2.0"
title           = "Negative provenance containment fixture"
spec            = "README.md"
decomposition   = "README.md"
created         = "2026-05-30"
total_units     = 0
tier1_units     = []
tier2_units     = []
tier3_units     = []

[provenance]
source_path   = "$rel"
source_sha256 = "$sha"
source_bytes  = $bytes
EOF

# Also assert the digest really matches, so a rejection can only come
# from containment, not from an incidental mismatch.
actual="sha256:$(sha256sum "$secret" | cut -d' ' -f1)"
if [ "$actual" != "$sha" ]; then
  echo "FATAL: test self-check failed (digest drift)" >&2; exit 2
fi

fail=0
assert_rejects() {
  local label="$1"; shift
  echo "--- CONTAINMENT: $label (expect REJECT) ---"
  if "$@" >/dev/null 2>&1; then
    echo "  REGRESSION: $label ACCEPTED an out-of-repo provenance binding"
    fail=1
  else
    echo "  ok: $label rejected the escape"
  fi
}

assert_rejects "rust provenance-binding" \
  "$RS_BIN" --repo-root "$REPO_ROOT" --mode provenance-binding "$fixture"
assert_rejects "go provenance-binding" \
  "$GO_BIN" --repo-root "$REPO_ROOT" --mode provenance-binding "$fixture"
assert_rejects "python provenance-binding" \
  python3 validators/validate_provenance.py "$fixture" --repo-root "$REPO_ROOT"

# Second vector: an ABSOLUTE source_path pointing at the same secret.
abs_fixture="$work/provenance-absolute.toml"
sed "s#^source_path .*#source_path   = \"$secret\"#" "$fixture" > "$abs_fixture"
assert_rejects "rust absolute source_path" \
  "$RS_BIN" --repo-root "$REPO_ROOT" --mode provenance-binding "$abs_fixture"
assert_rejects "go absolute source_path" \
  "$GO_BIN" --repo-root "$REPO_ROOT" --mode provenance-binding "$abs_fixture"
assert_rejects "python absolute source_path" \
  python3 validators/validate_provenance.py "$abs_fixture" --repo-root "$REPO_ROOT"

if [ "$fail" -ne 0 ]; then
  echo "provenance containment guard FAILED" >&2
  exit 1
fi
echo "provenance containment guard PASSED (all validators rejected both escape vectors)"
