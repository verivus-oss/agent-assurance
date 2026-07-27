// dagtoml-validate-go is the Go primary validator for DAG-TOML
// canonical examples, profiles, ontologies, kind descriptors, and
// semantic invariants.
//
// It runs in CI alongside the safe-Rust validator
// (tools/dagtoml-validate-rs/). Both are primary; the Python
// validators under validators/ are retained as cross-check
// references.
package main

import (
	"crypto/sha256"
	"crypto/sha512"
	"encoding/hex"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode"

	"github.com/BurntSushi/toml"
	pelletier "github.com/pelletier/go-toml/v2"
)

// ----------------------------------------------------------------------------
// Generic TOML loading
// ----------------------------------------------------------------------------

type rawDoc = map[string]any

func loadDoc(path string) (rawDoc, error) {
	bytes, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("%s: read failed: %w", path, err)
	}
	// Strict TOML 1.1 pre-check (issue #38 / contract C01). BurntSushi/toml
	// v1.6.0 is permissive on 13 dotted-key / inline-table redefinition cases
	// that the Rust (`toml` 1.1) and Python (tomli) primaries correctly reject.
	// pelletier/go-toml/v2 rejects all 13 while accepting the full TOML 1.1
	// valid corpus, so it runs first as a strictness gate: on a pelletier
	// parse error we REJECT here and never reach the BurntSushi decode. Every
	// document this validator currently accepts is valid TOML 1.1 and passes
	// pelletier, so the gate adds strictness without regressing acceptance.
	var strictSink any
	if err := pelletier.Unmarshal(bytes, &strictSink); err != nil {
		return nil, fmt.Errorf("%s: TOML parse failed (strict): %w", path, err)
	}
	// BurntSushi performs the structural decode the rest of the validator
	// relies on (its typed array/datetime shapes are threaded through
	// asArray/int64Of and the per-kind validators).
	var out rawDoc
	if _, err := toml.Decode(string(bytes), &out); err != nil {
		return nil, fmt.Errorf("%s: TOML parse failed: %w", path, err)
	}
	return out, nil
}

func tableOf(v any, key string) (map[string]any, bool) {
	m, ok := v.(map[string]any)
	if !ok {
		return nil, false
	}
	sub, ok := m[key].(map[string]any)
	return sub, ok
}

// hasKey reports whether a key is PRESENT, whatever its TOML type.
//
// tableOf answers false both for an absent key and for a key holding a
// non-table, which is the right answer when a table is required and the wrong
// one when a key is FORBIDDEN. RKC02 was enforced through
// tableOf, so a mutation-claim carrying `execution_proof = [{ ...proof... }]`
// declared proof material that the check never saw. An invariant that forbids
// a field must ask whether the field is there, not whether it is well-formed.
func hasKey(v any, key string) bool {
	m, ok := v.(map[string]any)
	if !ok {
		return false
	}
	_, present := m[key]
	return present
}

func stringOf(v any, key string) (string, bool) {
	m, ok := v.(map[string]any)
	if !ok {
		return "", false
	}
	s, ok := m[key].(string)
	return s, ok
}

// fieldState distinguishes the two cases stringOf collapses into a single
// false. A caller that defaults a wrong-typed value to "" and then skips its
// check on an empty value skips it on the wrong-typed value too, which is how
// `scheme = 1` and `scheme = ""` both bypassed the closed-vocabulary check
// while the Python reference rejected them.
type fieldState int

const (
	fieldAbsent fieldState = iota
	fieldNotString
	fieldString
)

func fieldOf(v any, key string) (string, fieldState) {
	m, ok := v.(map[string]any)
	if !ok {
		return "", fieldAbsent
	}
	raw, present := m[key]
	if !present {
		return "", fieldAbsent
	}
	s, ok := raw.(string)
	if !ok {
		return "", fieldNotString
	}
	return s, fieldString
}

// asArray normalizes the several shapes BurntSushi/toml may decode an
// array as into a uniform []any. TOML's `[[arrays-of-tables]]` are
// decoded as `[]map[string]any`, while `arr = [1, 2, 3]` lands as
// `[]any`. Both need to be treatable identically here.
func asArray(v any) ([]any, bool) {
	switch t := v.(type) {
	case []any:
		return t, true
	case []map[string]any:
		out := make([]any, len(t))
		for i, m := range t {
			out[i] = m
		}
		return out, true
	case []string:
		out := make([]any, len(t))
		for i, s := range t {
			out[i] = s
		}
		return out, true
	}
	return nil, false
}

// ----------------------------------------------------------------------------
// CLI
// ----------------------------------------------------------------------------

type mode int

const (
	modeAuto mode = iota
	modeProfile
	modeDisclosure
	modeProvenance
	modeMeta
	modeGateDecision
	modeMutationKinds
	modeKindDescriptor
	modeIJB
	modeProvenanceBinding
	modeImplementationDag
	modeTraceability
	modeReviewReadiness
	modeCostRecord
	modeRollbackPlan
	modeAbstractionClass
)

func parseMode(s string) (mode, error) {
	switch s {
	case "auto":
		return modeAuto, nil
	case "profile":
		return modeProfile, nil
	case "disclosure":
		return modeDisclosure, nil
	case "provenance":
		return modeProvenance, nil
	case "meta":
		return modeMeta, nil
	case "gate-decision":
		return modeGateDecision, nil
	case "mutation-kinds":
		return modeMutationKinds, nil
	case "kind-descriptor":
		return modeKindDescriptor, nil
	case "ijb":
		return modeIJB, nil
	case "provenance-binding":
		return modeProvenanceBinding, nil
	case "implementation-dag":
		return modeImplementationDag, nil
	case "traceability":
		return modeTraceability, nil
	case "review-readiness":
		return modeReviewReadiness, nil
	case "cost-record":
		return modeCostRecord, nil
	case "rollback-plan":
		return modeRollbackPlan, nil
	case "abstraction-class":
		return modeAbstractionClass, nil
	}
	return modeAuto, fmt.Errorf("invalid mode %q (want auto|profile|disclosure|provenance|meta|gate-decision|kind-descriptor|ijb|provenance-binding|implementation-dag|traceability|review-readiness|cost-record|rollback-plan|abstraction-class)", s)
}

// ----------------------------------------------------------------------------
// kind-descriptor structural validation
// ----------------------------------------------------------------------------

var kdPlaceholderMarkers = []string{"<", ">", "YYYY-MM-DD"}

func hasPlaceholder(s string) bool {
	for _, marker := range kdPlaceholderMarkers {
		if strings.Contains(s, marker) {
			return true
		}
	}
	return false
}

func isProseField(path string) bool {
	return path == "kind.prose" ||
		path == "kind.summary" ||
		strings.HasSuffix(path, ".inline") ||
		strings.HasSuffix(path, ".inline_summary") ||
		strings.HasSuffix(path, ".description") ||
		strings.HasSuffix(path, ".statement") ||
		strings.HasSuffix(path, ".notes") ||
		strings.HasSuffix(path, ".note")
}

func iterStrings(node any, prefix string, out *[][2]string) {
	switch x := node.(type) {
	case string:
		*out = append(*out, [2]string{prefix, x})
	case map[string]any:
		for k, v := range x {
			sub := k
			if prefix != "" {
				sub = prefix + "." + k
			}
			iterStrings(v, sub, out)
		}
	case []any:
		for i, v := range x {
			iterStrings(v, fmt.Sprintf("%s[%d]", prefix, i), out)
		}
	case []map[string]any:
		for i, v := range x {
			iterStrings(v, fmt.Sprintf("%s[%d]", prefix, i), out)
		}
	}
}

func validateKindDescriptor(path string, doc rawDoc, repoRoot string, checkRefs bool) []string {
	var errs []string
	meta, ok := doc["meta"].(map[string]any)
	if !ok {
		return []string{"missing required `[meta]` table"}
	}
	for _, field := range []string{"schema_version", "template_kind", "describes_kind", "title"} {
		if _, present := meta[field]; !present {
			errs = append(errs, fmt.Sprintf("meta: missing required field `%s`", field))
		}
	}
	if tk, _ := meta["template_kind"].(string); tk != "kind-descriptor" {
		errs = append(errs, fmt.Sprintf("meta.template_kind: expected \"kind-descriptor\", got %q", tk))
	}
	describes, describesOK := meta["describes_kind"].(string)
	if _, present := meta["describes_kind"]; present && !describesOK {
		errs = append(errs, "meta.describes_kind: must be a string")
	}
	kind, ok := doc["kind"].(map[string]any)
	if !ok {
		errs = append(errs, "missing required `[kind]` table")
		return errs
	}
	for _, field := range []string{"name", "summary", "prose"} {
		if _, present := kind[field]; !present {
			errs = append(errs, fmt.Sprintf("kind: missing required field `%s`", field))
		}
	}
	if name, ok := kind["name"].(string); ok && describesOK && name != describes {
		errs = append(errs, fmt.Sprintf("kind.name `%s` does not match meta.describes_kind `%s`", name, describes))
	}
	if summary, ok := kind["summary"].(string); ok && len(strings.TrimSpace(summary)) < 10 {
		errs = append(errs, "kind.summary: must be at least 10 characters")
	}
	if prose, ok := kind["prose"].(string); ok && len(strings.TrimSpace(prose)) < 50 {
		errs = append(errs, "kind.prose: must be at least 50 characters")
	}
	var stringsFound [][2]string
	iterStrings(doc, "", &stringsFound)
	for _, pair := range stringsFound {
		if !isProseField(pair[0]) && hasPlaceholder(pair[1]) {
			errs = append(errs, fmt.Sprintf("%s: placeholder value not allowed", pair[0]))
		}
	}
	if checkRefs {
		if examples, ok := asArray(kind["example"]); ok {
			for _, raw := range examples {
				entry, ok := raw.(map[string]any)
				if !ok {
					continue
				}
				file, ok := entry["file"].(string)
				if !ok || file == "" {
					continue
				}
				if hasPlaceholder(file) {
					errs = append(errs, fmt.Sprintf("kind.example.file: placeholder path not allowed: %s", file))
					continue
				}
				if _, err := os.Stat(filepath.Join(repoRoot, file)); err != nil {
					errs = append(errs, fmt.Sprintf("kind.example.file: path does not exist under repo root: %s", file))
				}
			}
		}
		if invs, ok := asArray(kind["hard_invariants"]); ok {
			for _, raw := range invs {
				entry, ok := raw.(map[string]any)
				if !ok {
					continue
				}
				enforcedBy, ok := entry["enforced_by"].(string)
				if !ok || enforcedBy == "" {
					continue
				}
				lowered := strings.ToLower(enforcedBy)
				if strings.Contains(lowered, "(planned)") || strings.Contains(lowered, "(tbd)") || strings.Contains(lowered, "prose review") {
					continue
				}
				looksPath := (strings.Contains(enforcedBy, "/") || strings.HasSuffix(enforcedBy, ".py") || strings.HasSuffix(enforcedBy, ".toml") || strings.HasSuffix(enforcedBy, ".json")) &&
					!strings.Contains(enforcedBy, " ") && !strings.Contains(enforcedBy, "(")
				if looksPath {
					if _, err := os.Stat(filepath.Join(repoRoot, enforcedBy)); err != nil {
						errs = append(errs, fmt.Sprintf("kind.hard_invariants.enforced_by: path does not exist under repo root: %s", enforcedBy))
					}
				}
			}
		}
		if refs, ok := asArray(kind["references"]); ok {
			for _, raw := range refs {
				ref, ok := raw.(string)
				if !ok {
					continue
				}
				bare := strings.TrimSpace(strings.SplitN(ref, "#", 2)[0])
				if bare == "" || hasPlaceholder(bare) {
					continue
				}
				if _, err := os.Stat(filepath.Join(repoRoot, bare)); err != nil {
					errs = append(errs, fmt.Sprintf("kind.references: path does not exist under repo root: %s", bare))
				}
			}
		}
	}
	_ = path
	return errs
}

// ----------------------------------------------------------------------------
// IJB conformance
// ----------------------------------------------------------------------------

var (
	ijbPrimitives       = []string{"thing", "scope", "path", "observed", "constraint", "time"}
	ijbClasses          = []string{"structural", "instance"}
	ijbConstraintTypes  = []string{"structural", "policy", "observed"}
	ijbMetaFieldMapping = map[string]struct {
		primitive      string
		class          string
		constraintType string
	}{
		"framework_profile": {"scope", "structural", ""},
		"template_kind":     {"scope", "structural", ""},
		"schema_version":    {"constraint", "", "structural"},
		"ontology_version":  {"constraint", "", "structural"},
		"confidentiality":   {"constraint", "", "policy"},
		"license":           {"constraint", "", "policy"},
		"embargo_until":     {"time", "", ""},
	}
)

func validatePrimitiveClass(block map[string]any, loc, expectedPrimitive, expectedClass, expectedConstraintType string) []string {
	var errs []string
	prim, _ := block["ijb_primitive"].(string)
	switch {
	case prim == "":
		errs = append(errs, fmt.Sprintf("%s: missing required `ijb_primitive`", loc))
	case !stringIn(prim, ijbPrimitives):
		errs = append(errs, fmt.Sprintf("%s: `ijb_primitive = %q` is not one of %v", loc, prim, ijbPrimitives))
	case prim != expectedPrimitive:
		errs = append(errs, fmt.Sprintf("%s: `ijb_primitive = %q` does not match the SPEC §10.2 mapping (expected %q)", loc, prim, expectedPrimitive))
	}
	if expectedClass != "" {
		cls, _ := block["ijb_class"].(string)
		switch {
		case cls == "":
			errs = append(errs, fmt.Sprintf("%s: missing required `ijb_class`", loc))
		case !stringIn(cls, ijbClasses):
			errs = append(errs, fmt.Sprintf("%s: `ijb_class = %q` is not one of %v", loc, cls, ijbClasses))
		case cls != expectedClass:
			errs = append(errs, fmt.Sprintf("%s: `ijb_class = %q` does not match the SPEC §10.2 mapping (expected %q)", loc, cls, expectedClass))
		}
	} else if _, present := block["ijb_class"]; present {
		errs = append(errs, fmt.Sprintf("%s: `ijb_class` is not permitted on this block per SPEC §10.2", loc))
	}
	if expectedConstraintType != "" {
		ct, _ := block["ijb_constraint_type"].(string)
		switch {
		case ct == "":
			errs = append(errs, fmt.Sprintf("%s: missing required `ijb_constraint_type`", loc))
		case !stringIn(ct, ijbConstraintTypes):
			errs = append(errs, fmt.Sprintf("%s: `ijb_constraint_type = %q` is not one of %v", loc, ct, ijbConstraintTypes))
		case ct != expectedConstraintType:
			errs = append(errs, fmt.Sprintf("%s: `ijb_constraint_type = %q` does not match the SPEC §10.2 mapping (expected %q)", loc, ct, expectedConstraintType))
		}
	} else if _, present := block["ijb_constraint_type"]; present {
		errs = append(errs, fmt.Sprintf("%s: `ijb_constraint_type` is not permitted on this block per SPEC §10.2", loc))
	}
	return errs
}

func validateIJBOntology(path string, doc rawDoc) []string {
	var errs []string
	if entities, ok := asArray(doc["entities"]); ok {
		for i, raw := range entities {
			if block, ok := raw.(map[string]any); ok {
				label, _ := block["id_prefix"].(string)
				if label == "" {
					label, _ = block["id_pattern"].(string)
				}
				errs = append(errs, validatePrimitiveClass(block, fmt.Sprintf("%s:entities[%d] (%s)", path, i, label), "thing", "structural", "")...)
			}
		}
	}
	if relations, ok := asArray(doc["relations"]); ok {
		for i, raw := range relations {
			if block, ok := raw.(map[string]any); ok {
				label, _ := block["predicate"].(string)
				errs = append(errs, validatePrimitiveClass(block, fmt.Sprintf("%s:relations[%d] (predicate=%s)", path, i, label), "path", "structural", "")...)
			}
		}
	}
	if vocabs, ok := asArray(doc["attribute_vocabularies"]); ok {
		for i, raw := range vocabs {
			block, ok := raw.(map[string]any)
			if !ok {
				continue
			}
			label, _ := block["attribute"].(string)
			loc := fmt.Sprintf("%s:attribute_vocabularies[%d] (attribute=%s)", path, i, label)
			prim, _ := block["ijb_primitive"].(string)
			switch {
			case prim == "":
				errs = append(errs, fmt.Sprintf("%s: missing required `ijb_primitive`", loc))
			case !stringIn(prim, ijbPrimitives):
				errs = append(errs, fmt.Sprintf("%s: `ijb_primitive = %q` is not one of %v", loc, prim, ijbPrimitives))
			case prim != "constraint":
				errs = append(errs, fmt.Sprintf("%s: `ijb_primitive = %q` does not match the SPEC §10.2 mapping (expected \"constraint\")", loc, prim))
			}
			if _, present := block["ijb_class"]; present {
				errs = append(errs, fmt.Sprintf("%s: `ijb_class` is not permitted on attribute_vocabularies blocks", loc))
			}
			ct, _ := block["ijb_constraint_type"].(string)
			switch {
			case ct == "":
				errs = append(errs, fmt.Sprintf("%s: missing required `ijb_constraint_type`", loc))
			case !stringIn(ct, ijbConstraintTypes):
				errs = append(errs, fmt.Sprintf("%s: `ijb_constraint_type = %q` is not one of %v", loc, ct, ijbConstraintTypes))
			}
		}
	}
	if ext, ok := doc["extension_rules"].(map[string]any); ok {
		errs = append(errs, validatePrimitiveClass(ext, path+":[extension_rules]", "constraint", "", "structural")...)
	} else {
		errs = append(errs, fmt.Sprintf("%s: missing required `[extension_rules]` table (SPEC §10.2 row)", path))
	}
	meta, _ := doc["meta"].(map[string]any)
	fieldPrims, ok := meta["ijb_field_primitives"].(map[string]any)
	if !ok {
		errs = append(errs, fmt.Sprintf("%s: missing required `[meta.ijb_field_primitives]` table", path))
		return errs
	}
	for field, expected := range ijbMetaFieldMapping {
		raw, hasAnnotation := fieldPrims[field]
		if !hasAnnotation {
			if _, present := meta[field]; present {
				errs = append(errs, fmt.Sprintf("%s:[meta.ijb_field_primitives].%s: missing required inline annotation table", path, field))
			}
			continue
		}
		block, ok := raw.(map[string]any)
		if !ok {
			errs = append(errs, fmt.Sprintf("%s:[meta.ijb_field_primitives].%s: must be an inline annotation table", path, field))
			continue
		}
		errs = append(errs, validatePrimitiveClass(block, fmt.Sprintf("%s:[meta.ijb_field_primitives].%s", path, field), expected.primitive, expected.class, expected.constraintType)...)
	}
	for field := range fieldPrims {
		if _, ok := ijbMetaFieldMapping[field]; !ok {
			errs = append(errs, fmt.Sprintf("%s:[meta.ijb_field_primitives].%s: unknown meta-field annotation key", path, field))
		}
	}
	return errs
}

