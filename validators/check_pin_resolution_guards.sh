#!/usr/bin/env bash
# check_pin_resolution_guards.sh
#
# Behavioural regression guards for SPEC 12.8.1 pin resolution defects
# that cannot be tracked as in-tree fixtures (they require alternate
# repo roots with conflicting or symlinked profile sets, which would
# corrupt this repository's own profile directory). Constructs each
# adversarial root under mktemp at run time and asserts all three
# implementations agree. Origin: U10 implementation review rounds 1-2
# (docs/reviews/2026-07-13-closure-record-form-promotion-impl/).
#
# Usage: check_pin_resolution_guards.sh <dagtoml-validate-rs> <dagtoml-validate-go>
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: check_pin_resolution_guards.sh <dagtoml-validate-rs> <dagtoml-validate-go>" >&2
  exit 2
fi

RS="$1"
GO="$2"
PY="${PYTHON:-python3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
SENTINEL="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

TMP="$(mktemp -d)" || { echo "check_pin_resolution_guards.sh: mktemp failed (TMPDIR unwritable?)" >&2; exit 2; }
trap 'rm -rf "$TMP"' EXIT

fail=0
expect() {
  # expect <label> <want:0|1> <cmd...>
  local label="$1" want="$2"
  shift 2
  local got=0
  "$@" >/dev/null 2>&1 || got=1
  if [ "$got" != "$want" ]; then
    echo "GUARD FAILED: ${label} (want exit ${want}, got ${got}): $*"
    fail=1
  else
    echo "  ok: ${label}"
  fi
}

write_profile() {
  # write_profile <dir> <name> <extra-toml...>
  local dir="$1" name="$2"
  mkdir -p "$dir"
  {
    printf 'closure_root = "%s"\n\n' "$SENTINEL"
    printf '[meta]\nschema_version = "0.1.0"\ntemplate_kind = "profile-descriptor"\n\n'
    printf '[profile]\nname = "%s"\nnamespace = "com.example"\nowner = "example"\n' "$name"
    printf 'license = "Apache-2.0"\nextends = []\nontology = "core/ontology.toml"\n'
    printf 'contained_kinds = ["pinned-note"]\n\n'
    printf '[[profile.closure_records]]\ncontained_kind = "pinned-note"\n'
    printf 'field = "notes.body_sha256"\npresence = "required"\n'
  } > "$dir/PROFILE.toml"
}

write_common() {
  # write_common <root>
  mkdir -p "$1/core"
  printf 'closure_root = "%s"\n[meta]\nschema_version = "0.1.0"\ntemplate_kind = "ontology"\n' \
    "$SENTINEL" > "$1/core/ontology.toml"
}

write_doc() {
  # write_doc <path> <root-value> [omit-fp]
  {
    printf 'closure_root = "%s"\n\n[meta]\nschema_version = "0.1.0"\ntemplate_kind = "pinned-note"\n' "$2"
    if [ "${3:-}" != "omit-fp" ]; then
      printf 'framework_profile = "com.example.pin"\n'
    fi
    printf '\n[notes]\nbody_sha256 = "sha256:%s"\n' \
      "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"
  } > "$1"
}

echo "--- GUARD 1: duplicate profile-descriptor names fail closed (rounds 1-2) ---"
R="$TMP/dup"
write_common "$R"
write_profile "$R/profiles/pin-a" "com.example.pin"
write_profile "$R/profiles/pin-b" "com.example.pin"
write_doc "$R/doc.toml" "$SENTINEL" omit-fp
expect "py duplicate-name refusal" 1 "$PY" "$HERE/validate_closure_root.py" "$R/doc.toml" --repo-root "$R"
expect "rs duplicate-name refusal" 1 "$RS" --repo-root "$R" --mode provenance "$R/doc.toml"
expect "go duplicate-name refusal" 1 "$GO" -repo-root "$R" -mode provenance "$R/doc.toml"
expect "py duplicate-name refusal (profile validator)" 1 \
  "$PY" "$HERE/validate_profile_descriptor.py" "$R/profiles/pin-a/PROFILE.toml" --repo-root "$R"

echo "--- GUARD 2: symlinked profile dir is followed by pin discovery (round 1) ---"
R="$TMP/sym"
write_common "$R"
mkdir -p "$TMP/external-profile"
write_profile "$TMP/external-profile" "com.example.pin"
mkdir -p "$R/profiles"
ln -s "$TMP/external-profile" "$R/profiles/pin-link"
# Pinned kind, no framework_profile: MUST be rejected only if the
# symlinked descriptor's pins were discovered.
write_doc "$R/doc.toml" "$SENTINEL" omit-fp
expect "py symlink pin discovery" 1 "$PY" "$HERE/validate_closure_root.py" "$R/doc.toml" --repo-root "$R"
expect "rs symlink pin discovery" 1 "$RS" --repo-root "$R" --mode provenance "$R/doc.toml"
expect "go symlink pin discovery" 1 "$GO" -repo-root "$R" -mode provenance "$R/doc.toml"

