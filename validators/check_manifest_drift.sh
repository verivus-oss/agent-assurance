#!/usr/bin/env bash
# Verify that reference/database/MANIFEST.toml counts still match the
# ontology files it derives from. Pure POSIX-ish bash + grep + awk —
# no Python, no extra deps. Run from the repo root.
#
# Exits 0 on agreement, 1 on any drift. Prints a small report either way.

set -euo pipefail

REPO_ROOT=${REPO_ROOT:-$(pwd)}
MANIFEST="$REPO_ROOT/reference/database/MANIFEST.toml"
CORE_ONTOLOGY="$REPO_ROOT/core/ontology.toml"

[ -f "$MANIFEST" ]         || { echo "missing $MANIFEST"; exit 1; }
[ -f "$CORE_ONTOLOGY" ]    || { echo "missing $CORE_ONTOLOGY"; exit 1; }

# Discover every profile under profiles/<name>/ontology.toml — the
# drift count is the union across core + every profile, so new
# profiles must not silently inflate the gap.
PROFILE_ONTOLOGIES=()
for dir in "$REPO_ROOT/profiles/"*/; do
    [ -f "$dir/ontology.toml" ] && PROFILE_ONTOLOGIES+=("$dir/ontology.toml")
done

# Extract a top-level integer field from the [counts] table.
#   awk reads the manifest, prints the int value on the right of `<key> =`
#   only while inside the [counts] section.
manifest_count() {
    awk -v key="$1" '
        /^\[counts\]/        { in_counts = 1; next }
        /^\[/                { in_counts = 0 }
        in_counts && $1 == key && $2 == "=" {
            print $3 + 0
            exit
        }
    ' "$MANIFEST"
}

# Count [[<section>]] blocks in a TOML file (top-of-line, no leading
# whitespace — the ontology files use that exact style).
toml_block_count() {
    grep -c "^\[\[$2\]\]" "$1" || true
}

TOTAL_ENTITIES=$(toml_block_count "$CORE_ONTOLOGY" entities)
TOTAL_RELATIONS=$(toml_block_count "$CORE_ONTOLOGY" relations)
TOTAL_VOCABS=$(toml_block_count "$CORE_ONTOLOGY" attribute_vocabularies)

for ont in "${PROFILE_ONTOLOGIES[@]}"; do
    TOTAL_ENTITIES=$((TOTAL_ENTITIES + $(toml_block_count "$ont" entities)))
    TOTAL_RELATIONS=$((TOTAL_RELATIONS + $(toml_block_count "$ont" relations)))
    TOTAL_VOCABS=$((TOTAL_VOCABS + $(toml_block_count "$ont" attribute_vocabularies)))
done

# Template kinds = 1 meta (kind-descriptor) + every *-kind.toml under
# core/ and every profiles/<name>/ subdirectory.
TOTAL_KINDS=$(find "$REPO_ROOT/core" -maxdepth 1 -name '*-kind.toml' | wc -l)
for dir in "$REPO_ROOT/profiles/"*/; do
    [ -d "$dir" ] || continue
    TOTAL_KINDS=$((TOTAL_KINDS + $(find "$dir" -maxdepth 1 -name '*-kind.toml' | wc -l)))
done
TOTAL_KINDS=$((TOTAL_KINDS + 1))  # +1 for the meta `kind-descriptor`

M_KINDS=$(manifest_count template_kinds)
M_ENTITIES=$(manifest_count entity_kinds)
M_RELATIONS=$(manifest_count relation_predicates)
M_VOCABS=$(manifest_count attribute_vocabularies)

fail=0
report() {
    local label=$1 expected=$2 actual=$3
    if [ "$expected" = "$actual" ]; then
        printf "  %-22s %4s == %s\n" "$label" "$expected" "$actual"
    else
        printf "  %-22s %4s != %s   <-- DRIFT\n" "$label" "$expected" "$actual"
        fail=1
    fi
}

echo "manifest-drift check (ontology vs reference/database/MANIFEST.toml)"
echo "  manifest                    ontology"
report template_kinds         "$M_KINDS"     "$TOTAL_KINDS"
report entity_kinds           "$M_ENTITIES"  "$TOTAL_ENTITIES"
report relation_predicates    "$M_RELATIONS" "$TOTAL_RELATIONS"
report attribute_vocabularies "$M_VOCABS"    "$TOTAL_VOCABS"

if [ "$fail" -ne 0 ]; then
    echo ""
    echo "DRIFT detected — regenerate reference/database/postgres/seed.sql and"
    echo "the [counts] table in reference/database/MANIFEST.toml from the"
    echo "current ontology, then re-run this script."
    exit 1
fi

# ----- additional check: RDF schema.ttl footer counts -----
# The Rust generator at tools/dagtoml-rdf embeds the observed counts at
# generation time in a footer comment. Reading these and comparing to
# the live ontology catches the case where someone edited the ontology
# and updated MANIFEST + seed but forgot to re-run dagtoml-rdf.
TTL="$REPO_ROOT/reference/database/rdf/schema.ttl"
if [ -f "$TTL" ]; then
    # Footer line shape:
    #   ### Counts at generation: N template kinds, N entity kinds, N relation predicates, N attribute vocabularies.
    footer=$(grep -E "^### Counts at generation:" "$TTL" || true)
    if [ -z "$footer" ]; then
        echo ""
        echo "DRIFT: $TTL is missing the '### Counts at generation:' footer"
        echo "       (rebuild with: cargo run --release -p dagtoml-rdf -- --repo-root . -o $TTL)"
        exit 1
    fi
    ttl_kinds=$(echo "$footer"        | grep -oE '[0-9]+ template kinds'        | grep -oE '^[0-9]+')
    ttl_entities=$(echo "$footer"     | grep -oE '[0-9]+ entity kinds'          | grep -oE '^[0-9]+')
    ttl_relations=$(echo "$footer"    | grep -oE '[0-9]+ relation predicates'   | grep -oE '^[0-9]+')
    ttl_vocabs=$(echo "$footer"       | grep -oE '[0-9]+ attribute vocabularies'| grep -oE '^[0-9]+')

    echo ""
    echo "rdf-drift check (schema.ttl footer vs ontology)"
    echo "  schema.ttl                  ontology"
    rfail=0
    rep() {
        local label=$1 expected=$2 actual=$3
        if [ "$expected" = "$actual" ]; then
            printf "  %-22s %4s == %s\n" "$label" "$expected" "$actual"
        else
            printf "  %-22s %4s != %s   <-- DRIFT\n" "$label" "$expected" "$actual"
            rfail=1
        fi
    }
    rep template_kinds         "$ttl_kinds"     "$TOTAL_KINDS"
    rep entity_kinds           "$ttl_entities"  "$TOTAL_ENTITIES"
    rep relation_predicates    "$ttl_relations" "$TOTAL_RELATIONS"
    rep attribute_vocabularies "$ttl_vocabs"    "$TOTAL_VOCABS"
    if [ "$rfail" -ne 0 ]; then
        echo ""
        echo "DRIFT: reference/database/rdf/schema.ttl is stale. Rebuild with:"
        echo "  cargo run --release -p dagtoml-rdf -- --repo-root . -o $TTL"
        exit 1
    fi
fi

echo ""

# Comprehensive count-mirror gate. Asserts every count surface in the
# repo (MANIFEST [counts] + expected_*_counts, dagtoml-duckdb {Rust,Go}
# EXPECTED_COUNTS hardcodes) agrees with reality (ontology TOMLs +
# seed.sql row counts). Failure here is drift in any mirror surface,
# not just the four block counts above. See
# validators/check_attribute_values.py and the methodology session
# under docs/reviews/2026-05-23-attribute-values-methodology/.
echo ""
if ! python3 "$REPO_ROOT/validators/check_attribute_values.py" --repo-root "$REPO_ROOT"; then
    exit 1
fi

echo ""
echo "OK — manifest matches ontology + every count-mirror surface agrees"