func validateIJBKindDescriptor(path string, doc rawDoc) []string {
	kind, ok := doc["kind"].(map[string]any)
	if !ok {
		return []string{fmt.Sprintf("%s: kind-descriptor missing required `[kind]` table", path)}
	}
	var errs []string
	errs = append(errs, validatePrimitiveClass(kind, path+":[kind]", "thing", "structural", "")...)
	for _, key := range []string{"required_fields", "required_sections", "hard_invariants"} {
		if arr, ok := asArray(kind[key]); ok {
			for i, raw := range arr {
				if block, ok := raw.(map[string]any); ok {
					errs = append(errs, validatePrimitiveClass(block, fmt.Sprintf("%s:[[kind.%s]][%d]", path, key, i), "constraint", "", "structural")...)
				}
			}
		}
	}
	if examples, ok := asArray(kind["example"]); ok {
		for i, raw := range examples {
			if block, ok := raw.(map[string]any); ok {
				errs = append(errs, validatePrimitiveClass(block, fmt.Sprintf("%s:[[kind.example]][%d]", path, i), "observed", "", "")...)
			}
		}
	}
	if rto, ok := kind["relation_to_ontology"].(map[string]any); ok {
		errs = append(errs, validatePrimitiveClass(rto, path+":[kind.relation_to_ontology]", "constraint", "", "structural")...)
	}
	return errs
}

func validateIJBProfileDescriptor(path string, doc rawDoc) []string {
	profile, ok := doc["profile"].(map[string]any)
	if !ok {
		return []string{fmt.Sprintf("%s: profile-descriptor missing required `[profile]` table", path)}
	}
	return validatePrimitiveClass(profile, path+":[profile]", "thing", "structural", "")
}

func matchesIDPattern(pattern, value string) bool {
	parts := strings.Split(pattern, `\d+`)
	if len(parts) != 2 || !strings.HasPrefix(value, parts[0]) {
		return value == pattern
	}
	suffix := value[len(parts[0]):]
	if suffix == "" {
		return false
	}
	i := 0
	for i < len(suffix) && suffix[i] >= '0' && suffix[i] <= '9' {
		i++
	}
	if i == 0 {
		return false
	}
	rest := suffix[i:]
	switch parts[1] {
	case "":
		return rest == ""
	case "[a-z]?":
		return rest == "" || (len(rest) == 1 && rest[0] >= 'a' && rest[0] <= 'z')
	default:
		return false
	}
}

func looksUpperPrefix(prefix string) bool {
	if prefix == "" || prefix[0] < 'A' || prefix[0] > 'Z' {
		return false
	}
	for _, r := range prefix[1:] {
		if !(r >= 'A' && r <= 'Z' || r >= '0' && r <= '9' || r == '_') {
			return false
		}
	}
	return true
}

func loadOntology(path string) (rawDoc, error) {
	return loadDoc(path)
}

func buildIJBResolver(ontologies []rawDoc) (map[string]bool, []string, map[string]bool) {
	prefixes := map[string]bool{}
	var patterns []string
	predicates := map[string]bool{}
	for _, doc := range ontologies {
		if entities, ok := asArray(doc["entities"]); ok {
			for _, raw := range entities {
				if block, ok := raw.(map[string]any); ok {
					if prefix, ok := block["id_prefix"].(string); ok && prefix != "" {
						prefixes[prefix] = true
					}
					if pattern, ok := block["id_pattern"].(string); ok && pattern != "" {
						patterns = append(patterns, pattern)
					}
				}
			}
		}
		if relations, ok := asArray(doc["relations"]); ok {
			for _, raw := range relations {
				if block, ok := raw.(map[string]any); ok {
					if pred, ok := block["predicate"].(string); ok && pred != "" {
						predicates[pred] = true
					}
				}
			}
		}
	}
	return prefixes, patterns, predicates
}

func checkEntityRef(token string, prefixes map[string]bool, patterns []string) string {
	if parts := strings.SplitN(token, ":", 2); len(parts) == 2 {
		prefix := parts[0]
		if !looksUpperPrefix(prefix) {
			return ""
		}
		if prefixes[prefix] {
			return ""
		}
		return fmt.Sprintf("entity prefix `%s` in `%s` does not resolve to a declared `[[entities]].id_prefix` in the loaded ontologies", prefix, token)
	}
	for _, pattern := range patterns {
		if matchesIDPattern(pattern, token) {
			return ""
		}
	}
	return ""
}

func walkIJBInstance(node any, parentKey, path string, prefixes map[string]bool, patterns []string, predicates map[string]bool, errs *[]string) {
	switch x := node.(type) {
	case string:
		if parentKey == "id" || predicates[parentKey] {
			if err := checkEntityRef(x, prefixes, patterns); err != "" {
				*errs = append(*errs, fmt.Sprintf("%s: %s", path, err))
			}
		}
	case map[string]any:
		for k, v := range x {
			sub := k
			if path != "" {
				sub = path + "." + k
			}
			walkIJBInstance(v, k, sub, prefixes, patterns, predicates, errs)
		}
	case []any:
		for i, v := range x {
			walkIJBInstance(v, parentKey, fmt.Sprintf("%s[%d]", path, i), prefixes, patterns, predicates, errs)
		}
	case []map[string]any:
		for i, v := range x {
			walkIJBInstance(v, parentKey, fmt.Sprintf("%s[%d]", path, i), prefixes, patterns, predicates, errs)
		}
	}
}

func validateIJBInstance(path string, doc rawDoc, repoRoot string) []string {
	var errs []string
	var ontologies []rawDoc
	corePath := filepath.Join(repoRoot, "core", "ontology.toml")
	coreDoc, err := loadOntology(corePath)
	if err != nil {
		errs = append(errs, fmt.Sprintf("core ontology not found or unparsable at %s", corePath))
	} else {
		errs = append(errs, validateIJBOntology(corePath, coreDoc)...)
		ontologies = append(ontologies, coreDoc)
	}
	if meta, ok := doc["meta"].(map[string]any); ok {
		if fp, ok := meta["framework_profile"].(string); ok && fp != "" {
			profile := fp
			if profile == "AGDF" {
				profile = "agent-assurance"
			}
			profilePath := filepath.Join(repoRoot, "profiles", profile, "ontology.toml")
			profileDoc, err := loadOntology(profilePath)
			if err != nil {
				errs = append(errs, fmt.Sprintf("framework_profile = %q but profile ontology not found or unparsable at %s", fp, profilePath))
			} else {
				errs = append(errs, validateIJBOntology(profilePath, profileDoc)...)
				ontologies = append(ontologies, profileDoc)
			}
		}
	}
	if len(errs) > 0 {
		return errs
	}
	prefixes, patterns, predicates := buildIJBResolver(ontologies)
	walkIJBInstance(doc, "", "", prefixes, patterns, predicates, &errs)
	if units, ok := doc["units"].(map[string]any); ok {
		for unitID := range units {
			matched := false
			for _, pattern := range patterns {
				if matchesIDPattern(pattern, unitID) {
					matched = true
					break
				}
			}
			if !matched {
				errs = append(errs, fmt.Sprintf("units.%s: identifier does not match any declared entity `id_pattern` in the loaded ontologies", unitID))
			}
		}
	}
	_ = path
	return errs
}

func validateIJB(path string, doc rawDoc, repoRoot string) []string {
	tk, _ := stringOf(doc["meta"], "template_kind")
	switch tk {
	case "ontology":
		return validateIJBOntology(path, doc)
	case "kind-descriptor":
		return validateIJBKindDescriptor(path, doc)
	case "profile-descriptor":
		return validateIJBProfileDescriptor(path, doc)
	default:
		return validateIJBInstance(path, doc, repoRoot)
	}
}

// ----------------------------------------------------------------------------
// Full [provenance] source binding validation
// ----------------------------------------------------------------------------

func validateProvenanceBinding(path string, doc rawDoc, repoRoot string) []string {
	var errs []string
	prov, ok := doc["provenance"].(map[string]any)
	if !ok {
		return errs
	}
	sourcePath, ok := prov["source_path"].(string)
	if !ok || sourcePath == "" {
		return []string{fmt.Sprintf("%s: [provenance].source_path is required", path)}
	}
	sourceSHA, ok := prov["source_sha256"].(string)
	if !ok || sourceSHA == "" {
		return []string{fmt.Sprintf("%s: [provenance].source_sha256 is required", path)}
	}
	sourceBytes, ok := int64Of(prov["source_bytes"])
	if !ok {
		return []string{fmt.Sprintf("%s: [provenance].source_bytes is required and must be an integer", path)}
	}
	// SPEC §11: source_path MUST be relative and resolve to a file under
	// repo root. Reject absolute paths and any `..`/symlink escape so an
	// attestation cannot bind its provenance digest to a file outside the
	// repo (e.g. "../../etc/passwd"). Mirrors
	// validators/validate_provenance.py; a primary validator must not be
	// weaker than the cross-check.
	if filepath.IsAbs(sourcePath) {
		return []string{fmt.Sprintf(
			"%s: [provenance].source_path must be relative to repo root, got absolute path %s", path, sourcePath)}
	}
	canonRoot, err := filepath.EvalSymlinks(repoRoot)
	if err != nil {
		return []string{fmt.Sprintf("%s: [provenance] cannot canonicalize repo root: %v", path, err)}
	}
	// EvalSymlinks resolves `..` and follows symlinks (so a symlinked escape
	// is caught by the containment check below) and returns an error for a
	// non-existent path.
	full, err := filepath.EvalSymlinks(filepath.Join(canonRoot, sourcePath))
	if err != nil {
		return []string{fmt.Sprintf("%s: [provenance].source_path does not resolve to a file under repo root (%s): %v", path, sourcePath, err)}
	}
	rel, err := filepath.Rel(canonRoot, full)
	if err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(os.PathSeparator)) {
		return []string{fmt.Sprintf("%s: [provenance].source_path %s resolves outside repo root (%s not under %s); SPEC §11 requires source_path to point to a file under repo root", path, sourcePath, full, canonRoot)}
	}
	if info, statErr := os.Stat(full); statErr != nil || !info.Mode().IsRegular() {
		return []string{fmt.Sprintf("%s: [provenance].source_path does not resolve to a regular file under repo root (%s)", path, sourcePath)}
	}
	data, err := os.ReadFile(full)
	if err != nil {
		return []string{fmt.Sprintf("%s: [provenance].source_path could not be read (%s): %v", path, sourcePath, err)}
	}
	if enc, ok := prov["encryption"].(map[string]any); ok {
		if hashOver, _ := enc["hash_is_over"].(string); hashOver == "plaintext" {
			return errs
		}
	}
	if sourceBytes < 0 || int64(len(data)) != sourceBytes {
		errs = append(errs, fmt.Sprintf("%s: [provenance].source_bytes = %d but actual byte length is %d", path, sourceBytes, len(data)))
	}
	sum := sha256.Sum256(data)
	actual := fmt.Sprintf("sha256:%x", sum)
	if actual != sourceSHA {
		errs = append(errs, fmt.Sprintf("%s: [provenance].source_sha256 = %s but actual digest is %s", path, sourceSHA, actual))
	}
	return errs
}

func int64Of(v any) (int64, bool) {
	switch n := v.(type) {
	case int64:
		return n, true
	case int:
		return int64(n), true
	case int32:
		return int64(n), true
	default:
		return 0, false
	}
}

// ----------------------------------------------------------------------------
// Core implementation-dag validation
// ----------------------------------------------------------------------------

var implementationValidStatus = []string{"pending", "in_progress", "done", "blocked", "deferred"}

func stringSlice(v any) ([]string, bool) {
	arr, ok := asArray(v)
	if !ok {
		return nil, false
	}
	out := make([]string, 0, len(arr))
	for _, raw := range arr {
		s, ok := raw.(string)
		if !ok {
			return nil, false
		}
		out = append(out, s)
	}
	return out, true
}

func validateImplementationUnits(doc rawDoc) ([]string, map[string]map[string]any) {
	var errs []string
	units, ok := doc["units"].(map[string]any)
	if !ok || len(units) == 0 {
		return []string{"no `units` table found"}, nil
	}
	out := map[string]map[string]any{}
	for uid, raw := range units {
		unit, ok := raw.(map[string]any)
		if !ok {
			errs = append(errs, fmt.Sprintf("%s: unit entry must be a table", uid))
			continue
		}
		out[uid] = unit
		for _, field := range []string{"name", "summary", "layer", "tier", "status", "depends_on", "blocks", "estimated_loc"} {
			if _, present := unit[field]; !present {
				errs = append(errs, fmt.Sprintf("%s: missing required field `%s`", uid, field))
			}
		}
		if status, ok := unit["status"].(string); ok && !stringIn(status, implementationValidStatus) {
			errs = append(errs, fmt.Sprintf("%s: invalid status `%s`", uid, status))
		}
		if tier, ok := int64Of(unit["tier"]); ok && (tier < 1 || tier > 3) {
			errs = append(errs, fmt.Sprintf("%s: invalid tier `%d` (must be 1, 2, or 3)", uid, tier))
		}
		if layer, ok := int64Of(unit["layer"]); ok && layer < 0 {
			errs = append(errs, fmt.Sprintf("%s: layer must be a non-negative integer", uid))
		}
		if loc, ok := int64Of(unit["estimated_loc"]); ok && loc < 0 {
			errs = append(errs, fmt.Sprintf("%s: estimated_loc must be a non-negative integer", uid))
		}
	}
	return errs, out
}

func duplicates(xs []string) []string {
	seen := map[string]bool{}
	dupes := map[string]bool{}
	for _, x := range xs {
		if seen[x] {
			dupes[x] = true
		}
		seen[x] = true
	}
	out := make([]string, 0, len(dupes))
	for x := range dupes {
		out = append(out, x)
	}
	sort.Strings(out)
	return out
}

func setFromSlice(xs []string) map[string]bool {
	out := map[string]bool{}
	for _, x := range xs {
		out[x] = true
	}
	return out
}

func validateImplementationEdges(units map[string]map[string]any) ([]string, map[string]map[string]bool, map[string]map[string]bool) {
	var errs []string
	uids := map[string]bool{}
	for uid := range units {
		uids[uid] = true
	}
	deps := map[string]map[string]bool{}
	blocks := map[string]map[string]bool{}
	for uid, unit := range units {
		depList, _ := stringSlice(unit["depends_on"])
		blockList, _ := stringSlice(unit["blocks"])
		for _, r := range depList {
			switch {
			case r == uid:
				errs = append(errs, fmt.Sprintf("%s: depends_on includes self", uid))
			case !uids[r]:
				errs = append(errs, fmt.Sprintf("%s: depends_on references unknown unit `%s`", uid, r))
			}
		}
		for _, r := range duplicates(depList) {
			errs = append(errs, fmt.Sprintf("%s: depends_on has duplicate entry `%s`", uid, r))
		}
		for _, r := range blockList {
			switch {
			case r == uid:
				errs = append(errs, fmt.Sprintf("%s: blocks includes self", uid))
			case !uids[r]:
				errs = append(errs, fmt.Sprintf("%s: blocks references unknown unit `%s`", uid, r))
			}
		}
		for _, r := range duplicates(blockList) {
			errs = append(errs, fmt.Sprintf("%s: blocks has duplicate entry `%s`", uid, r))
		}
		deps[uid] = setFromSlice(depList)
		blocks[uid] = setFromSlice(blockList)
	}
	for a, bs := range blocks {
		for b := range bs {
			if uids[b] && !deps[b][a] {
				errs = append(errs, fmt.Sprintf("inverse mismatch: %s.blocks contains `%s` but %s.depends_on is missing `%s`", a, b, b, a))
			}
		}
	}
	for b, ds := range deps {
		for a := range ds {
			if uids[a] && !blocks[a][b] {
				errs = append(errs, fmt.Sprintf("inverse mismatch: %s.depends_on contains `%s` but %s.blocks is missing `%s`", b, a, a, b))
			}
		}
	}
	return errs, deps, blocks
}

func detectImplementationCycles(deps map[string]map[string]bool) []string {
	var errs []string
	seen := map[string]bool{}
	var visit func(string, []string)
	visit = func(node string, stack []string) {
		for i, s := range stack {
			if s == node {
				cycle := append(append([]string{}, stack[i:]...), node)
				errs = append(errs, fmt.Sprintf("cycle in depends_on: %s", strings.Join(cycle, " -> ")))
				return
			}
		}
		if seen[node] {
			return
		}
		seen[node] = true
		stack = append(stack, node)
		keys := make([]string, 0, len(deps[node]))
		for dep := range deps[node] {
			keys = append(keys, dep)
		}
		sort.Strings(keys)
		for _, dep := range keys {
			visit(dep, stack)
		}
	}
	keys := make([]string, 0, len(deps))
	for uid := range deps {
		keys = append(keys, uid)
	}
	sort.Strings(keys)
	for _, uid := range keys {
		visit(uid, nil)
	}
	return errs
}

func validateImplementationArtifacts(units map[string]map[string]any) []string {
	var errs []string
	producers := map[string][]string{}
	for uid, unit := range units {
		produces, _ := stringSlice(unit["produces"])
		for _, art := range produces {
			producers[art] = append(producers[art], uid)
		}
	}
	for art, ps := range producers {
		if !strings.HasPrefix(art, "ART:") && !strings.HasPrefix(art, "OUT:") {
			errs = append(errs, fmt.Sprintf("%s: produces `%s` has unrecognized prefix (expected ART: or OUT:)", ps[0], art))
		}
		if len(ps) > 1 {
			sort.Strings(ps)
			errs = append(errs, fmt.Sprintf("artifact `%s` has multiple producers: %v", art, ps))
		}
	}
	for uid, unit := range units {
		consumes, _ := stringSlice(unit["consumes"])
		for _, art := range consumes {
			switch {
			case !strings.HasPrefix(art, "ART:") && !strings.HasPrefix(art, "OUT:"):
				errs = append(errs, fmt.Sprintf("%s: consumes `%s` has unrecognized prefix (expected ART: or OUT:)", uid, art))
			case producers[art] == nil:
				errs = append(errs, fmt.Sprintf("%s: consumes `%s` which is not produced by any unit in the DAG", uid, art))
			}
		}
	}
	return errs
}

func validateImplementationLayerOrdering(units map[string]map[string]any, deps map[string]map[string]bool) []string {
	var errs []string
	for u, ds := range deps {
		ul, ok := int64Of(units[u]["layer"])
		if !ok {
			continue
		}
		for d := range ds {
			dl, ok := int64Of(units[d]["layer"])
			if ok && ul <= dl {
				errs = append(errs, fmt.Sprintf("layer ordering: %s (layer=%d) depends_on %s (layer=%d) — a depender must be in a strictly higher layer", u, ul, d, dl))
			}
		}
	}
	return errs
}

