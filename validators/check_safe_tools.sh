#!/usr/bin/env bash
# Enforce the "safe-only" policy for native code under tools/.
#
#   Rust: every Rust crate at tools/<name>/ MUST have
#         `#![forbid(unsafe_code)]` near the top of its
#         src/main.rs or src/lib.rs.
#
#   Go:   no .go file under tools/ may `import "unsafe"`.
#
# Pure POSIX-ish bash + grep + find. No Python, no third-party deps.
# Run from the repo root; exits non-zero on any violation.
#
# Rationale: dependencies (serde, oxttl, go-toml/v2, etc.) may use
# unsafe internally — that is out of scope for this check. What we
# enforce is that nothing WE write under tools/ reaches for unsafe.
# Dependencies' use is the responsibility of cargo-geiger / go-vet
# audits, which are separate concerns.

set -euo pipefail

REPO_ROOT=${REPO_ROOT:-$(pwd)}
TOOLS_DIR="$REPO_ROOT/tools"

if [ ! -d "$TOOLS_DIR" ]; then
    echo "no tools/ dir at $TOOLS_DIR — nothing to check"
    exit 0
fi

fail=0

# ---------- Rust ----------
rust_crates=()
while IFS= read -r -d '' c; do
    rust_crates+=("$(dirname "$c")")
done < <(find "$TOOLS_DIR" -maxdepth 2 -name 'Cargo.toml' -print0)

if [ "${#rust_crates[@]}" -gt 0 ]; then
    echo "safe-Rust check: ${#rust_crates[@]} crate(s) under tools/"
    for crate in "${rust_crates[@]}"; do
        name=$(basename "$crate")
        # Look for the lint declaration in EITHER main.rs OR lib.rs.
        found=0
        for entry in "$crate/src/main.rs" "$crate/src/lib.rs"; do
            [ -f "$entry" ] || continue
            if grep -qE '^#!\[forbid\(unsafe_code\)\]' "$entry"; then
                found=1
                break
            fi
        done
        if [ "$found" -eq 1 ]; then
            printf "  %-30s  OK (forbid(unsafe_code) present)\n" "$name"
        else
            printf "  %-30s  FAIL — missing #![forbid(unsafe_code)] in src/main.rs or src/lib.rs\n" "$name"
            fail=1
        fi
        # Belt-and-braces: also scan every .rs file for `unsafe {` or
        # `unsafe fn`. forbid() should catch this at compile time, but
        # the grep catches it earlier and gives a clearer error.
        if grep -rnE '^\s*unsafe[[:space:]]*[{(]|^\s*unsafe[[:space:]]+fn' \
             "$crate/src" 2>/dev/null | grep -v '^[^:]*://' >/tmp/unsafe-rs.txt; then
            if [ -s /tmp/unsafe-rs.txt ]; then
                echo "    found unsafe block(s):"
                sed 's/^/      /' /tmp/unsafe-rs.txt
                fail=1
            fi
        fi
    done
else
    echo "safe-Rust check: no Rust crates under tools/"
fi

# ---------- Go ----------
go_modules=()
while IFS= read -r -d '' g; do
    go_modules+=("$(dirname "$g")")
done < <(find "$TOOLS_DIR" -maxdepth 2 -name 'go.mod' -print0)

if [ "${#go_modules[@]}" -gt 0 ]; then
    echo "safe-Go check: ${#go_modules[@]} module(s) under tools/"
    for mod in "${go_modules[@]}"; do
        name=$(basename "$mod")
        # Match any of:
        #   import "unsafe"
        #   import _ "unsafe"
        #   "unsafe"  (inside an import (...) group)
        # but NOT references in comments or doc strings.
        offending=$(grep -rnE \
            '(^[[:space:]]*import[[:space:]]+(_[[:space:]]+)?"unsafe")|(^[[:space:]]*"unsafe")' \
            "$mod" --include='*.go' 2>/dev/null || true)
        if [ -n "$offending" ]; then
            printf "  %-30s  FAIL — 'unsafe' import detected:\n" "$name"
            # shellcheck disable=SC2001  # sed is the idiomatic way to add a fixed indent
            echo "$offending" | sed 's/^/      /'
            fail=1
        else
            printf "  %-30s  OK (no unsafe import)\n" "$name"
        fi
    done
else
    echo "safe-Go check: no Go modules under tools/"
fi

if [ "$fail" -ne 0 ]; then
    echo ""
    echo "SAFETY VIOLATION — tools/ contains native code that opted into"
    echo "unsafe primitives. Native tooling in this repo MUST be safe Rust"
    echo "(#![forbid(unsafe_code)]) and safe Go (no \`unsafe\` import)."
    echo "If a tool genuinely needs unsafe, surface the case in a design"
    echo "doc and update this script's policy explicitly — do not bypass."
    exit 1
fi

echo ""
echo "OK — all tools/ are safe (forbid(unsafe_code) Rust + unsafe-free Go)"