echo "--- GUARD 3: symlinked dir also serves kind-descriptor candidates (round 2, R2-2) ---"
printf 'closure_root = "%s"\n[meta]\nschema_version = "0.1.0"\ntemplate_kind = "kind-descriptor"\ndescribes_kind = "pinned-note"\n[kind]\nname = "pinned-note"\n' \
  "$SENTINEL" > "$TMP/external-profile/pinned-note-kind.toml"
expect "py kind-candidate via symlink (accept)" 0 \
  "$PY" "$HERE/validate_profile_descriptor.py" "$R/profiles/pin-link/PROFILE.toml" --repo-root "$R"
expect "rs kind-candidate via symlink (accept)" 0 "$RS" --repo-root "$R" --mode profile "$R/profiles/pin-link/PROFILE.toml"
expect "go kind-candidate via symlink (accept)" 0 "$GO" -repo-root "$R" -mode profile "$R/profiles/pin-link/PROFILE.toml"

echo "--- GUARD 4: trailing-newline profile name rejected everywhere (round 2, R2-1) ---"
# Round-3 correction (R3-1): the first version of this guard omitted the
# kind descriptor, so the root failed on an unrelated INV05 resolution
# error whether or not the regex fix was present (vacuously green under
# mutation). The descriptor below makes the newline name the ONLY
# defect, so reverting the backslash-Z anchor flips this guard.
R="$TMP/nl"
write_common "$R"
write_profile "$R/profiles/nl" "com.example.pin"
printf 'closure_root = "%s"\n[meta]\nschema_version = "0.1.0"\ntemplate_kind = "kind-descriptor"\ndescribes_kind = "pinned-note"\n[kind]\nname = "pinned-note"\n' \
  "$SENTINEL" > "$R/profiles/nl/pinned-note-kind.toml"
"$PY" - "$R/profiles/nl/PROFILE.toml" <<'PYEOF'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
t = p.read_text().replace('name = "com.example.pin"', 'name = """\ncom.example.pin\n"""')
p.write_text(t)
PYEOF
expect "py newline name" 1 "$PY" "$HERE/validate_profile_descriptor.py" "$R/profiles/nl/PROFILE.toml" --repo-root "$R"
expect "rs newline name" 1 "$RS" --repo-root "$R" --mode profile "$R/profiles/nl/PROFILE.toml"
expect "go newline name" 1 "$GO" -repo-root "$R" -mode profile "$R/profiles/nl/PROFILE.toml"

# GUARD 5 is a PARITY PIN, not a mutation-detectable regression guard:
# reverting the CLOSURE_ROOT_RE backslash-Z hardening does NOT flip it,
# because the raw-value equality comparison downstream also rejects the
# smuggled value. What this guard pins is the three-way REJECT verdict
# itself (py/rs/go agree), so a future refactor that quietly starts
# accepting a newline-smuggled closure_root in any one implementation
# breaks here. See the U10 round-3 record for the full rationale.
echo "--- GUARD 5: newline-smuggled closure_root value rejected everywhere (round 3) ---"
R="$TMP/root-nl"
write_common "$R"
write_profile "$R/profiles/pin" "com.example.pin"
printf 'closure_root = "%s"\n[meta]\nschema_version = "0.1.0"\ntemplate_kind = "kind-descriptor"\ndescribes_kind = "pinned-note"\n[kind]\nname = "pinned-note"\n' \
  "$SENTINEL" > "$R/profiles/pin/pinned-note-kind.toml"
{
  printf 'closure_root = """\n%s\n"""\n\n' "$SENTINEL"
  printf '[meta]\nschema_version = "0.1.0"\ntemplate_kind = "pinned-note"\nframework_profile = "com.example.pin"\n\n'
  printf '[notes]\nbody_sha256 = "sha256:af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"\n'
} > "$R/doc.toml"
expect "py newline closure_root" 1 "$PY" "$HERE/validate_closure_root.py" "$R/doc.toml" --repo-root "$R"
expect "rs newline closure_root" 1 "$RS" --repo-root "$R" --mode provenance "$R/doc.toml"
expect "go newline closure_root" 1 "$GO" -repo-root "$R" -mode provenance "$R/doc.toml"

if [ "$fail" -ne 0 ]; then
  echo "PIN-RESOLUTION GUARDS FAILED"
  exit 1
fi
echo "PIN-RESOLUTION GUARDS PASSED"