func validateImplementationMeta(doc rawDoc, units map[string]map[string]any) []string {
	var errs []string
	meta, _ := doc["meta"].(map[string]any)
	if total, ok := int64Of(meta["total_units"]); ok && total != int64(len(units)) {
		errs = append(errs, fmt.Sprintf("meta.total_units=%d but units table has %d entries", total, len(units)))
	}
	byTier := map[int64]map[string]bool{1: {}, 2: {}, 3: {}}
	for uid, unit := range units {
		if tier, ok := int64Of(unit["tier"]); ok && tier >= 1 && tier <= 3 {
			byTier[tier][uid] = true
		}
	}
	for tier := int64(1); tier <= 3; tier++ {
		key := fmt.Sprintf("tier%d_units", tier)
		declaredList, ok := stringSlice(meta[key])
		if !ok {
			continue
		}
		declared := setFromSlice(declaredList)
		for extra := range declared {
			if !byTier[tier][extra] {
				errs = append(errs, fmt.Sprintf("meta.%s lists `%s` but that unit does not have tier=%d", key, extra, tier))
			}
		}
		for missing := range byTier[tier] {
			if !declared[missing] {
				errs = append(errs, fmt.Sprintf("meta.%s is missing `%s` (unit has tier=%d)", key, missing, tier))
			}
		}
	}
	return errs
}

func longestImplementationPath(units map[string]map[string]any, blocks map[string]map[string]bool) (int64, bool) {
	memo := map[string]int64{}
	visiting := map[string]bool{}
	var dfs func(string) (int64, bool)
	dfs = func(node string) (int64, bool) {
		if v, ok := memo[node]; ok {
			return v, true
		}
		if visiting[node] {
			return 0, false
		}
		visiting[node] = true
		own, _ := int64Of(units[node]["estimated_loc"])
		var bestTail int64
		for next := range blocks[node] {
			if _, ok := units[next]; ok {
				score, ok := dfs(next)
				if !ok {
					return 0, false
				}
				if score > bestTail {
					bestTail = score
				}
			}
		}
		visiting[node] = false
		total := own + bestTail
		memo[node] = total
		return total, true
	}
	var best int64
	for uid := range units {
		score, ok := dfs(uid)
		if !ok {
			return 0, false
		}
		if score > best {
			best = score
		}
	}
	return best, true
}

func validateImplementationComputed(doc rawDoc, units map[string]map[string]any, deps, blocks map[string]map[string]bool) []string {
	var errs []string
	computed, ok := doc["computed"].(map[string]any)
	if !ok {
		return errs
	}
	actualEntry := map[string]bool{}
	actualLeaf := map[string]bool{}
	actualLayers := map[int64]int64{}
	actualTierLoc := map[int64]int64{}
	var actualAll int64
	for uid, unit := range units {
		if len(deps[uid]) == 0 {
			actualEntry[uid] = true
		}
		if len(blocks[uid]) == 0 {
			actualLeaf[uid] = true
		}
		if layer, ok := int64Of(unit["layer"]); ok {
			actualLayers[layer]++
		}
		loc, _ := int64Of(unit["estimated_loc"])
		actualAll += loc
		if tier, ok := int64Of(unit["tier"]); ok && tier >= 1 && tier <= 3 {
			actualTierLoc[tier] += loc
		}
	}
	if declaredList, ok := stringSlice(computed["entry_points"]); ok {
		declared := setFromSlice(declaredList)
		for extra := range declared {
			if !actualEntry[extra] {
				errs = append(errs, fmt.Sprintf("computed.entry_points lists `%s` but its depends_on is non-empty", extra))
			}
		}
		for missing := range actualEntry {
			if !declared[missing] {
				errs = append(errs, fmt.Sprintf("computed.entry_points is missing `%s` (has empty depends_on)", missing))
			}
		}
	}
	if declaredList, ok := stringSlice(computed["leaf_nodes"]); ok {
		declared := setFromSlice(declaredList)
		for extra := range declared {
			if !actualLeaf[extra] {
				errs = append(errs, fmt.Sprintf("computed.leaf_nodes lists `%s` but its blocks is non-empty", extra))
			}
		}
		for missing := range actualLeaf {
			if !declared[missing] {
				errs = append(errs, fmt.Sprintf("computed.leaf_nodes is missing `%s` (has empty blocks)", missing))
			}
		}
	}
	if mp, ok := computed["max_parallel"].(map[string]any); ok {
		for layer, count := range actualLayers {
			key := fmt.Sprintf("layer%d", layer)
			got, ok := int64Of(mp[key])
			switch {
			case !ok:
				errs = append(errs, fmt.Sprintf("computed.max_parallel is missing `%s` (actual count=%d)", key, count))
			case got != count:
				errs = append(errs, fmt.Sprintf("computed.max_parallel.%s=%d but %d unit(s) actually in layer %d", key, got, count, layer))
			}
		}
		for key, raw := range mp {
			if !strings.HasPrefix(key, "layer") {
				continue
			}
			layer, err := strconv.ParseInt(strings.TrimPrefix(key, "layer"), 10, 64)
			if err != nil {
				errs = append(errs, fmt.Sprintf("computed.max_parallel has malformed key `%s`", key))
				continue
			}
			if _, ok := actualLayers[layer]; !ok {
				got, _ := int64Of(raw)
				errs = append(errs, fmt.Sprintf("computed.max_parallel.%s=%d but no units are in layer %d", key, got, layer))
			}
		}
	}
	if loc, ok := computed["loc_totals"].(map[string]any); ok {
		if all, ok := int64Of(loc["all"]); ok && all != actualAll {
			errs = append(errs, fmt.Sprintf("computed.loc_totals.all=%d but sum of estimated_loc=%d", all, actualAll))
		}
		for tier := int64(1); tier <= 3; tier++ {
			key := fmt.Sprintf("tier%d", tier)
			if got, ok := int64Of(loc[key]); ok && got != actualTierLoc[tier] {
				errs = append(errs, fmt.Sprintf("computed.loc_totals.%s=%d but actual sum for tier-%d units=%d", key, got, tier, actualTierLoc[tier]))
			}
		}
	}
	cp, _ := stringSlice(computed["critical_path"])
	cpLoc, hasCPLoc := int64Of(computed["critical_path_loc"])
	if len(cp) == 0 {
		if hasCPLoc {
			errs = append(errs, fmt.Sprintf("computed.critical_path_loc=%d but critical_path is empty or missing", cpLoc))
		}
		return errs
	}
	badRef := false
	for i, uid := range cp {
		if _, ok := units[uid]; !ok {
			errs = append(errs, fmt.Sprintf("computed.critical_path[%d]=`%s` references unknown unit", i, uid))
			badRef = true
		}
	}
	if badRef {
		return errs
	}
	for i := 0; i+1 < len(cp); i++ {
		if !blocks[cp[i]][cp[i+1]] {
			errs = append(errs, fmt.Sprintf("computed.critical_path: %s -> %s is not a direct dependency edge", cp[i], cp[i+1]))
		}
	}
	if len(deps[cp[0]]) != 0 {
		errs = append(errs, fmt.Sprintf("computed.critical_path starts at `%s` which is not an entry point", cp[0]))
	}
	if len(blocks[cp[len(cp)-1]]) != 0 {
		errs = append(errs, fmt.Sprintf("computed.critical_path ends at `%s` which is not a leaf", cp[len(cp)-1]))
	}
	var cpActual int64
	for _, uid := range cp {
		loc, _ := int64Of(units[uid]["estimated_loc"])
		cpActual += loc
	}
	if hasCPLoc && cpLoc != cpActual {
		errs = append(errs, fmt.Sprintf("computed.critical_path_loc=%d but sum along path=%d", cpLoc, cpActual))
	}
	if longest, ok := longestImplementationPath(units, blocks); ok && cpActual < longest {
		errs = append(errs, fmt.Sprintf("computed.critical_path LOC=%d but a longer path exists with LOC=%d", cpActual, longest))
	}
	return errs
}

func validateImplementationDag(path string, doc rawDoc) []string {
	errs, units := validateImplementationUnits(doc)
	if len(units) == 0 {
		return errs
	}
	edgeErrs, deps, blocks := validateImplementationEdges(units)
	errs = append(errs, edgeErrs...)
	errs = append(errs, detectImplementationCycles(deps)...)
	errs = append(errs, validateImplementationArtifacts(units)...)
	errs = append(errs, validateImplementationLayerOrdering(units, deps)...)
	errs = append(errs, validateImplementationMeta(doc, units)...)
	errs = append(errs, validateImplementationComputed(doc, units, deps, blocks)...)
	errs = append(errs, validateImplementationPaths(units)...)
	_ = path
	return errs
}

// implPlaceholderMarkers mirrors PLACEHOLDER_MARKERS in
// validators/validate_implementation_dag.py: implementation-dag file
// claims treat only the angle-bracket markers as placeholders. This is
// deliberately narrower than kdPlaceholderMarkers (which also rejects
// `YYYY-MM-DD`), matching the per-kind policy split in the Python reference.
var implPlaceholderMarkers = []string{"<", ">"}

func hasImplPlaceholder(s string) bool {
	for _, marker := range implPlaceholderMarkers {
		if strings.Contains(s, marker) {
			return true
		}
	}
	return false
}

// validateImplementationPaths mirrors the Python reference validator's
// default placeholder policy: unresolved markers in unit file claims
// are rejected.
func validateImplementationPaths(units map[string]map[string]any) []string {
	var errs []string
	for uid, unit := range units {
		for _, field := range []string{"files_create", "files_modify"} {
			files, _ := stringSlice(unit[field])
			for _, f := range files {
				if hasImplPlaceholder(f) {
					errs = append(errs, fmt.Sprintf("%s.%s: placeholder not allowed: `%s`", uid, field, f))
				}
			}
		}
	}
	return errs
}

// ----------------------------------------------------------------------------
// Core traceability validation
// ----------------------------------------------------------------------------

var traceabilitySections = []string{
	"intents", "features", "requirements", "regulations", "decisions",
	"implementations", "code", "tests", "outputs",
}

func traceabilityLinkFields(section string) []string {
	switch section {
	case "intents":
		return []string{"derived_from", "realized_by"}
	case "features":
		return []string{"realizes", "constrained_by", "implemented_by", "produces"}
	case "requirements", "regulations":
		return []string{"constrains", "verified_by"}
	case "decisions":
		return []string{"addresses", "shapes", "supersedes"}
	case "implementations":
		return []string{"implements", "guided_by", "code", "tests", "downstream_outputs"}
	case "code":
		return []string{"realizes"}
	case "tests":
		return []string{"verifies"}
	case "outputs":
		return []string{"realizes"}
	}
	return nil
}

func traceabilityDownstreamFields(section string) []string {
	switch section {
	case "intents":
		return []string{"realized_by"}
	case "features":
		return []string{"implemented_by", "produces"}
	case "requirements", "regulations":
		return []string{"verified_by", "constrains"}
	case "decisions":
		return []string{"shapes"}
	case "implementations":
		return []string{"code", "tests", "downstream_outputs"}
	case "code":
		return []string{"realizes"}
	case "tests":
		return []string{"verifies"}
	case "outputs":
		return []string{"realizes"}
	}
	return nil
}

func traceabilityGatherEntities(doc rawDoc) (map[string]map[string]any, []string) {
	entities := map[string]map[string]any{}
	var errs []string
	for _, section := range traceabilitySections {
		entries, _ := asArray(doc[section])
		for _, raw := range entries {
			entry, ok := raw.(map[string]any)
			if !ok {
				continue
			}
			id, ok := entry["id"].(string)
			if !ok || id == "" {
				errs = append(errs, fmt.Sprintf("%s: missing required `id` field", section))
				continue
			}
			if _, exists := entities[id]; exists {
				errs = append(errs, fmt.Sprintf("duplicate id: %s", id))
				continue
			}
			entities[id] = entry
		}
	}
	return entities, errs
}

func traceabilityHasPlaceholder(s string) bool {
	return strings.Contains(s, "<") || strings.Contains(s, ">") || strings.Contains(s, "YYYY-MM-DD")
}

func validateTraceabilityLinks(doc rawDoc, entities map[string]map[string]any) []string {
	var errs []string
	for _, section := range traceabilitySections {
		entries, _ := asArray(doc[section])
		for _, raw := range entries {
			entry, ok := raw.(map[string]any)
			if !ok {
				continue
			}
			id, _ := entry["id"].(string)
			if id == "" {
				id = section + ":<missing-id>"
			}
			for _, field := range traceabilityLinkFields(section) {
				targets, _ := stringSlice(entry[field])
				for _, target := range targets {
					if entities[target] == nil {
						errs = append(errs, fmt.Sprintf("%s: `%s` target missing: %s", id, field, target))
					}
				}
			}
		}
	}
	relations, _ := asArray(doc["relations"])
	for _, raw := range relations {
		rel, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		source, _ := rel["from"].(string)
		target, _ := rel["to"].(string)
		typ, _ := rel["type"].(string)
		if typ == "" {
			typ = "<missing-type>"
		}
		if entities[source] == nil {
			errs = append(errs, fmt.Sprintf("relation `%s` missing `from` target: %s", typ, source))
		}
		if entities[target] == nil {
			errs = append(errs, fmt.Sprintf("relation `%s` missing `to` target: %s", typ, target))
		}
	}
	return errs
}

func traceabilityForwardGraph(doc rawDoc) map[string]map[string]bool {
	graph := map[string]map[string]bool{}
	for _, section := range traceabilitySections {
		entries, _ := asArray(doc[section])
		for _, raw := range entries {
			entry, ok := raw.(map[string]any)
			if !ok {
				continue
			}
			id, _ := entry["id"].(string)
			if id == "" {
				continue
			}
			for _, field := range traceabilityDownstreamFields(section) {
				targets, _ := stringSlice(entry[field])
				for _, target := range targets {
					if graph[id] == nil {
						graph[id] = map[string]bool{}
					}
					graph[id][target] = true
				}
			}
		}
	}
	return graph
}

func traceabilityReachable(graph map[string]map[string]bool, start string, prefixes []string) bool {
	stack := []string{start}
	seen := map[string]bool{}
	for len(stack) > 0 {
		current := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if seen[current] {
			continue
		}
		seen[current] = true
		if current != start {
			for _, prefix := range prefixes {
				if strings.HasPrefix(current, prefix) {
					return true
				}
			}
		}
		for next := range graph[current] {
			stack = append(stack, next)
		}
	}
	return false
}

func validateTraceabilityCycles(doc rawDoc) []string {
	var errs []string
	for _, pair := range [][2]string{{"intents", "derived_from"}, {"decisions", "supersedes"}} {
		section, field := pair[0], pair[1]
		graph := map[string]map[string]bool{}
		entries, _ := asArray(doc[section])
		for _, raw := range entries {
			entry, ok := raw.(map[string]any)
			if !ok {
				continue
			}
			id, _ := entry["id"].(string)
			if id == "" {
				continue
			}
			targets, _ := stringSlice(entry[field])
			for _, target := range targets {
				if graph[id] == nil {
					graph[id] = map[string]bool{}
				}
				graph[id][target] = true
			}
		}
		visiting, visited := map[string]bool{}, map[string]bool{}
		var visit func(string) bool
		visit = func(node string) bool {
			if visited[node] {
				return false
			}
			if visiting[node] {
				return true
			}
			visiting[node] = true
			for next := range graph[node] {
				if visit(next) {
					return true
				}
			}
			visiting[node] = false
			visited[node] = true
			return false
		}
		keys := make([]string, 0, len(graph))
		for node := range graph {
			keys = append(keys, node)
		}
		sort.Strings(keys)
		for _, node := range keys {
			if visit(node) {
				errs = append(errs, fmt.Sprintf("%s: `%s` contains a cycle involving %s", section, field, node))
				break
			}
		}
	}
	return errs
}

func validateTraceabilityDownstream(doc rawDoc) []string {
	var errs []string
	graph := traceabilityForwardGraph(doc)
	for _, section := range []string{"requirements", "regulations"} {
		entries, _ := asArray(doc[section])
		for _, raw := range entries {
			entry, ok := raw.(map[string]any)
			if !ok {
				continue
			}
			id, _ := entry["id"].(string)
			if id != "" && !traceabilityReachable(graph, id, []string{"CODE:", "TEST:", "OUT:", "IMP:"}) {
				errs = append(errs, fmt.Sprintf("%s: no downstream realization path to implementation, code, tests, or outputs", id))
			}
		}
	}
	return errs
}

func validateTraceabilityPaths(doc rawDoc) []string {
	var errs []string
	for _, section := range []string{"code", "tests"} {
		entries, _ := asArray(doc[section])
		for _, raw := range entries {
			entry, ok := raw.(map[string]any)
			if !ok {
				continue
			}
			id, _ := entry["id"].(string)
			if id == "" {
				id = section + ":<missing-id>"
			}
			path, _ := entry["path"].(string)
			switch {
			case path == "":
				errs = append(errs, fmt.Sprintf("%s: missing `path`", id))
			case traceabilityHasPlaceholder(path):
				errs = append(errs, fmt.Sprintf("%s: placeholder path not allowed: %s", id, path))
			}
		}
	}
	return errs
}

func validateTraceabilityPlaceholders(doc rawDoc) []string {
	var errs []string
	for _, section := range traceabilitySections {
		entries, _ := asArray(doc[section])
		for _, raw := range entries {
			entry, ok := raw.(map[string]any)
			if !ok {
				continue
			}
			if id, _ := entry["id"].(string); id != "" && traceabilityHasPlaceholder(id) {
				errs = append(errs, fmt.Sprintf("%s: placeholder id not allowed: %s", section, id))
			}
		}
	}
	return errs
}

func validateTraceabilityComputed(doc rawDoc, entities map[string]map[string]any) []string {
	var errs []string
	computed, ok := doc["computed"].(map[string]any)
	if !ok {
		return errs
	}
	for _, field := range []string{"root_intents", "terminal_outputs", "unverified_requirements", "unmapped_code", "coverage_gaps"} {
		targets, _ := stringSlice(computed[field])
		for _, target := range targets {
			if target != "" && field != "coverage_gaps" && entities[target] == nil {
				errs = append(errs, fmt.Sprintf("computed `%s` target missing: %s", field, target))
			}
		}
	}
	return errs
}

func validateTraceability(path string, doc rawDoc) []string {
	entities, errs := traceabilityGatherEntities(doc)
	errs = append(errs, validateTraceabilityPlaceholders(doc)...)
	errs = append(errs, validateTraceabilityLinks(doc, entities)...)
	errs = append(errs, validateTraceabilityCycles(doc)...)
	errs = append(errs, validateTraceabilityDownstream(doc)...)
	errs = append(errs, validateTraceabilityPaths(doc)...)
	errs = append(errs, validateTraceabilityComputed(doc, entities)...)
	_ = path
	return errs
}

// ----------------------------------------------------------------------------
// Review-readiness validation
// ----------------------------------------------------------------------------

func reviewNormalizeKind(value string) string {
	value = strings.ReplaceAll(strings.ToLower(strings.TrimSpace(value)), "_", "-")
	switch value {
	case "readiness-gate", "readiness", "gate-readiness":
		return "readiness-gate"
	case "contract-declaration", "contract", "contracts":
		return "contract-declaration"
	case "evidence-matrix", "evidence", "matrix":
		return "evidence-matrix"
	}
	return ""
}

func reviewSectionAliases(kind string) map[string][]string {
	switch kind {
	case "readiness-gate":
		return map[string][]string{
			"artifact_classes": {"artifact_classes", "artifacts", "readiness.artifact_classes"},
			"gates":            {"gates", "readiness_gates", "readiness.gates"},
		}
	case "contract-declaration":
		return map[string][]string{"contracts": {"contracts", "declarations", "contract_declarations"}}
	case "evidence-matrix":
		return map[string][]string{
			"claims":   {"claims", "assertions"},
			"evidence": {"evidence", "artifacts", "evidence_artifacts"},
			"matrix":   {"matrix", "rows", "evidence_matrix"},
		}
	}
	return nil
}

func reviewRequiredFields(kind, section string) [][]string {
	switch kind + "/" + section {
	case "readiness-gate/artifact_classes":
		return [][]string{{"id"}}
	case "readiness-gate/gates":
		return [][]string{{"id"}, {"artifact_class"}, {"checks", "required_documents", "criteria", "summary"}}
	case "contract-declaration/contracts":
		return [][]string{{"id"}, {"statement", "contract", "summary"}, {"applies_to", "depends_on", "supersedes", "verified_by"}}
	case "evidence-matrix/claims":
		return [][]string{{"id"}, {"claim", "statement", "assertion"}}
	case "evidence-matrix/evidence":
		return [][]string{{"id"}, {"path", "artifact_path", "evidence_path", "file_path"}}
	case "evidence-matrix/matrix":
		return [][]string{{"id"}, {"claim", "claim_id"}, {"evidence", "evidence_id"}, {"scope_covered", "scope"}, {"known_exclusions", "exclusions", "limitations"}}
	}
	return nil
}

func reviewLinkFields(kind, section string) map[string]string {
	switch kind + "/" + section {
	case "readiness-gate/gates":
		return map[string]string{"artifact_class": "artifact_classes"}
	case "contract-declaration/contracts":
		return map[string]string{"depends_on": "contracts", "supersedes": "contracts", "related_to": "contracts", "verified_by": "", "applies_to": ""}
	case "evidence-matrix/matrix":
		return map[string]string{"claim": "claims", "claim_id": "claims", "evidence": "evidence", "evidence_id": "evidence"}
	}
	return nil
}

func dottedValue(doc rawDoc, dotted string) (any, bool) {
	var cur any = doc
	for _, part := range strings.Split(dotted, ".") {
		m, ok := cur.(map[string]any)
		if !ok {
			return nil, false
		}
		cur, ok = m[part]
		if !ok {
			return nil, false
		}
	}
	return cur, true
}

func reviewEntries(value any) []map[string]any {
	switch v := value.(type) {
	case map[string]any:
		return []map[string]any{v}
	case []map[string]any:
		return v
	case []any:
		out := make([]map[string]any, 0, len(v))
		for _, raw := range v {
			if entry, ok := raw.(map[string]any); ok {
				out = append(out, entry)
			}
		}
		return out
	}
	return nil
}

func reviewTargets(value any) []string {
	if s, ok := value.(string); ok {
		return []string{s}
	}
	xs, _ := stringSlice(value)
	return xs
}

func reviewDetectKind(doc rawDoc) string {
	if meta, ok := doc["meta"].(map[string]any); ok {
		for _, key := range []string{"template_kind", "kind", "control_kind", "template"} {
			if raw, _ := meta[key].(string); raw != "" {
				if kind := reviewNormalizeKind(raw); kind != "" {
					return kind
				}
			}
		}
	}
	if _, ok := doc["contracts"]; ok {
		return "contract-declaration"
	}
	if _, ok := doc["declarations"]; ok {
		return "contract-declaration"
	}
	if _, ok := doc["contract_declarations"]; ok {
		return "contract-declaration"
	}
	if _, hasGates := doc["gates"]; hasGates {
		if _, hasClasses := doc["artifact_classes"]; hasClasses {
			return "readiness-gate"
		}
	}
	if _, hasClaims := doc["claims"]; hasClaims {
		if _, hasEvidence := doc["evidence"]; hasEvidence {
			return "evidence-matrix"
		}
	}
	return ""
}

func reviewValuePresent(entry map[string]any, field string) bool {
	v, ok := entry[field]
	if !ok {
		return false
	}
	switch x := v.(type) {
	case string:
		return x != ""
	case []any:
		return len(x) > 0
	case []string:
		return len(x) > 0
	case map[string]any:
		return len(x) > 0
	default:
		return true
	}
}

func collectReviewPlaceholders(value any, prefix string, errs *[]string) {
	switch x := value.(type) {
	case string:
		if traceabilityHasPlaceholder(x) {
			*errs = append(*errs, fmt.Sprintf("placeholder value not allowed at %s", prefix))
		}
	case map[string]any:
		for k, v := range x {
			sub := k
			if prefix != "" {
				sub = prefix + "." + k
			}
			collectReviewPlaceholders(v, sub, errs)
		}
	case []any:
		for i, v := range x {
			collectReviewPlaceholders(v, fmt.Sprintf("%s[%d]", prefix, i), errs)
		}
	case []map[string]any:
		for i, v := range x {
			collectReviewPlaceholders(v, fmt.Sprintf("%s[%d]", prefix, i), errs)
		}
	}
}

func validateReviewReadiness(path string, doc rawDoc) []string {
	var errs []string
	kind := reviewDetectKind(doc)
	if kind == "" {
		return []string{"unable to detect template kind from TOML content"}
	}
	if meta, ok := doc["meta"].(map[string]any); ok {
		if rv, _ := meta["release_version"].(string); rv != "" && rv != "0.1.0" {
			errs = append(errs, fmt.Sprintf("meta.release_version (%s) does not match expected 0.1.0", rv))
		}
	} else {
		errs = append(errs, "missing required `meta` section")
	}
	resolved := map[string][]map[string]any{}
	aliases := reviewSectionAliases(kind)
	for canonical, names := range aliases {
		var raw any
		var foundAlias string
		found := false
		for _, alias := range names {
			if v, ok := dottedValue(doc, alias); ok {
				raw, foundAlias, found = v, alias, true
				break
			}
		}
		if !found {
			errs = append(errs, fmt.Sprintf("missing required `%s` section", canonical))
			continue
		}
		switch raw.(type) {
		case map[string]any, []any, []map[string]any:
		default:
			errs = append(errs, fmt.Sprintf("`%s` must be a table or array of tables", foundAlias))
			continue
		}
		if arr, ok := asArray(raw); ok && len(arr) == 0 {
			errs = append(errs, fmt.Sprintf("`%s` must contain at least one entry", foundAlias))
		}
		resolved[canonical] = reviewEntries(raw)
	}
	idIndex := map[string]string{}
	for section, entries := range resolved {
		for _, entry := range entries {
			id, _ := entry["id"].(string)
			if id == "" {
				errs = append(errs, fmt.Sprintf("%s: missing required `id` field", section))
				continue
			}
			if _, exists := idIndex[id]; exists {
				errs = append(errs, fmt.Sprintf("duplicate id across sections: %s", id))
			} else {
				idIndex[id] = section
			}
			for _, group := range reviewRequiredFields(kind, section) {
				present := false
				for _, field := range group {
					if reviewValuePresent(entry, field) {
						present = true
						break
					}
				}
				if !present {
					if len(group) == 1 {
						errs = append(errs, fmt.Sprintf("%s: missing required `%s` field", id, group[0]))
					} else {
						errs = append(errs, fmt.Sprintf("%s: missing required `%s` field", id, strings.Join(group, "` or `")))
					}
				}
			}
		}
	}
	for section, entries := range resolved {
		for _, entry := range entries {
			id, _ := entry["id"].(string)
			if id == "" {
				id = "<missing-id>"
			}
			for field, targetSection := range reviewLinkFields(kind, section) {
				if targetSection == "" {
					continue
				}
				for _, target := range reviewTargets(entry[field]) {
					actual, ok := idIndex[target]
					switch {
					case !ok:
						errs = append(errs, fmt.Sprintf("%s: `%s` target missing: %s", id, field, target))
					case actual != targetSection:
						errs = append(errs, fmt.Sprintf("%s: `%s` target must reference `%s` ids: %s", id, field, targetSection, target))
					}
				}
			}
		}
	}
	collectReviewPlaceholders(doc, "", &errs)
	_ = path
	return errs
}

// ----------------------------------------------------------------------------
// Cost-record validation
// ----------------------------------------------------------------------------

type costVocabs struct {
	decider   map[string]bool
	citing    map[string]bool
	dimension map[string]bool
}

func ontologyValues(doc rawDoc, attribute string) map[string]bool {
	out := map[string]bool{}
	entries, _ := asArray(doc["attribute_vocabularies"])
	for _, raw := range entries {
		entry, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		if attr, _ := entry["attribute"].(string); attr != attribute {
			continue
		}
		values, _ := asArray(entry["values"])
		for _, rawValue := range values {
			if value, ok := rawValue.(string); ok {
				out[value] = true
			}
		}
	}
	return out
}

func loadCostVocabs(repoRoot string) (costVocabs, error) {
	doc, err := loadDoc(filepath.Join(repoRoot, "profiles/cost/ontology.toml"))
	if err != nil {
		return costVocabs{}, err
	}
	v := costVocabs{
		decider:   ontologyValues(doc, "decider_class"),
		citing:    ontologyValues(doc, "cost_citing_kind"),
		dimension: ontologyValues(doc, "cost_dimension_category"),
	}
	var missing []string
	if len(v.decider) == 0 {
		missing = append(missing, "decider_class")
	}
	if len(v.citing) == 0 {
		missing = append(missing, "cost_citing_kind")
	}
	if len(v.dimension) == 0 {
		missing = append(missing, "cost_dimension_category")
	}
	if len(missing) > 0 {
		return costVocabs{}, fmt.Errorf("cost-profile ontology is missing required vocabularies: %v", missing)
	}
	return v, nil
}

var requiredCostRecordFields = []string{
	"action_id", "incurred_at", "citing_kind", "citing_ref", "decider_class",
	"producer_id", "hash_algorithm", "canonical_form",
}

func validateCostRecord(path string, doc rawDoc, repoRoot string) []string {
	var errs []string
	vocab, err := loadCostVocabs(repoRoot)
	if err != nil {
		return []string{fmt.Sprintf("cost-profile ontology could not be loaded: %v", err)}
	}
	meta, ok := doc["meta"].(map[string]any)
	if !ok || meta["template_kind"] != "cost-record" {
		return []string{fmt.Sprintf("%s: not a cost-record instance (meta.template_kind != 'cost-record')", path)}
	}
	if fp, _ := meta["framework_profile"].(string); fp != "cost" {
		errs = append(errs, fmt.Sprintf("%s: meta.framework_profile must be 'cost', got %q", path, fp))
	}
	record, ok := doc["record"].(map[string]any)
	if !ok {
		errs = append(errs, fmt.Sprintf("%s: missing required `[record]` table", path))
		return errs
	}
	for _, field := range requiredCostRecordFields {
		if value, _ := record[field].(string); value == "" {
			errs = append(errs, fmt.Sprintf("%s: record.%s must be a non-empty string", path, field))
		}
	}
	if incurredAt, ok := record["incurred_at"].(string); ok {
		if _, err := time.Parse(time.RFC3339Nano, incurredAt); err != nil {
			errs = append(errs, fmt.Sprintf("%s: record.incurred_at must be RFC 3339 date-time, got %q", path, incurredAt))
		}
	}
	if citingKind, ok := record["citing_kind"].(string); ok && !vocab.citing[citingKind] {
		errs = append(errs, fmt.Sprintf("%s: record.citing_kind %q not in closed vocabulary", path, citingKind))
	}
	if deciderClass, ok := record["decider_class"].(string); ok && !vocab.decider[deciderClass] {
		errs = append(errs, fmt.Sprintf("%s: record.decider_class %q not in closed vocabulary", path, deciderClass))
	}
	if hashAlgorithm, ok := record["hash_algorithm"].(string); ok {
		switch strings.ToLower(hashAlgorithm) {
		case "md5", "sha1":
			errs = append(errs, fmt.Sprintf("%s: record.hash_algorithm %q is forbidden by SPEC §12.1", path, hashAlgorithm))
		}
	}
	dims, ok := asArray(record["dimensions"])
	if !ok || len(dims) == 0 {
		errs = append(errs, fmt.Sprintf("%s: at least one `[[record.dimensions]]` entry is required", path))
		return errs
	}
	for i, raw := range dims {
		dim, ok := raw.(map[string]any)
		if !ok {
			errs = append(errs, fmt.Sprintf("%s: record.dimensions[%d] must be a table", path, i))
			continue
		}
		category, _ := dim["category"].(string)
		if !vocab.dimension[category] {
			errs = append(errs, fmt.Sprintf("%s: record.dimensions[%d].category %q not in closed vocabulary", path, i, category))
		}
		switch q := dim["quantity"].(type) {
		case int64:
			if q < 0 {
				errs = append(errs, fmt.Sprintf("%s: record.dimensions[%d].quantity must be a non-negative integer; got %d", path, i, q))
			}
		case int:
			if q < 0 {
				errs = append(errs, fmt.Sprintf("%s: record.dimensions[%d].quantity must be a non-negative integer; got %d", path, i, q))
			}
		default:
			errs = append(errs, fmt.Sprintf("%s: record.dimensions[%d].quantity must be a non-negative integer", path, i))
		}
		if unit, _ := dim["unit_label"].(string); unit == "" {
			errs = append(errs, fmt.Sprintf("%s: record.dimensions[%d].unit_label must be a non-empty string", path, i))
		}
	}
	return errs
}

// ----------------------------------------------------------------------------
// Rollback-plan validation
// ----------------------------------------------------------------------------

func triggerKindValues(repoRoot string) (map[string]bool, error) {
	doc, err := loadDoc(filepath.Join(repoRoot, "profiles/agent-assurance/ontology.toml"))
	if err != nil {
		return nil, err
	}
	values := ontologyValues(doc, "trigger_kind")
	if len(values) == 0 {
		return nil, fmt.Errorf("ontology declares no trigger_kind values")
	}
	return values, nil
}

func validateRollbackPlan(doc rawDoc, repoRoot string) []string {
	var errs []string
	allowed, err := triggerKindValues(repoRoot)
	if err != nil {
		return []string{fmt.Sprintf("agent-assurance ontology could not be loaded: %v", err)}
	}
	meta, ok := doc["meta"].(map[string]any)
	if !ok || meta["template_kind"] != "rollback-plan" {
		var actual any
		if ok {
			actual = meta["template_kind"]
		}
		errs = append(errs, fmt.Sprintf("[meta].template_kind is %v; expected 'rollback-plan'.", actual))
	}
	triggers, ok := asArray(doc["triggers"])
	if !ok || len(triggers) == 0 {
		errs = append(errs, "at least one [[triggers]] entry is required.")
		return errs
	}
	for i, raw := range triggers {
		trig, ok := raw.(map[string]any)
		if !ok {
			errs = append(errs, fmt.Sprintf("[[triggers]] #%d: must be a table.", i))
			continue
		}
		trigID, _ := trig["id"].(string)
		if trigID == "" {
			trigID = "<unset>"
		}
		kindValue, _ := trig["trigger_kind"].(string)
		if kindValue == "" {
			kindValue, _ = trig["kind"].(string)
		}
		switch {
		case strings.TrimSpace(kindValue) == "":
			errs = append(errs, fmt.Sprintf("[[triggers]] #%d (id=%q): missing trigger_kind/kind.", i, trigID))
		case !allowed[kindValue]:
			errs = append(errs, fmt.Sprintf("[[triggers]] #%d (id=%q): trigger_kind=%q not in profile ontology vocabulary.", i, trigID, kindValue))
		}
		for _, field := range []string{"id", "metric", "threshold", "action"} {
			if _, present := trig[field]; !present {
				errs = append(errs, fmt.Sprintf("[[triggers]] #%d (id=%q): missing required field '%s'.", i, trigID, field))
			}
		}
	}
	return errs
}

// ----------------------------------------------------------------------------
// SPEC §13 abstraction_class / capability_envelope validation
// ----------------------------------------------------------------------------

var abstractionIDRe = regexp.MustCompile(`^[a-z0-9][a-z0-9._-]*\.v\d+$`)

func loadCapabilityDomains(repoRoot string) (map[string]bool, error) {
	doc, err := loadDoc(filepath.Join(repoRoot, "core/ontology.toml"))
	if err != nil {
		return nil, err
	}
	values := ontologyValues(doc, "capability_envelope.domain")
	if len(values) == 0 {
		return nil, fmt.Errorf("core ontology is missing capability_envelope.domain vocabulary")
	}
	return values, nil
}

func checkAbstractionIJB(table map[string]any, loc string, errs *[]string) {
	if table["ijb_primitive"] != "constraint" {
		*errs = append(*errs, fmt.Sprintf("%s.ijb_primitive: must be 'constraint'", loc))
	}
	if table["ijb_constraint_type"] != "structural" {
		*errs = append(*errs, fmt.Sprintf("%s.ijb_constraint_type: must be 'structural'", loc))
	}
}

func checkNonNegativeInt(table map[string]any, key, loc string, errs *[]string) {
	switch v := table[key].(type) {
	case int64:
		if v >= 0 {
			return
		}
	case int:
		if v >= 0 {
			return
		}
	}
	*errs = append(*errs, fmt.Sprintf("%s.%s: must be a non-negative integer", loc, key))
}

func checkBoolean(table map[string]any, key, loc string, errs *[]string) {
	if _, ok := table[key].(bool); !ok {
		*errs = append(*errs, fmt.Sprintf("%s.%s: must be a boolean", loc, key))
	}
}

func checkStringList(table map[string]any, key, loc string, errs *[]string) {
	values, ok := asArray(table[key])
	if !ok {
		*errs = append(*errs, fmt.Sprintf("%s.%s: must be a list of strings", loc, key))
		return
	}
	for _, value := range values {
		if _, ok := value.(string); !ok {
			*errs = append(*errs, fmt.Sprintf("%s.%s: must be a list of strings", loc, key))
			return
		}
	}
}

func checkCapabilityDomain(name string, table map[string]any, loc string, errs *[]string) {
	if denied, _ := table["denied"].(bool); denied {
		return
	}
	switch name {
	case "filesystem":
		checkStringList(table, "preopens", loc, errs)
		checkBoolean(table, "read_allowed", loc, errs)
		checkBoolean(table, "write_allowed", loc, errs)
		checkBoolean(table, "exec_allowed", loc, errs)
	case "sockets":
		for _, key := range []string{"tcp_allowlist", "udp_allowlist"} {
			if _, present := table[key]; present {
				if b, ok := table[key].(bool); !ok || b {
					checkStringList(table, key, loc, errs)
				}
			}
		}
		if _, present := table["ip_resolve_allowed"]; present {
			checkBoolean(table, "ip_resolve_allowed", loc, errs)
		}
	case "http":
		checkStringList(table, "outgoing_host_allowlist", loc, errs)
		checkNonNegativeInt(table, "max_concurrent_requests", loc, errs)
	case "clocks":
		checkBoolean(table, "wall_clock_allowed", loc, errs)
		checkBoolean(table, "monotonic_clock_allowed", loc, errs)
		if _, present := table["precision_cap_ms"]; present {
			checkNonNegativeInt(table, "precision_cap_ms", loc, errs)
		}
	case "random":
		source, _ := table["entropy_source"].(string)
		if source != "os" && source != "deterministic_seed" && source != "none" {
			*errs = append(*errs, fmt.Sprintf("%s.entropy_source: must be one of ['os', 'deterministic_seed', 'none']", loc))
		}
	case "environment":
		checkStringList(table, "var_allowlist", loc, errs)
	case "process_spawn":
		checkStringList(table, "allowed_programs", loc, errs)
	case "ipc":
		checkBoolean(table, "shared_memory_allowed", loc, errs)
		checkBoolean(table, "fd_passing_allowed", loc, errs)
	case "crypto_keys":
		for _, key := range []string{"read_keys", "use_keys"} {
			if _, present := table[key]; present {
				checkStringList(table, key, loc, errs)
			}
		}
		if _, present := table["generate_allowed"]; present {
			checkBoolean(table, "generate_allowed", loc, errs)
		}
	}
}

func validateAbstractionClass(path string, doc rawDoc, repoRoot string) []string {
	var errs []string
	domains, err := loadCapabilityDomains(repoRoot)
	if err != nil {
		return []string{fmt.Sprintf("core ontology could not be loaded: %v", err)}
	}
	kind, ok := doc["kind"].(map[string]any)
	if !ok {
		return nil
	}
	if ac, ok := kind["abstraction_class"].(map[string]any); ok {
		loc := fmt.Sprintf("%s: [kind.abstraction_class]", path)
		id, _ := ac["id"].(string)
		if id == "" || !abstractionIDRe.MatchString(id) {
			errs = append(errs, fmt.Sprintf("%s.id: must match `<slug>.v<integer>`, got %q", loc, id))
		}
		if desc, _ := ac["description"].(string); desc == "" {
			errs = append(errs, fmt.Sprintf("%s.description: must be a non-empty string", loc))
		}
		checkAbstractionIJB(ac, loc, &errs)
	}
	if ce, ok := kind["capability_envelope"].(map[string]any); ok {
		loc := fmt.Sprintf("%s: [kind.capability_envelope]", path)
		if specVersion, _ := ce["spec_version"].(string); specVersion == "" {
			errs = append(errs, fmt.Sprintf("%s.spec_version: must be a non-empty string", loc))
		}
		checkAbstractionIJB(ce, loc, &errs)
		if cpu, ok := ce["cpu_bounds"].(map[string]any); ok {
			checkNonNegativeInt(cpu, "max_cpu_ms", loc+".cpu_bounds", &errs)
			checkNonNegativeInt(cpu, "max_cpu_percent", loc+".cpu_bounds", &errs)
		} else {
			errs = append(errs, fmt.Sprintf("%s.cpu_bounds: missing required table", loc))
		}
		if mem, ok := ce["memory_bounds"].(map[string]any); ok {
			checkNonNegativeInt(mem, "max_bytes", loc+".memory_bounds", &errs)
		} else {
			errs = append(errs, fmt.Sprintf("%s.memory_bounds: missing required table", loc))
		}
		known := map[string]bool{
			"cpu_bounds": true, "memory_bounds": true, "spec_version": true,
			"ijb_primitive": true, "ijb_constraint_type": true,
		}
		for key, raw := range ce {
			if known[key] {
				continue
			}
			sub, ok := raw.(map[string]any)
			if !ok {
				errs = append(errs, fmt.Sprintf("%s.%s: top-level value must be a sub-table", loc, key))
				continue
			}
			if !domains[key] {
				errs = append(errs, fmt.Sprintf("%s.%s: not a capability domain.", loc, key))
				continue
			}
			checkCapabilityDomain(key, sub, loc+"."+key, &errs)
		}
	}
	return errs
}

// ----------------------------------------------------------------------------
// §2.2 version pins + §2.6 docs + §2.7 confidentiality/license/embargo_until
// ----------------------------------------------------------------------------

var confidentialityClosed = []string{
	"public", "restricted", "confidential", "trade-secret", "embargoed",
}

func validateMeta(path string, doc rawDoc) []string {
	var errs []string
	meta, ok := doc["meta"].(map[string]any)
	if !ok {
		return errs
	}

	if schemaVersion, ok := meta["schema_version"].(string); !ok || !semverRE.MatchString(schemaVersion) {
		errs = append(errs, fmt.Sprintf(
			"%s: [meta].schema_version must be a semver string `MAJOR.MINOR.PATCH`", path))
	}

	if raw, present := meta["ontology_version"]; present && !isPositiveInteger(raw) {
		errs = append(errs, fmt.Sprintf(
			"%s: [meta].ontology_version must be a positive integer snapshot", path))
	}

	if docsURL, ok := meta["docs"].(string); ok {
		if !strings.HasPrefix(docsURL, "https://") {
			errs = append(errs, fmt.Sprintf(
				"%s: [meta].docs must start with `https://` (SPEC §2.6)", path))
		}
		// drop optional fragment, then disallow `?` in the remainder
		stripped := docsURL
		if i := strings.IndexByte(stripped, '#'); i >= 0 {
			stripped = stripped[:i]
		}
		if strings.ContainsRune(stripped, '?') {
			errs = append(errs, fmt.Sprintf(
				"%s: [meta].docs must not contain a query string (SPEC §2.6)", path))
		}
	}

	if raw, present := meta["confidentiality"]; present {
		c, isStr := raw.(string)
		if !isStr {
			errs = append(errs, fmt.Sprintf(
				"%s: [meta].confidentiality, when present, must be a string (SPEC §2.7)", path))
			return errs
		}
		if !stringIn(c, confidentialityClosed) {
			errs = append(errs, fmt.Sprintf(
				"%s: [meta].confidentiality = `%s` is not in the closed set %v (SPEC §2.7)",
				path, c, confidentialityClosed))
		}
		if c == "embargoed" {
			until, hasStr := meta["embargo_until"].(string)
			switch {
			case !hasStr:
				errs = append(errs, fmt.Sprintf(
					"%s: [meta].confidentiality = \"embargoed\" REQUIRES [meta].embargo_until (SPEC §2.7)", path))
			case !isRFC3339DateOrDateTime(until):
				errs = append(errs, fmt.Sprintf(
					"%s: [meta].embargo_until = `%s` does not match RFC 3339 date or date-time syntax (SPEC §2.7)",
					path, until))
			}
		} else if until, hasStr := meta["embargo_until"].(string); hasStr && !isRFC3339DateOrDateTime(until) {
			errs = append(errs, fmt.Sprintf(
				"%s: [meta].embargo_until = `%s` does not match RFC 3339 date or date-time syntax (SPEC §2.7)",
				path, until))
		}
	}

	if raw, present := meta["license"]; present {
		lic, isStr := raw.(string)
		switch {
		case !isStr:
			errs = append(errs, fmt.Sprintf(
				"%s: [meta].license, when present, must be a string (SPEC §2.7)", path))
		case strings.TrimSpace(lic) == "":
			errs = append(errs, fmt.Sprintf(
				"%s: [meta].license, when present, must be a non-empty string", path))
		}
	}
	return errs
}

// isRFC3339DateOrDateTime accepts:
//
//	YYYY-MM-DD                              (full-date)
//	YYYY-MM-DDTHH:MM:SS[.fff][Z|±HH:MM]     (full date-time)
//
// Syntactic check only; SPEC §2.7 forbids the validator from comparing
// against wall-clock time.
var (
	semverRE          = regexp.MustCompile(`^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`)
	rfc3339DateRE     = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}$`)
	rfc3339DateTimeRE = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$`)
)

func isPositiveInteger(v any) bool {
	switch n := v.(type) {
	case int:
		return n > 0
	case int64:
		return n > 0
	case uint64:
		return n > 0
	default:
		return false
	}
}

func isRFC3339DateOrDateTime(s string) bool {
	return rfc3339DateRE.MatchString(s) || rfc3339DateTimeRE.MatchString(s)
}

func stringIn(s string, xs []string) bool {
	for _, x := range xs {
		if x == s {
			return true
		}
	}
	return false
}

// ----------------------------------------------------------------------------
// §11.1 [provenance.encryption]
// ----------------------------------------------------------------------------

var hashIsOverClosed = []string{"plaintext", "ciphertext"}

func validateProvenanceEncryption(path string, doc rawDoc) []string {
	var errs []string
	prov, ok := doc["provenance"].(map[string]any)
	if !ok {
		return errs
	}
	enc, ok := prov["encryption"].(map[string]any)
	if !ok {
		return errs
	}
	sealed, sealedPresent := enc["sealed"].(bool)
	switch {
	case !sealedPresent:
		errs = append(errs, fmt.Sprintf(
			"%s: [provenance.encryption].sealed is required (boolean) when the sub-table is present",
			path))
	case !sealed:
		errs = append(errs, fmt.Sprintf(
			"%s: [provenance.encryption] is present but sealed=false — SPEC §11.1 forbids the sub-table in that case",
			path))
	}
	v, vOK := enc["hash_is_over"].(string)
	if !vOK {
		errs = append(errs, fmt.Sprintf(
			"%s: [provenance.encryption].hash_is_over is required (SPEC §11.1)", path))
	} else if !stringIn(v, hashIsOverClosed) {
		errs = append(errs, fmt.Sprintf(
			"%s: [provenance.encryption].hash_is_over = `%s` is not in %v",
			path, v, hashIsOverClosed))
	}
	if raw, present := enc["scheme_hint"]; present {
		if _, isStr := raw.(string); !isStr {
			errs = append(errs, fmt.Sprintf(
				"%s: [provenance.encryption].scheme_hint, when present, must be a string (SPEC §11.1)", path))
		}
	}
	return errs
}

// ----------------------------------------------------------------------------
// SPEC §12.8 closure_root source-hash subset
// ----------------------------------------------------------------------------

const emptySHA256 = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
const emptySHA384 = "sha384:38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da274edebfe76f65fbd51ad2f14898b95b"
const emptySHA512 = "sha512:cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"

func isLowerHex(s string) bool {
	for _, r := range s {
		if !((r >= '0' && r <= '9') || (r >= 'a' && r <= 'f')) {
			return false
		}
	}
	return true
}

func splitClosureRoot(value string) (string, error) {
	parts := strings.SplitN(value, ":", 2)
	if len(parts) != 2 {
		return "", fmt.Errorf("`closure_root` must match `<algo>:<lowercase-hex-digest>`")
	}
	algo, hexpart := parts[0], parts[1]
	expectedLen := 0
	switch algo {
	case "sha256":
		expectedLen = 64
	case "sha384":
		expectedLen = 96
	case "sha512":
		expectedLen = 128
	case "md5", "sha1":
		return "", fmt.Errorf("`closure_root` uses forbidden weak digest algorithm `%s`. SPEC §12.1 forbids MD5 and SHA-1", algo)
	default:
		return "", fmt.Errorf("`closure_root` uses unknown digest algorithm `%s`", algo)
	}
	if len(hexpart) != expectedLen || !isLowerHex(hexpart) {
		return "", fmt.Errorf("`closure_root` digest must be %d lowercase hex chars for `%s`", expectedLen, algo)
	}
	return algo, nil
}

func sourceHashRecords(path string, doc rawDoc) ([]string, []string) {
	var records []string
	prov, ok := doc["provenance"].(map[string]any)
	if !ok {
		return records, nil
	}
	raw, ok := prov["source_sha256"]
	if !ok {
		return records, nil
	}
	sourceHash, ok := raw.(string)
	if !ok || !strings.HasPrefix(sourceHash, "sha256:") || len(sourceHash) != len("sha256:")+64 || !isLowerHex(sourceHash[len("sha256:"):]) {
		return nil, []string{fmt.Sprintf("%s: `[provenance].source_sha256`, when present, must match `sha256:<64 lowercase hex chars>`", path)}
	}
	records = append(records, fmt.Sprintf("provenance.source_sha256 %s\n", sourceHash))
	sort.Strings(records)
	return records, nil
}

// ----------------------------------------------------------------------------
// SPEC §12.8.1: profile-pinned closure records
// ----------------------------------------------------------------------------
//
// The pin map is keyed by `template_kind` (kind names are
// namespace-partitioned per SPEC §6.1, so a kind maps to at most one
// profile). Built from the discovered profile descriptors, with
// `closure_records` unioned across `extends` like `contained_kinds`.
// Declaration-shape enforcement (INV07) lives in the profile-descriptor
// path; this consumes well-formed declarations.

type pinnedClosureRecord struct {
	field    string
	presence string
	profile  string
}

// loadPinnedRecords returns {template_kind -> sorted [(field,
// presence, profile_name)]} over the discovered descriptor set.
func loadPinnedRecords(descriptors map[string]descriptor) map[string][]pinnedClosureRecord {
	pinMap := map[string][]pinnedClosureRecord{}
	for root := range descriptors {
		seen := map[string]bool{}
		var visit func(node string)
		visit = func(node string) {
			if seen[node] {
				return
			}
			d, ok := descriptors[node]
			if !ok {
				return
			}
			seen[node] = true
			profile, ok := d.doc["profile"].(map[string]any)
			if !ok {
				return
			}
			if arr, ok := asArray(profile["closure_records"]); ok {
				for _, raw := range arr {
					rec, ok := raw.(map[string]any)
					if !ok {
						continue
					}
					kind, kindOK := rec["contained_kind"].(string)
					field, fieldOK := rec["field"].(string)
					presence, presenceOK := rec["presence"].(string)
					if !kindOK || !fieldOK || !presenceOK {
						continue
					}
					if presence != "required" && presence != "when-present" {
						continue
					}
					// Dedup by (field, presence) only: a record
					// inherited through `extends` reaches this map once
					// per extending root, but its record string excludes
					// the profile name, so keying dedup on the profile
					// would double-emit the record and corrupt the
					// digest stream.
					duplicate := false
					for _, existing := range pinMap[kind] {
						if existing.field == field && existing.presence == presence {
							duplicate = true
							break
						}
					}
					if !duplicate {
						pinMap[kind] = append(pinMap[kind], pinnedClosureRecord{field, presence, root})
					}
				}
			}
			if ext, ok := asArray(profile["extends"]); ok {
				for _, child := range ext {
					if s, ok := child.(string); ok {
						visit(s)
					}
				}
			}
		}
		visit(root)
	}
	for _, entries := range pinMap {
		sort.Slice(entries, func(i, j int) bool {
			if entries[i].field != entries[j].field {
				return entries[i].field < entries[j].field
			}
			if entries[i].presence != entries[j].presence {
				return entries[i].presence < entries[j].presence
			}
			return entries[i].profile < entries[j].profile
		})
	}
	return pinMap
}

func walkField(doc rawDoc, dotted string) (any, bool) {
	var current any = doc
	for _, segment := range strings.Split(dotted, ".") {
		table, ok := current.(map[string]any)
		if !ok {
			return nil, false
		}
		value, ok := table[segment]
		if !ok {
			return nil, false
		}
		current = value
	}
	return current, true
}

// pinnedClosureInputs implements SPEC §12.8.1 record emission + pin
// resolution for one document.
//
// Pins resolve by `template_kind` over the full loaded descriptor set,
// in EVERY mode that validates `closure_root`; a document of a pinned
// kind with a missing/unresolvable `framework_profile` is rejected.
// There is no pin-free fall-through for a pinned kind.
func pinnedClosureInputs(path string, doc rawDoc, pinMap map[string][]pinnedClosureRecord, loadedProfiles map[string]bool) ([]string, []string) {
	meta, ok := doc["meta"].(map[string]any)
	if !ok {
		return nil, nil
	}
	// SPEC 2.3: `template_kind` IS a string. Absence is a ratified escape from
	// conformance scope, and so is a non-spec-reserved string value (SPEC 12).
	// A value that is PRESENT but not a string is neither. Reading it as absent
	// drops every pinned closure record for the kind and silently degrades the
	// document to the one-record source-hash closure, which is the pin-free
	// fall-through the comment above says does not exist.
	if raw, present := meta["template_kind"]; present {
		if _, isString := raw.(string); !isString {
			return nil, []string{fmt.Sprintf(
				"%s: `meta.template_kind` is present but is not a string (SPEC 2.3). A "+
					"malformed kind selector MUST NOT be read as an absent one: that drops "+
					"every pinned closure record for the kind and silently degrades the "+
					"document to a one-record source-hash closure", path)}
		}
	}
	templateKind, ok := meta["template_kind"].(string)
	if !ok {
		// legacy synonym
		templateKind, ok = meta["kind"].(string)
	}
	if !ok {
		return nil, nil
	}
	pins, pinned := pinMap[templateKind]
	if !pinned {
		return nil, nil
	}

	var errs []string
	frameworkProfile, fpOK := meta["framework_profile"].(string)
	if !fpOK || frameworkProfile == "" {
		errs = append(errs, fmt.Sprintf(
			"%s: documents of pinned kind `%s` MUST declare `meta.framework_profile` (SPEC §12.8.1 pin resolution)",
			path, templateKind))
	} else if !loadedProfiles[frameworkProfile] {
		errs = append(errs, fmt.Sprintf(
			"%s: `meta.framework_profile` `%s` does not resolve to a loaded profile-descriptor (SPEC §12.8.1 pin resolution; pinned kind `%s`)",
			path, frameworkProfile, templateKind))
	}

	var records []string
	for _, pin := range pins {
		value, present := walkField(doc, pin.field)
		if !present {
			if pin.presence == "required" {
				errs = append(errs, fmt.Sprintf(
					"%s: pinned closure record `%s` (required by profile `%s`, SPEC §12.8.1) is missing",
					path, pin.field, pin.profile))
			}
			continue
		}
		s, isString := value.(string)
		if !isString || !sha256RE.MatchString(s) {
			errs = append(errs, fmt.Sprintf(
				"%s: pinned closure record `%s` must match `sha256:<64 lowercase hex chars>` (SPEC §12.8.1), got %#v",
				path, pin.field, value))
			continue
		}
		records = append(records, fmt.Sprintf("%s %s\n", pin.field, s))
	}
	return records, errs
}

func expectedClosureRoot(algo string, records []string) string {
	stream := strings.Join(records, "")
	switch algo {
	case "sha256":
		sum := sha256.Sum256([]byte(stream))
		return fmt.Sprintf("sha256:%x", sum)
	case "sha384":
		sum := sha512.Sum384([]byte(stream))
		return fmt.Sprintf("sha384:%x", sum)
	case "sha512":
		sum := sha512.Sum512([]byte(stream))
		return fmt.Sprintf("sha512:%x", sum)
	default:
		panic("algorithm checked before digest")
	}
}

func validateClosureRoot(path string, doc rawDoc, pinMap map[string][]pinnedClosureRecord, loadedProfiles map[string]bool) []string {
	raw, ok := doc["closure_root"]
	if !ok {
		return []string{fmt.Sprintf("%s: missing required root-level `closure_root` field (SPEC §12.1)", path)}
	}
	value, ok := raw.(string)
	if !ok || value == "" {
		return []string{fmt.Sprintf("%s: `closure_root` must be a non-empty string", path)}
	}
	algo, err := splitClosureRoot(value)
	if err != nil {
		return []string{fmt.Sprintf("%s: %s", path, err)}
	}
	records, inputErrs := sourceHashRecords(path, doc)
	// SPEC §12.8.1: pinned records join the same sorted record stream
	// as `provenance.source_sha256`; any pin-input error short-circuits
	// before the digest comparison (mirrors the Python reference).
	pinnedRecords, pinnedErrs := pinnedClosureInputs(path, doc, pinMap, loadedProfiles)
	records = append(records, pinnedRecords...)
	inputErrs = append(inputErrs, pinnedErrs...)
	if len(inputErrs) > 0 {
		return inputErrs
	}
	sort.Strings(records)
	expected := expectedClosureRoot(algo, records)
	if value != expected {
		if len(records) == 0 {
			sentinel := expected
			switch algo {
			case "sha256":
				sentinel = emptySHA256
			case "sha384":
				sentinel = emptySHA384
			case "sha512":
				sentinel = emptySHA512
			}
			return []string{fmt.Sprintf("%s: self-contained documents MUST use the canonical empty-closure sentinel `%s`; got `%s`", path, sentinel, value)}
		}
		return []string{fmt.Sprintf("%s: `closure_root` does not match SPEC §12.8 source-hash closure. Expected `%s` from %d canonical source-hash input(s), got `%s`.", path, expected, len(records), value)}
	}
	return nil
}

// ----------------------------------------------------------------------------
// §2.5 framework_profile partition (instance file check)
// ----------------------------------------------------------------------------

func validateFrameworkProfile(path string, doc rawDoc, descriptors map[string]descriptor) []string {
	var errs []string
	meta, ok := doc["meta"].(map[string]any)
	if !ok {
		return errs
	}
	name, ok := meta["framework_profile"].(string)
	if !ok || name == "" {
		return errs
	}
	resolved := name
	if resolved == "AGDF" {
		resolved = "agent-assurance"
	}
	u := unprefixedRE.MatchString(resolved)
	r := reverseDNSRE.MatchString(resolved)
	if !u && !r {
		errs = append(errs, fmt.Sprintf(
			"%s: [meta].framework_profile = `%s` does not match the SPEC §2.5 namespacing partition (must be unprefixed kebab-case or reverse-DNS)",
			path, name))
		return errs
	}
	if u {
		if _, present := descriptors[resolved]; !present {
			errs = append(errs, fmt.Sprintf(
				"%s: [meta].framework_profile = `%s` is an unprefixed (spec-reserved) name but no loaded profile-descriptor declares it (SPEC §2.5)",
				path, name))
		}
	}
	return errs
}

// ----------------------------------------------------------------------------
// §6.1 profile-descriptor
// ----------------------------------------------------------------------------

var requiredProfileFields = []string{
	"name", "namespace", "owner", "license", "extends", "ontology", "contained_kinds",
}

// INV07 (spec.md §12.8.1): profile-pinned closure records.
var (
	closureRecordKeys            = []string{"contained_kind", "field", "presence"}
	closureRecordPresence        = []string{"required", "when-present"}
	closureRecordFieldRE         = regexp.MustCompile(`^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$`)
	closureRecordForbiddenFields = []string{"closure_root", "provenance.source_sha256"}
	postureFields                = []string{"confidentiality", "license", "embargo_until"}
)

func stringInSlice(s string, set []string) bool {
	for _, v := range set {
		if v == s {
			return true
		}
	}
	return false
}

var (
	unprefixedRE = regexp.MustCompile(`^[a-z][a-z0-9-]*$`)
	reverseDNSRE = regexp.MustCompile(`^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+$`)
	sha256RE     = regexp.MustCompile(`^sha256:[0-9a-f]{64}$`)
)

type descriptor struct {
	path string
	doc  rawDoc
}

// discoverDescriptors also reports duplicate profile names: a
// duplicate would let one descriptor shadow another in the name-keyed
// map and silently erase its closure pins, so the caller MUST refuse
// to validate anything when duplicates exist (SPEC 12.8.1 pin
// resolution: no pin-free fall-through). Directory entries are checked
// via os.Stat on the candidate path so symlinked profile directories
// are followed, matching the Rust and Python discovery.
func discoverDescriptors(repoRoot string) (map[string]descriptor, []string) {
	out := map[string]descriptor{}
	var duplicates []string
	root := filepath.Join(repoRoot, "profiles")
	entries, err := os.ReadDir(root)
	if err != nil {
		return out, duplicates
	}
	for _, e := range entries {
		candidate := filepath.Join(root, e.Name(), "PROFILE.toml")
		info, err := os.Stat(candidate)
		if err != nil || info.IsDir() {
			continue
		}
		doc, err := loadDoc(candidate)
		if err != nil {
			continue
		}
		if tk, ok := stringOf(doc["meta"], "template_kind"); !ok || tk != "profile-descriptor" {
			continue
		}
		if name, ok := stringOf(doc["profile"], "name"); ok {
			if existing, dup := out[name]; dup {
				duplicates = append(duplicates, fmt.Sprintf(
					"duplicate profile-descriptor name `%s` (%s and %s)",
					name, existing.path, candidate))
				continue
			}
			out[name] = descriptor{candidate, doc}
		}
	}
	return out, duplicates
}

func checkNamespacePartition(name, namespace string) []string {
	var errs []string
	u := unprefixedRE.MatchString(name)
	r := reverseDNSRE.MatchString(name)
	if !u && !r {
		errs = append(errs, fmt.Sprintf(
			"[profile].name `%s` does not match the SPEC §2.5 namespacing partition", name))
		return errs
	}
	if u {
		if namespace != "spec.reserved" {
			errs = append(errs, fmt.Sprintf(
				"[profile].namespace `%s` is inconsistent with unprefixed name `%s` (SPEC §2.5)",
				namespace, name))
		}
	} else {
		if namespace == "spec.reserved" {
			errs = append(errs, fmt.Sprintf(
				"[profile].namespace = \"spec.reserved\" is not permitted for reverse-DNS name `%s`", name))
		} else if !strings.HasPrefix(name, namespace+".") {
			errs = append(errs, fmt.Sprintf(
				"[profile].namespace `%s` is not a strict reverse-DNS prefix of name `%s` (SPEC §2.5)",
				namespace, name))
		}
	}
	return errs
}

func checkExtendsAcyclic(name string, descriptors map[string]descriptor) []string {
	var errs []string
	visited := map[string]bool{}
	var path []string
	var visit func(n string)
	visit = func(n string) {
		for i, p := range path {
			if p == n {
				cycle := append([]string{}, path[i:]...)
				cycle = append(cycle, n)
				errs = append(errs, "`extends` graph contains a cycle: "+strings.Join(cycle, " -> "))
				return
			}
		}
		if visited[n] {
			return
		}
		visited[n] = true
		d, ok := descriptors[n]
		if !ok {
			return
		}
		profile, ok := d.doc["profile"].(map[string]any)
		if !ok {
			return
		}
		ext, ok := asArray(profile["extends"])
		if !ok {
			return
		}
		path = append(path, n)
		for _, c := range ext {
			if s, ok := c.(string); ok {
				visit(s)
			}
		}
		path = path[:len(path)-1]
	}
	visit(name)
	return errs
}

func kindDescriptorCandidates(repoRoot, slug, profileName string) []string {
	fname := slug + "-kind.toml"
	cands := []string{
		filepath.Join(repoRoot, "profiles", profileName, fname),
		filepath.Join(repoRoot, "core", fname),
	}
	if entries, err := os.ReadDir(filepath.Join(repoRoot, "profiles")); err == nil {
		for _, e := range entries {
			// Stat follows symlinked profile directories (DirEntry.IsDir
			// does not), matching rs/py.
			info, statErr := os.Stat(filepath.Join(repoRoot, "profiles", e.Name()))
			if statErr != nil || !info.IsDir() {
				continue
			}
			cands = append(cands, filepath.Join(repoRoot, "profiles", e.Name(), fname))
		}
	}
	seen := map[string]bool{}
	out := cands[:0]
	for _, c := range cands {
		if !seen[c] {
			seen[c] = true
			out = append(out, c)
		}
	}
	return out
}

// effectiveProfileSets unions `contained_kinds` and `closure_records`
// across the `extends` graph rooted at `name` (spec.md §6.1 rules 3 and
// 4). The root resolves through `descriptors` when discovered there,
// falling back to the profile table of the document under validation
// (mirrors the Python reference, which merges CLI files into the
// discovery set before validating).
func effectiveProfileSets(name string, localProfile map[string]any, descriptors map[string]descriptor) (map[string]bool, []map[string]any) {
	kinds := map[string]bool{}
	var records []map[string]any
	seen := map[string]bool{}
	var visit func(node string)
	visit = func(node string) {
		if seen[node] {
			return
		}
		var profile map[string]any
		if d, ok := descriptors[node]; ok {
			profile, _ = d.doc["profile"].(map[string]any)
		} else if node == name {
			profile = localProfile
		}
		if profile == nil {
			return // unresolved extends entry; INV03 handles it
		}
		seen[node] = true
		if ck, ok := asArray(profile["contained_kinds"]); ok {
			for _, e := range ck {
				if s, ok := e.(string); ok {
					kinds[s] = true
				}
			}
		}
		if recs, ok := asArray(profile["closure_records"]); ok {
			for _, r := range recs {
				if t, ok := r.(map[string]any); ok {
					records = append(records, t)
				}
			}
		}
		if ext, ok := asArray(profile["extends"]); ok {
			for _, c := range ext {
				if s, ok := c.(string); ok {
					visit(s)
				}
			}
		}
	}
	visit(name)
	return kinds, records
}

// checkClosureRecords enforces INV07 (spec.md §12.8.1):
// profile-pinned closure records.
func checkClosureRecords(path, name string, profile map[string]any, descriptors map[string]descriptor) []string {
	var errs []string
	var closureRecords []any
	if raw, present := profile["closure_records"]; present {
		arr, ok := asArray(raw)
		if !ok {
			return []string{fmt.Sprintf(
				"%s: [profile].closure_records must be an array of tables (INV07)", path)}
		}
		closureRecords = arr
	}

	for index, entry := range closureRecords {
		place := fmt.Sprintf("%s: [[profile.closure_records]] entry %d", path, index)
		table, ok := entry.(map[string]any)
		if !ok {
			errs = append(errs, fmt.Sprintf("%s must be a table (INV07)", place))
			continue
		}
		var unknown []string
		for k := range table {
			if !stringInSlice(k, closureRecordKeys) {
				unknown = append(unknown, k)
			}
		}
		if len(unknown) > 0 {
			sort.Strings(unknown)
			errs = append(errs, fmt.Sprintf(
				"%s carries unknown keys %v (INV07: exactly contained_kind / field / presence)",
				place, unknown))
		}
		badShape := false
		for _, key := range closureRecordKeys {
			if s, ok := table[key].(string); !ok || s == "" {
				errs = append(errs, fmt.Sprintf(
					"%s.%s must be a non-empty string (INV07)", place, key))
				badShape = true
			}
		}
		if badShape {
			continue
		}

		field, _ := table["field"].(string)
		presence, _ := table["presence"].(string)
		if !closureRecordFieldRE.MatchString(field) {
			errs = append(errs, fmt.Sprintf(
				"%s.field `%s` does not match the frozen path grammar ^[A-Za-z0-9_-]+(\\.[A-Za-z0-9_-]+)*$ (INV07)",
				place, field))
		} else if stringInSlice(field, closureRecordForbiddenFields) ||
			strings.SplitN(field, ".", 2)[0] == "meta" ||
			stringInSlice(field, postureFields) {
			errs = append(errs, fmt.Sprintf(
				"%s.field `%s` is a forbidden pin target (INV07: not closure_root, not provenance.source_sha256, no meta.* path, no §12.9 posture field)",
				place, field))
		}
		if !stringInSlice(presence, closureRecordPresence) {
			errs = append(errs, fmt.Sprintf(
				"%s.presence `%s` must be one of %v (INV07)",
				place, presence, closureRecordPresence))
		}
	}

	effectiveKinds, effectiveRecords := effectiveProfileSets(name, profile, descriptors)

	for index, entry := range closureRecords {
		table, ok := entry.(map[string]any)
		if !ok {
			continue
		}
		if ck, ok := table["contained_kind"].(string); ok && ck != "" && !effectiveKinds[ck] {
			errs = append(errs, fmt.Sprintf(
				"%s: [[profile.closure_records]] entry %d.contained_kind `%s` is not in the post-extends-union contained_kinds (INV07)",
				path, index, ck))
		}
	}

	type pinPair struct{ ck, field string }
	var pairs []pinPair
	for _, rec := range effectiveRecords {
		ck, ckOK := rec["contained_kind"].(string)
		fld, fldOK := rec["field"].(string)
		if ckOK && fldOK {
			pairs = append(pairs, pinPair{ck, fld})
		}
	}
	counts := map[pinPair]int{}
	for _, p := range pairs {
		counts[p]++
	}
	var duplicates []pinPair
	for p, n := range counts {
		if n > 1 {
			duplicates = append(duplicates, p)
		}
	}
	sort.Slice(duplicates, func(i, j int) bool {
		if duplicates[i].ck != duplicates[j].ck {
			return duplicates[i].ck < duplicates[j].ck
		}
		return duplicates[i].field < duplicates[j].field
	})
	for _, p := range duplicates {
		errs = append(errs, fmt.Sprintf(
			"%s: duplicate closure-record pin (`%s`, `%s`) after the extends union (INV07)",
			path, p.ck, p.field))
	}

	return errs
}

func validateProfileDescriptor(path string, doc rawDoc, repoRoot string, descriptors map[string]descriptor) []string {
	var errs []string
	meta, ok := doc["meta"].(map[string]any)
	if !ok {
		return []string{fmt.Sprintf("%s: missing [meta]", path)}
	}
	if tk, _ := meta["template_kind"].(string); tk != "profile-descriptor" {
		return []string{fmt.Sprintf("%s: meta.template_kind must equal \"profile-descriptor\" (got %q)", path, tk)}
	}
	profile, ok := doc["profile"].(map[string]any)
	if !ok {
		return []string{fmt.Sprintf("%s: missing [profile]", path)}
	}
	for _, f := range requiredProfileFields {
		if _, present := profile[f]; !present {
			errs = append(errs, fmt.Sprintf("%s: [profile].%s is required", path, f))
		}
	}
	if len(errs) > 0 {
		return errs
	}
	name, _ := profile["name"].(string)
	namespace, _ := profile["namespace"].(string)
	if name == "" {
		errs = append(errs, fmt.Sprintf("%s: [profile].name must be a non-empty string", path))
	}
	if namespace == "" {
		errs = append(errs, fmt.Sprintf("%s: [profile].namespace must be a non-empty string", path))
	}
	for _, e := range checkNamespacePartition(name, namespace) {
		errs = append(errs, fmt.Sprintf("%s: %s", path, e))
	}
	for _, e := range checkExtendsAcyclic(name, descriptors) {
		errs = append(errs, fmt.Sprintf("%s: %s", path, e))
	}
	if ext, ok := asArray(profile["extends"]); ok {
		for _, e := range ext {
			s, ok := e.(string)
			if !ok {
				errs = append(errs, fmt.Sprintf("%s: [profile].extends entries must be strings", path))
				continue
			}
			if _, found := descriptors[s]; !found {
				errs = append(errs, fmt.Sprintf(
					"%s: [profile].extends entry `%s` does not resolve to a loaded profile-descriptor",
					path, s))
			}
		}
	}
	if ontologyRel, ok := profile["ontology"].(string); ok {
		full := filepath.Join(repoRoot, ontologyRel)
		info, err := os.Stat(full)
		if err != nil || info.IsDir() {
			errs = append(errs, fmt.Sprintf(
				"%s: [profile].ontology path does not resolve to a file (%s)", path, full))
		} else if ont, err := loadDoc(full); err == nil {
			if tk, _ := stringOf(ont["meta"], "template_kind"); tk != "ontology" {
				errs = append(errs, fmt.Sprintf(
					"%s: [profile].ontology (%s) does not declare template_kind = \"ontology\"",
					path, ontologyRel))
			}
		} else {
			errs = append(errs, fmt.Sprintf("%s: ontology parse failure: %v", path, err))
		}
	}
	if ck, ok := asArray(profile["contained_kinds"]); ok {
		for _, e := range ck {
			slug, ok := e.(string)
			if !ok || slug == "" {
				errs = append(errs, fmt.Sprintf(
					"%s: [profile].contained_kinds entries must be non-empty strings", path))
				continue
			}
			matched := false
			for _, c := range kindDescriptorCandidates(repoRoot, slug, name) {
				if info, err := os.Stat(c); err != nil || info.IsDir() {
					continue
				}
				kd, err := loadDoc(c)
				if err != nil {
					continue
				}
				tk, _ := stringOf(kd["meta"], "template_kind")
				dk, _ := stringOf(kd["meta"], "describes_kind")
				if tk == "kind-descriptor" && dk == slug {
					matched = true
					break
				}
			}
			if !matched {
				errs = append(errs, fmt.Sprintf(
					"%s: [profile].contained_kinds entry `%s` does not resolve to a *-kind.toml with matching describes_kind",
					path, slug))
			}
		}
	}
	// INV07: profile-pinned closure records (spec.md §12.8.1)
	errs = append(errs, checkClosureRecords(path, name, profile, descriptors)...)
	return errs
}

// ----------------------------------------------------------------------------
// Disclosure profile (3 kinds)
// ----------------------------------------------------------------------------

type vocab struct {
	values     []string
	extensible bool
}

func loadDisclosureVocabs(repoRoot string) map[string]vocab {
	out := map[string]vocab{}
	doc, err := loadDoc(filepath.Join(repoRoot, "profiles/disclosure/ontology.toml"))
	if err != nil {
		return out
	}
	arr, ok := asArray(doc["attribute_vocabularies"])
	if !ok {
		return out
	}
	for _, entry := range arr {
		t, ok := entry.(map[string]any)
		if !ok {
			continue
		}
		attr, ok := t["attribute"].(string)
		if !ok {
			continue
		}
		v := vocab{}
		if vs, ok := asArray(t["values"]); ok {
			for _, x := range vs {
				if s, ok := x.(string); ok {
					v.values = append(v.values, s)
				}
			}
		}
		if e, ok := t["extensible"].(bool); ok {
			v.extensible = e
		}
		out[attr] = v
	}
	return out
}

func checkVocab(attribute string, value *string, vocabs map[string]vocab, location string) []string {
	v, ok := vocabs[attribute]
	if !ok {
		return []string{fmt.Sprintf(
			"%s: ontology missing attribute_vocabulary `%s` (cannot enforce closure)",
			location, attribute)}
	}
	if value == nil {
		return []string{fmt.Sprintf("%s: `%s` must be a string", location, attribute)}
	}
	for _, x := range v.values {
		if x == *value {
			return nil
		}
	}
	if v.extensible {
		return nil
	}
	return []string{fmt.Sprintf(
		"%s: `%s = %q` is not in the closed vocabulary %v",
		location, attribute, *value, v.values)}
}

func validateDisclosure(path string, doc rawDoc, repoRoot string) []string {
	vocabs := loadDisclosureVocabs(repoRoot)
	meta, _ := doc["meta"].(map[string]any)
	tk, _ := meta["template_kind"].(string)
	switch tk {
	case "disclosure-attestation":
		return validateAttestation(path, doc, meta, vocabs)
	case "redaction-manifest":
		return validateRedaction(path, doc, vocabs)
	case "selective-disclosure-proof":
		return validateProof(path, doc, vocabs)
	}
	return []string{fmt.Sprintf("%s: template_kind %q is not a disclosure-profile kind", path, tk)}
}

func validateAttestation(path string, doc rawDoc, meta map[string]any, vocabs map[string]vocab) []string {
	var errs []string
	embargo, _ := meta["embargo_until"].(string)
	arr, ok := asArray(doc["attestations"])
	if !ok || len(arr) == 0 {
		return []string{fmt.Sprintf("%s: at least one [[attestations]] entry required", path)}
	}
	for i, e := range arr {
		t, ok := e.(map[string]any)
		if !ok {
			errs = append(errs, fmt.Sprintf("%s:attestations[%d]: must be a table", path, i))
			continue
		}
		loc := fmt.Sprintf("%s:attestations[%d]", path, i)
		id, _ := t["id"].(string)
		if !strings.HasPrefix(id, "DISC:") {
			errs = append(errs, fmt.Sprintf("%s: `id` must start with `DISC:`", loc))
		}
		var posturePtr *string
		if posture, ok := t["disclosure_posture"].(string); ok {
			posturePtr = &posture
		}
		errs = append(errs, checkVocab("disclosure_posture", posturePtr, vocabs,
			loc+".disclosure_posture")...)
		if posturePtr != nil && *posturePtr == "partial" {
			ok := false
			if arr, isArr := asArray(t["covered_by"]); isArr {
				for _, v := range arr {
					if s, ok2 := v.(string); ok2 && strings.HasPrefix(s, "RED:") {
						ok = true
						break
					}
				}
			}
			if !ok {
				errs = append(errs, fmt.Sprintf(
					"%s: `disclosure_posture = \"partial\"` requires at least one `covered_by` entry referencing a `RED:` id",
					loc))
			}
		}
		if posturePtr != nil && *posturePtr == "embargoed" && embargo == "" {
			errs = append(errs, fmt.Sprintf(
				"%s: `disclosure_posture = \"embargoed\"` requires `[meta].embargo_until` (SPEC §2.7)",
				loc))
		}
	}
	return errs
}

func validateRedaction(path string, doc rawDoc, vocabs map[string]vocab) []string {
	var errs []string
	arr, ok := asArray(doc["redactions"])
	if !ok || len(arr) == 0 {
		return []string{fmt.Sprintf("%s: at least one [[redactions]] entry required", path)}
	}
	for i, e := range arr {
		t, ok := e.(map[string]any)
		if !ok {
			errs = append(errs, fmt.Sprintf("%s:redactions[%d]: must be a table", path, i))
			continue
		}
		loc := fmt.Sprintf("%s:redactions[%d]", path, i)
		id, _ := t["id"].(string)
		if !strings.HasPrefix(id, "RED:") {
			errs = append(errs, fmt.Sprintf("%s: `id` must start with `RED:`", loc))
		}
		var methodPtr, reasonPtr *string
		if m, ok := t["redaction_method"].(string); ok {
			methodPtr = &m
		}
		if r, ok := t["redaction_reason"].(string); ok {
			reasonPtr = &r
		}
		errs = append(errs, checkVocab("redaction_method", methodPtr, vocabs, loc+".redaction_method")...)
		errs = append(errs, checkVocab("redaction_reason", reasonPtr, vocabs, loc+".redaction_reason")...)
		if reasonPtr != nil && *reasonPtr == "other" {
			notes, _ := t["notes"].(string)
			if strings.TrimSpace(notes) == "" {
				errs = append(errs, fmt.Sprintf(
					"%s: `redaction_reason = \"other\"` requires a non-empty `notes` field", loc))
			}
		}
	}
	return errs
}

func validateProof(path string, doc rawDoc, vocabs map[string]vocab) []string {
	var errs []string
	arr, ok := asArray(doc["proofs"])
	if !ok || len(arr) == 0 {
		return []string{fmt.Sprintf("%s: at least one [[proofs]] entry required", path)}
	}
	for i, e := range arr {
		t, ok := e.(map[string]any)
		if !ok {
			errs = append(errs, fmt.Sprintf("%s:proofs[%d]: must be a table", path, i))
			continue
		}
		loc := fmt.Sprintf("%s:proofs[%d]", path, i)
		id, _ := t["id"].(string)
		if !strings.HasPrefix(id, "SDP:") {
			errs = append(errs, fmt.Sprintf("%s: `id` must start with `SDP:`", loc))
		}
		bound, _ := t["bound_source"].(string)
		if !sha256RE.MatchString(bound) {
			errs = append(errs, fmt.Sprintf(
				"%s: `bound_source` must match `^sha256:[0-9a-f]{64}$` (got %q)", loc, bound))
		}
		var schemePtr *string
		if s, ok := t["proof_scheme"].(string); ok {
			schemePtr = &s
		}
		errs = append(errs, checkVocab("proof_scheme", schemePtr, vocabs, loc+".proof_scheme")...)
		if cv, ok := asArray(t["covers"]); ok {
			for ci, c := range cv {
				s, ok := c.(string)
				if !ok {
					errs = append(errs, fmt.Sprintf("%s.covers[%d]: must be a string", loc, ci))
					continue
				}
				if !strings.HasPrefix(s, "RED:") {
					errs = append(errs, fmt.Sprintf(
						"%s.covers[%d]: every entry must start with `RED:` (got %q)", loc, ci, s))
				}
			}
		}
	}
	return errs
}

// ----------------------------------------------------------------------------
// Driver
// ----------------------------------------------------------------------------

func main() {
	var (
		repoRoot string
		modeStr  string
	)
	flag.StringVar(&repoRoot, "repo-root", "", "Repository root (required)")
	flag.StringVar(&modeStr, "mode", "auto", "Validation mode (auto|profile|disclosure|provenance|meta|gate-decision|kind-descriptor|ijb|provenance-binding|implementation-dag|traceability|review-readiness|cost-record|rollback-plan|abstraction-class)")
	flag.Parse()

	if repoRoot == "" {
		fmt.Fprintln(os.Stderr, "error: --repo-root is required")
		os.Exit(2)
	}
	files := flag.Args()
	if len(files) == 0 {
		fmt.Fprintln(os.Stderr, "error: at least one input file is required")
		os.Exit(2)
	}
	m, err := parseMode(modeStr)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(2)
	}
	root, err := filepath.Abs(repoRoot)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error: resolving repo root:", err)
		os.Exit(2)
	}
	descriptors, duplicateProfiles := discoverDescriptors(root)
	if len(duplicateProfiles) > 0 {
		fmt.Fprintln(os.Stderr, "DAGTOML VALIDATION FAILED (go primary)")
		for _, d := range duplicateProfiles {
			fmt.Fprintf(os.Stderr, "- %s: pin resolution refuses to proceed (SPEC 12.8.1)\n", d)
		}
		os.Exit(1)
	}
	// SPEC §12.8.1: build the profile-pinned closure-record map and the
	// loaded-profile-name set once per run; both feed closure_root
	// validation in every mode that runs it.
	pinMap := loadPinnedRecords(descriptors)
	loadedProfiles := make(map[string]bool, len(descriptors))
	for name := range descriptors {
		loadedProfiles[name] = true
	}

	var allErrors []string
	for _, path := range files {
		doc, err := loadDoc(path)
		if err != nil {
			allErrors = append(allErrors, err.Error())
			continue
		}
		var errs []string
		tk, _ := stringOf(doc["meta"], "template_kind")
		if m == modeAuto || m == modeMeta {
			errs = append(errs, validateMeta(path, doc)...)
			errs = append(errs, validateFrameworkProfile(path, doc, descriptors)...)
		}
		if m == modeAuto || m == modeProvenance {
			errs = append(errs, validateProvenanceEncryption(path, doc)...)
			errs = append(errs, validateClosureRoot(path, doc, pinMap, loadedProfiles)...)
		}
		if m == modeAuto || m == modeProvenanceBinding {
			errs = append(errs, validateProvenanceBinding(path, doc, root)...)
		}
		switch m {
		case modeAuto:
			switch tk {
			case "profile-descriptor":
				errs = append(errs, validateProfileDescriptor(path, doc, root, descriptors)...)
				errs = append(errs, validateIJB(path, doc, root)...)
			case "kind-descriptor", "ontology":
				if tk == "kind-descriptor" {
					errs = append(errs, validateKindDescriptor(path, doc, root, true)...)
					errs = append(errs, validateAbstractionClass(path, doc, root)...)
				}
				errs = append(errs, validateIJB(path, doc, root)...)
			case "implementation-dag":
				errs = append(errs, validateImplementationDag(path, doc)...)
				errs = append(errs, validateIJB(path, doc, root)...)
			case "traceability":
				errs = append(errs, validateTraceability(path, doc)...)
				errs = append(errs, validateIJB(path, doc, root)...)
			case "readiness-gate", "contract-declaration", "evidence-matrix":
				errs = append(errs, validateReviewReadiness(path, doc)...)
				errs = append(errs, validateIJB(path, doc, root)...)
			case "cost-record":
				errs = append(errs, validateCostRecord(path, doc, root)...)
				errs = append(errs, validateIJB(path, doc, root)...)
			case "rollback-plan":
				errs = append(errs, validateRollbackPlan(doc, root)...)
				errs = append(errs, validateIJB(path, doc, root)...)
			case "disclosure-attestation", "redaction-manifest", "selective-disclosure-proof":
				errs = append(errs, validateDisclosure(path, doc, root)...)
				errs = append(errs, validateIJB(path, doc, root)...)
			case "gate-decision":
				errs = append(errs, validateGateDecision(path, doc, root)...)
				errs = append(errs, validateIJB(path, doc, root)...)
			case "state-mutation", "mutation-claim":
				errs = append(errs, validateMutationKinds(path, doc, root)...)
				errs = append(errs, validateIJB(path, doc, root)...)
			case "":
			default:
				errs = append(errs, validateIJB(path, doc, root)...)
			}
		case modeProfile:
			errs = append(errs, validateProfileDescriptor(path, doc, root, descriptors)...)
		case modeDisclosure:
			errs = append(errs, validateDisclosure(path, doc, root)...)
		case modeGateDecision:
			errs = append(errs, validateGateDecision(path, doc, root)...)
		case modeMutationKinds:
			errs = append(errs, validateMutationKinds(path, doc, root)...)
		case modeKindDescriptor:
			errs = append(errs, validateKindDescriptor(path, doc, root, true)...)
			errs = append(errs, validateAbstractionClass(path, doc, root)...)
		case modeIJB:
			errs = append(errs, validateIJB(path, doc, root)...)
		case modeImplementationDag:
			errs = append(errs, validateImplementationDag(path, doc)...)
		case modeTraceability:
			errs = append(errs, validateTraceability(path, doc)...)
		case modeReviewReadiness:
			errs = append(errs, validateReviewReadiness(path, doc)...)
		case modeCostRecord:
			errs = append(errs, validateCostRecord(path, doc, root)...)
		case modeRollbackPlan:
			errs = append(errs, validateRollbackPlan(doc, root)...)
		case modeAbstractionClass:
			errs = append(errs, validateAbstractionClass(path, doc, root)...)
		}
		if len(errs) > 0 {
			allErrors = append(allErrors, fmt.Sprintf("--- %s ---", path))
			allErrors = append(allErrors, errs...)
		}
	}

	if len(allErrors) > 0 {
		fmt.Fprintln(os.Stderr, "DAGTOML VALIDATION FAILED (go primary)")
		// stable order is helpful for diff-based investigation
		stable := make([]string, len(allErrors))
		copy(stable, allErrors)
		// (preserve original ordering — only sort for non-grouped sets)
		_ = sort.SliceStable
		for _, line := range stable {
			fmt.Fprintln(os.Stderr, "-", line)
		}
		os.Exit(1)
	}
	fmt.Println("DAGTOML VALIDATION PASSED (go primary)")
	fmt.Printf("- files validated: %d\n", len(files))
	fmt.Printf("- profiles in resolution set: %d\n", len(descriptors))
}

// ----------------------------------------------------------------------------
// Gate-decision profile (agent-assurance gate-decision-kind)
// Enforces INV01..INV06 from profiles/agent-assurance/gate-decision-kind.toml.
// The load-bearing invariant is INV06: when decision.subject_class =
// "self-modification", the deciding model's provider_id AND model_family_id
// MUST both differ from the proposing model's (conjunctive AND).
//
// Mirrors validators/validate_gate_decision.py (Python reference) and the
// `gate_decision` module in tools/dagtoml-validate-rs/src/main.rs. CI runs
// all three; divergence is a build break.
// ----------------------------------------------------------------------------

var (
	gdHex64Re     = regexp.MustCompile(`^[0-9a-f]{64}$`)
	gdAssertionRe = regexp.MustCompile(`^A-[A-Za-z0-9][A-Za-z0-9_-]*$`)
	gdObservedRe  = regexp.MustCompile(`^A-[A-Za-z0-9][A-Za-z0-9_-]*\s*=\s*observed\([^)]+\)\s*$`)
)

// gdRawArray normalises an array value from BurntSushi/toml's dynamic
// decoder into a flat []any WITHOUT dropping non-table elements. The Rust
// reference (tools/dagtoml-validate-rs/src/main.rs gate_decision) iterates
// the raw TOML array so that INV01's emptiness test sees every element and
// INV02/INV03 can report a non-table entry as a violation. A previous
// table-only normaliser silently discarded scalar elements, which let a
// `verdict = "pass"` document carrying `failed_constraint_refs = ["A-1"]`
// (an array of strings) pass INV01 in Go while Rust rejected it — a
// cross-implementation divergence on the separation-of-duty gate. Keep the
// element type intact; the INV loops decide table-vs-not per element.
func gdRawArray(v any) []any {
	switch x := v.(type) {
	case []any:
		return x
	case []map[string]any:
		out := make([]any, len(x))
		for i := range x {
			out[i] = x[i]
		}
		return out
	case []string:
		out := make([]any, len(x))
		for i := range x {
			out[i] = x[i]
		}
		return out
	}
	return nil
}

func loadGateDecisionVocab(repoRoot, attribute string) []string {
	path := filepath.Join(repoRoot, "profiles/agent-assurance/ontology.toml")
	doc, err := loadDoc(path)
	if err != nil {
		return nil
	}
	// BurntSushi/toml decodes [[array_of_tables]] into either []any (whose
	// elements are map[string]any) or []map[string]any depending on the
	// declared destination type. We accept either shape.
	var entries []map[string]any
	switch v := doc["attribute_vocabularies"].(type) {
	case []map[string]any:
		entries = v
	case []any:
		for _, e := range v {
			if m, ok := e.(map[string]any); ok {
				entries = append(entries, m)
			}
		}
	default:
		return nil
	}
	for _, t := range entries {
		if a, _ := t["attribute"].(string); a == attribute {
			var rawValues []any
			switch vv := t["values"].(type) {
			case []any:
				rawValues = vv
			case []string:
				return append([]string(nil), vv...)
			default:
				return nil
			}
			out := make([]string, 0, len(rawValues))
			for _, v := range rawValues {
				if s, ok := v.(string); ok {
					out = append(out, s)
				}
			}
			return out
		}
	}
	return nil
}

func gdVocabContains(values []string, v string) bool {
	for _, x := range values {
		if x == v {
			return true
		}
	}
	return false
}

// Kind-layer invariants for the com.verivus.runtime mutation kinds.
//
// Ported from validators/validate_state_mutation.py to close the
// primary-parity gap recorded against RKM02/RKM03/RKM04/RKM06 and RKC02.
// Before this port a primary-only consumer accepted a hollow proof (the two
// pinned digests with no scheme, finality or locator), because the closure
// layer sees pins and nothing else.

// boundTupleFields is the SPEC 12.8.2 tuple. Values are PREHASHED, never
// inlined: an inlined value carrying 0x0A forges a different field assignment
// with an identical digest.
var boundTupleFields = [][2]string{
	{"mutation.target_id", "target_id"},
	{"mutation.operation", "operation"},
	{"mutation.authorization_sha256", "authorization_sha256"},
	{"mutation.effect_sha256", "effect_sha256"},
	{"mutation.performed_at", "performed_at"},
}

var allowedMutationKeys = map[string]bool{
	"performed_at": true, "target_id": true, "operation": true,
	"authorization_sha256": true, "effect_sha256": true,
}

var allowedProofKeys = map[string]bool{
	"scheme": true, "finality_basis": true, "proof_sha256": true,
	"binds_sha256": true, "proof_locator": true,
}

var requiredProofKeys = []string{
	"scheme", "finality_basis", "proof_sha256", "binds_sha256", "proof_locator",
}

// schemeFinality carries RKM06: a scheme may only claim durability its own
// evidence class can carry.
var schemeFinality = map[string][]string{
	"ledger-transaction": {"none", "ledger-confirmed", "ledger-final"},
	"zk-receipt":         {"none", "ledger-confirmed", "ledger-final"},
	"provider-receipt":   {"none", "provider-acknowledged"},
	"tee-quote":          {"none"},
}

// finalityValues is the closed `finality_basis` vocabulary, mirroring the
// profile ontology.
var finalityValues = map[string]bool{
	"none":                  true,
	"provider-acknowledged": true,
	"ledger-confirmed":      true,
	"ledger-final":          true,
}

func daysInMonth(year, month int) int {
	switch month {
	case 2:
		if year%4 == 0 && (year%100 != 0 || year%400 == 0) {
			return 29
		}
		return 28
	case 4, 6, 9, 11:
		return 30
	}
	return 31
}

func isMutationDigest(s string) bool {
	for _, p := range [][2]any{{"sha256:", 64}, {"sha384:", 96}, {"sha512:", 128}} {
		prefix := p[0].(string)
		n := p[1].(int)
		if strings.HasPrefix(s, prefix) {
			hexPart := s[len(prefix):]
			if len(hexPart) != n {
				return false
			}
			for _, c := range hexPart {
				if !((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f')) {
					return false
				}
			}
			return true
		}
	}
	return false
}

// isRFC3339UTC accepts YYYY-MM-DDTHH:MM:SS[.frac]Z. Hand-rolled to match the
// Rust primary byte for byte rather than relying on time.Parse leniency.
func isRFC3339UTC(s string) bool {
	if len(s) < 20 || s[len(s)-1] != 'Z' {
		return false
	}
	digits := func(a, b int) bool {
		for i := a; i < b; i++ {
			if s[i] < '0' || s[i] > '9' {
				return false
			}
		}
		return true
	}
	if !(digits(0, 4) && s[4] == '-' && digits(5, 7) && s[7] == '-' && digits(8, 10)) {
		return false
	}
	if !(s[10] == 'T' && digits(11, 13) && s[13] == ':' && digits(14, 16) &&
		s[16] == ':' && digits(17, 19)) {
		return false
	}
	if len(s) != 20 &&
		!(s[19] == '.' && len(s) <= 30 && len(s)-21 >= 1 && digits(20, len(s)-1)) {
		return false
	}
	// Calendar validity, not merely digit positions: the shape check alone
	// accepts `2026-99-26T10:15:00Z`, and performed_at is a member of the
	// RKM04 bound tuple carrying the freshness claim.
	num := func(a, b int) int {
		n := 0
		for i := a; i < b; i++ {
			n = n*10 + int(s[i]-'0')
		}
		return n
	}
	year, month, day := num(0, 4), num(5, 7), num(8, 10)
	hour, minute, second := num(11, 13), num(14, 16), num(17, 19)
	if month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month) {
		return false
	}
	// Second 60 is a leap second, which RFC3339 5.6 permits.
	return hour <= 23 && minute <= 59 && second <= 60
}

func isOperationToken(s string) bool {
	if len(s) == 0 || len(s) > 64 {
		return false
	}
	c0 := s[0]
	if !((c0 >= 'a' && c0 <= 'z') || (c0 >= '0' && c0 <= '9')) {
		return false
	}
	for i := 0; i < len(s); i++ {
		c := s[i]
		if !((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '.' || c == '_' || c == '-') {
			return false
		}
	}
	return true
}

// isURIShaped: scheme:rest, no whitespace or control characters, bounded.
// A locator names where a proof lives; it is never a place to inline one.
func isURIShaped(s string) bool {
	colon := strings.Index(s, ":")
	if colon <= 0 {
		return false
	}
	scheme, rest := s[:colon], s[colon+1:]
	if len(rest) == 0 || len(rest) > 480 {
		return false
	}
	if scheme[0] < 'a' || scheme[0] > 'z' {
		return false
	}
	for i := 1; i < len(scheme); i++ {
		c := scheme[i]
		if !((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '+' || c == '.' || c == '-') {
			return false
		}
	}
	for _, r := range rest {
		if unicode.IsSpace(r) || unicode.IsControl(r) || r == 0x7f {
			return false
		}
	}
	return true
}

func mutationBoundTuple(mutation map[string]any) string {
	records := make([]string, 0, len(boundTupleFields))
	for _, f := range boundTupleFields {
		value, _ := stringOf(mutation, f[1])
		vd := sha256.Sum256([]byte(value))
		records = append(records, fmt.Sprintf("%s sha256:%s\n", f[0], hex.EncodeToString(vd[:])))
	}
	sort.Strings(records)
	sum := sha256.Sum256([]byte(strings.Join(records, "")))
	return "sha256:" + hex.EncodeToString(sum[:])
}

func checkMutationTable(path string, doc rawDoc, defects *[]string) {
	mutation, ok := tableOf(doc, "mutation")
	if !ok {
		if hasKey(doc, "mutation") {
			*defects = append(*defects, fmt.Sprintf(
				"%s: `mutation` is present but is not a table. A present-but-wrong-typed "+
					"element MUST NOT be reported as absent (SPEC 12.8.2)", path))
		} else {
			*defects = append(*defects, fmt.Sprintf(
				"%s: missing required `[mutation]` table", path))
		}
		return
	}
	keys := make([]string, 0, len(mutation))
	for k := range mutation {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		if !allowedMutationKeys[k] {
			*defects = append(*defects, fmt.Sprintf(
				"%s: mutation.%s is not a permitted key (closed key set; payloads and "+
					"credentials have no field to live in)", path, k))
		}
	}
	for _, k := range []string{"authorization_sha256", "effect_sha256"} {
		v, state := fieldOf(mutation, k)
		switch {
		case state == fieldAbsent:
			*defects = append(*defects, fmt.Sprintf("%s: mutation.%s is required", path, k))
		case state == fieldNotString:
			*defects = append(*defects, fmt.Sprintf(
				"%s: mutation.%s must be a string carrying a digest scalar", path, k))
		case !isMutationDigest(v):
			*defects = append(*defects, fmt.Sprintf(
				"%s: mutation.%s %q is not a digest scalar", path, k, v))
		}
	}
	switch v, state := fieldOf(mutation, "performed_at"); {
	case state == fieldAbsent:
		*defects = append(*defects, fmt.Sprintf("%s: mutation.performed_at is required", path))
	case state == fieldNotString:
		*defects = append(*defects, fmt.Sprintf(
			"%s: mutation.performed_at must be a string", path))
	case !isRFC3339UTC(v):
		*defects = append(*defects, fmt.Sprintf(
			"%s: mutation.performed_at %q must be an RFC3339 UTC timestamp ending in Z, naming "+
				"a real instant", path, v))
	}
	switch v, state := fieldOf(mutation, "operation"); {
	case state == fieldAbsent:
		*defects = append(*defects, fmt.Sprintf("%s: mutation.operation is required", path))
	case state == fieldNotString:
		*defects = append(*defects, fmt.Sprintf("%s: mutation.operation must be a string", path))
	case !isOperationToken(v):
		*defects = append(*defects, fmt.Sprintf(
			"%s: mutation.operation %q must be a bare lowercase token, at most 64 characters",
			path, v))
	}
	switch v, state := fieldOf(mutation, "target_id"); {
	case state == fieldAbsent:
		*defects = append(*defects, fmt.Sprintf("%s: mutation.target_id is required", path))
	case state == fieldNotString:
		*defects = append(*defects, fmt.Sprintf("%s: mutation.target_id must be a string", path))
	case !isURIShaped(v):
		*defects = append(*defects, fmt.Sprintf(
			"%s: mutation.target_id %q must be a URI or URN with no whitespace or control "+
				"characters", path, v))
	}
	prov, ok := tableOf(doc, "provenance")
	if !ok {
		*defects = append(*defects, fmt.Sprintf(
			"%s: missing required `[provenance]` table; provenance.source_sha256 is a required "+
				"field of this kind", path))
		return
	}
	if v, present := stringOf(prov, "source_sha256"); !present || !isMutationDigest(v) {
		*defects = append(*defects, fmt.Sprintf(
			"%s: provenance.source_sha256 is required and MUST be a digest scalar", path))
	}
}

func validateMutationKinds(path string, doc rawDoc, repoRoot string) []string {
	var defects []string
	meta, ok := tableOf(doc, "meta")
	if !ok {
		return nil
	}
	tk, _ := stringOf(meta, "template_kind")

	if tk == "mutation-claim" {
		// RKC02: a claim must not borrow the appearance of proof. Presence is
		// what is forbidden, so this asks only whether the key is there. A
		// well-formedness test would let `execution_proof = [{ ... }]` through.
		if hasKey(doc, "execution_proof") {
			defects = append(defects, fmt.Sprintf(
				"%s: a mutation-claim MUST NOT carry `[execution_proof]` (RKC02). A document "+
					"with a proof is a state-mutation and MUST declare that template_kind, so "+
					"that RKM02, RKM04 and RKM06 apply to it", path))
		}
		checkMutationTable(path, doc, &defects)
		return defects
	}
	if tk != "state-mutation" {
		return nil
	}

	checkMutationTable(path, doc, &defects)

	// RKM02: the proof is mandatory and complete.
	proof, ok := tableOf(doc, "execution_proof")
	if !ok {
		if hasKey(doc, "execution_proof") {
			defects = append(defects, fmt.Sprintf(
				"%s: `execution_proof` is present but is not a table (RKM02). A "+
					"present-but-wrong-typed element MUST NOT be reported as absent "+
					"(SPEC 12.8.2), and proof material outside a table is not a proof", path))
		} else {
			defects = append(defects, fmt.Sprintf(
				"%s: missing required `[execution_proof]` table (RKM02). A record of an "+
					"irreversible state change with no execution proof is not a state-mutation; "+
					"use mutation-claim instead", path))
		}
		return defects
	}
	pkeys := make([]string, 0, len(proof))
	for k := range proof {
		pkeys = append(pkeys, k)
	}
	sort.Strings(pkeys)
	for _, k := range pkeys {
		if !allowedProofKeys[k] {
			defects = append(defects, fmt.Sprintf(
				"%s: execution_proof.%s is not a permitted key (RKM03 closed key set)", path, k))
		}
	}
	for _, k := range requiredProofKeys {
		if _, present := proof[k]; !present {
			defects = append(defects, fmt.Sprintf(
				"%s: execution_proof.%s is required (RKM02)", path, k))
		}
	}
	for _, k := range []string{"proof_sha256", "binds_sha256"} {
		// Absence is already reported against requiredProofKeys.
		switch v, state := fieldOf(proof, k); {
		case state == fieldNotString:
			defects = append(defects, fmt.Sprintf(
				"%s: execution_proof.%s must be a string carrying a digest scalar", path, k))
		case state == fieldString && !isMutationDigest(v):
			defects = append(defects, fmt.Sprintf(
				"%s: execution_proof.%s %q is not a digest scalar", path, k, v))
		}
	}
	switch v, state := fieldOf(proof, "proof_locator"); {
	case state == fieldNotString:
		defects = append(defects, fmt.Sprintf(
			"%s: execution_proof.proof_locator must be a string carrying a URI-shaped "+
				"reference (RKM03)", path))
	case state == fieldString && !isURIShaped(v):
		defects = append(defects, fmt.Sprintf(
			"%s: execution_proof.proof_locator %q must be a URI-shaped reference. A locator "+
				"names where the proof can be fetched; it is not a place to inline the proof "+
				"itself (RKM03)", path, v))
	}

	// RKM02 vocabulary membership, then RKM06 coherence. Membership is checked
	// with no empty-string and no wrong-type escape: neither is a member of a
	// closed vocabulary, and letting either skip the check accepted a proof
	// declaring no scheme at all.
	scheme, schemeOK := "", false
	switch v, state := fieldOf(proof, "scheme"); {
	case state == fieldNotString:
		defects = append(defects, fmt.Sprintf(
			"%s: execution_proof.scheme must be a string drawn from the closed "+
				"execution_proof_scheme vocabulary", path))
	case state == fieldString:
		if _, known := schemeFinality[v]; known {
			scheme, schemeOK = v, true
		} else {
			defects = append(defects, fmt.Sprintf(
				"%s: execution_proof.scheme %q is not in the closed execution_proof_scheme "+
					"vocabulary", path, v))
		}
	}
	finality, finalityOK := "", false
	switch v, state := fieldOf(proof, "finality_basis"); {
	case state == fieldNotString:
		defects = append(defects, fmt.Sprintf(
			"%s: execution_proof.finality_basis must be a string drawn from the closed "+
				"finality_basis vocabulary", path))
	case state == fieldString:
		if finalityValues[v] {
			finality, finalityOK = v, true
		} else {
			defects = append(defects, fmt.Sprintf(
				"%s: execution_proof.finality_basis %q is not in the closed finality_basis "+
					"vocabulary", path, v))
		}
	}
	if schemeOK && finalityOK {
		allowed := schemeFinality[scheme]
		okFinality := false
		for _, a := range allowed {
			if a == finality {
				okFinality = true
				break
			}
		}
		if !okFinality {
			defects = append(defects, fmt.Sprintf(
				"%s: execution_proof scheme %q cannot claim finality_basis %q (RKM06); it "+
					"carries evidence for %v only", path, scheme, finality, allowed))
		}
	}

	// RKM04: the proof must bind THIS mutation, not merely exist.
	//
	// Skipped unless every bound field is a string. Computing the tuple over a
	// non-string field would hash the empty string in its place and report a
	// mismatch against a tuple no producer wrote, burying the type defect
	// already reported above under a bogus RKM04 failure.
	if mutation, has := tableOf(doc, "mutation"); has {
		allBoundFieldsAreStrings := true
		for _, f := range boundTupleFields {
			if _, state := fieldOf(mutation, f[1]); state != fieldString {
				allBoundFieldsAreStrings = false
				break
			}
		}
		declared, present := stringOf(proof, "binds_sha256")
		if allBoundFieldsAreStrings && present && isMutationDigest(declared) {
			expected := mutationBoundTuple(mutation)
			if declared != expected {
				defects = append(defects, fmt.Sprintf(
					"%s: execution_proof.binds_sha256 %s does not equal the SPEC 12.8.2 bound "+
						"tuple recomputed from this document (%s) (RKM04). The proof does not "+
						"commit to this mutation", path, declared, expected))
			}
		}
	}

	return defects
}

func validateGateDecision(path string, doc rawDoc, repoRoot string) []string {
	var defects []string

	meta, ok := tableOf(doc, "meta")
	if !ok {
		return []string{fmt.Sprintf("%s: missing [meta]", path)}
	}
	tk, _ := stringOf(meta, "template_kind")
	if tk != "gate-decision" {
		return []string{fmt.Sprintf("%s: template_kind = %q (expected 'gate-decision')", path, tk)}
	}
	fp, _ := stringOf(meta, "framework_profile")
	if fp != "agent-assurance" {
		defects = append(defects, fmt.Sprintf(
			"%s: meta.framework_profile = %q (expected 'agent-assurance')", path, fp))
	}

	decision, ok := tableOf(doc, "decision")
	if !ok {
		return append(defects, fmt.Sprintf("%s: missing or non-table [decision]", path))
	}

	verdict, _ := decision["verdict"].(string)
	// Raw array: length and element types preserved so a non-table element
	// counts toward INV01 and is reported by INV02 (Rust parity).
	failedRefs := gdRawArray(decision["failed_constraint_refs"])

	// INV01: verdict == "pass" iff failed_constraint_refs is empty.
	isPass := verdict == "pass"
	isEmpty := len(failedRefs) == 0
	if isPass != isEmpty {
		defects = append(defects, fmt.Sprintf(
			"%s: INV01 violated: decision.verdict = %q but failed_constraint_refs has %d entries",
			path, verdict, len(failedRefs)))
	}

	// INV02.
	for i, e := range failedRefs {
		t, ok := e.(map[string]any)
		if !ok {
			defects = append(defects, fmt.Sprintf(
				"%s: INV02 violated: failed_constraint_refs[%d] is not a table", path, i))
			continue
		}
		cid, _ := t["constraint_id"].(string)
		if !gdAssertionRe.MatchString(cid) {
			defects = append(defects, fmt.Sprintf(
				"%s: INV02 violated: failed_constraint_refs[%d].constraint_id = %q does not match %s",
				path, i, cid, gdAssertionRe.String()))
		}
	}

	// INV03.
	overrides := gdRawArray(decision["override_refs"])
	for i, e := range overrides {
		t, ok := e.(map[string]any)
		if !ok {
			defects = append(defects, fmt.Sprintf(
				"%s: INV03 violated: override_refs[%d] is not a table", path, i))
			continue
		}
		line, _ := t["observation_line"].(string)
		if !gdObservedRe.MatchString(line) {
			defects = append(defects, fmt.Sprintf(
				"%s: INV03 violated: override_refs[%d].observation_line does not match canonical observed(...) shape: %q",
				path, i, line))
		}
	}

	// INV04.
	er, _ := decision["evidence_root"].(string)
	if !gdHex64Re.MatchString(er) {
		defects = append(defects, fmt.Sprintf(
			"%s: INV04 violated: decision.evidence_root = %q does not match %s",
			path, er, gdHex64Re.String()))
	}

	// INV06.
	subjectClass, hasSubjectClass := decision["subject_class"].(string)
	if hasSubjectClass {
		vocab := loadGateDecisionVocab(repoRoot, "subject_class")
		if vocab == nil {
			defects = append(defects, fmt.Sprintf(
				"%s: INV06 vocab load failed (subject_class vocabulary missing)", path))
		} else if !gdVocabContains(vocab, subjectClass) {
			defects = append(defects, fmt.Sprintf(
				"%s: INV06 violated: decision.subject_class = %q not in subject_class vocabulary %v",
				path, subjectClass, vocab))
		}
	}

	if subjectClass == "self-modification" {
		required := []string{
			"proposing_provider_id", "proposing_model_family_id",
			"deciding_provider_id", "deciding_model_family_id",
		}
		var missing []string
		for _, k := range required {
			v, _ := decision[k].(string)
			if v == "" {
				missing = append(missing, k)
			}
		}
		if len(missing) > 0 {
			defects = append(defects, fmt.Sprintf(
				"%s: INV06 violated: subject_class = 'self-modification' requires all four of %v; missing or empty: %v",
				path, required, missing))
		}

		providerVocab := loadGateDecisionVocab(repoRoot, "provider_id")
		familyVocab := loadGateDecisionVocab(repoRoot, "model_family_id")

		propP, _ := decision["proposing_provider_id"].(string)
		propF, _ := decision["proposing_model_family_id"].(string)
		decP, _ := decision["deciding_provider_id"].(string)
		decF, _ := decision["deciding_model_family_id"].(string)

		for _, item := range []struct {
			label string
			val   string
			vocab []string
		}{
			{"proposing_provider_id", propP, providerVocab},
			{"deciding_provider_id", decP, providerVocab},
			{"proposing_model_family_id", propF, familyVocab},
			{"deciding_model_family_id", decF, familyVocab},
		} {
			if item.val != "" && item.vocab != nil && !gdVocabContains(item.vocab, item.val) {
				defects = append(defects, fmt.Sprintf(
					"%s: INV06 violated: decision.%s = %q not in vocabulary %v",
					path, item.label, item.val, item.vocab))
			}
		}

		// Conjunctive AND.
		if propP != "" && propF != "" && decP != "" && decF != "" {
			sameProvider := decP == propP
			sameFamily := decF == propF
			if sameProvider || sameFamily {
				var problems []string
				if sameProvider {
					problems = append(problems, fmt.Sprintf(
						"deciding_provider_id (%q) == proposing_provider_id (%q)", decP, propP))
				}
				if sameFamily {
					problems = append(problems, fmt.Sprintf(
						"deciding_model_family_id (%q) == proposing_model_family_id (%q)", decF, propF))
				}
				defects = append(defects, fmt.Sprintf(
					"%s: INV06 violated (conjunctive AND): %s. INV06 requires BOTH deciding_provider_id != proposing_provider_id AND deciding_model_family_id != proposing_model_family_id. Same-provider/different-family and different-provider/same-family BOTH fail INV06.",
					path, strings.Join(problems, " AND ")))
			}
		}
	}

	return defects
}
