// dagtoml-validate-go is the Go primary validator for the DAG-TOML
// artifacts introduced by the draft layering work:
//
//   - template_kind = "profile-descriptor" (spec.md §6.1)
//   - the disclosure profile kinds (disclosure-attestation,
//     redaction-manifest, selective-disclosure-proof)
//   - [provenance.encryption] sub-table (spec.md §11.1)
//   - SPEC §2.7 cross-field rules (confidentiality / license /
//     embargo_until)
//   - SPEC §2.5 namespacing partition
//   - SPEC §2.6 docs URL shape
//   - SPEC §2.2 / §8 version pin shapes: schema_version is semver;
//     ontology_version, when present, is a positive integer snapshot
//
// It runs in CI alongside the safe-Rust validator
// (tools/dagtoml-validate-rs/). Both are primary; the Python
// validators under validators/ are retained as cross-check
// references.
package main

import (
	"crypto/sha256"
	"crypto/sha512"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/BurntSushi/toml"
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

func stringOf(v any, key string) (string, bool) {
	m, ok := v.(map[string]any)
	if !ok {
		return "", false
	}
	s, ok := m[key].(string)
	return s, ok
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
	}
	return modeAuto, fmt.Errorf("invalid mode %q (want auto|profile|disclosure|provenance|meta|gate-decision)", s)
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

func validateClosureRoot(path string, doc rawDoc) []string {
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
	records, errs := sourceHashRecords(path, doc)
	if len(errs) > 0 {
		return errs
	}
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

var (
	unprefixedRE = regexp.MustCompile(`^[a-z][a-z0-9-]*$`)
	reverseDNSRE = regexp.MustCompile(`^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+$`)
	sha256RE     = regexp.MustCompile(`^sha256:[0-9a-f]{64}$`)
)

type descriptor struct {
	path string
	doc  rawDoc
}

func discoverDescriptors(repoRoot string) map[string]descriptor {
	out := map[string]descriptor{}
	root := filepath.Join(repoRoot, "profiles")
	entries, err := os.ReadDir(root)
	if err != nil {
		return out
	}
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
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
			out[name] = descriptor{candidate, doc}
		}
	}
	return out
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
			if e.IsDir() {
				cands = append(cands, filepath.Join(repoRoot, "profiles", e.Name(), fname))
			}
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
	flag.StringVar(&modeStr, "mode", "auto", "Validation mode (auto|profile|disclosure|provenance|meta)")
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
	descriptors := discoverDescriptors(root)

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
			errs = append(errs, validateClosureRoot(path, doc)...)
		}
		switch m {
		case modeAuto:
			switch tk {
			case "profile-descriptor":
				errs = append(errs, validateProfileDescriptor(path, doc, root, descriptors)...)
			case "disclosure-attestation", "redaction-manifest", "selective-disclosure-proof":
				errs = append(errs, validateDisclosure(path, doc, root)...)
			case "gate-decision":
				errs = append(errs, validateGateDecision(path, doc, root)...)
			}
		case modeProfile:
			errs = append(errs, validateProfileDescriptor(path, doc, root, descriptors)...)
		case modeDisclosure:
			errs = append(errs, validateDisclosure(path, doc, root)...)
		case modeGateDecision:
			errs = append(errs, validateGateDecision(path, doc, root)...)
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

// gdAsTableArray normalises an array-of-tables value from BurntSushi/toml's
// dynamic decoder, which returns either []map[string]any or []any
// (where elements are map[string]any) depending on context.
func gdAsTableArray(v any) []map[string]any {
	switch x := v.(type) {
	case []map[string]any:
		return x
	case []any:
		out := make([]map[string]any, 0, len(x))
		for _, e := range x {
			if m, ok := e.(map[string]any); ok {
				out = append(out, m)
			}
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
	failedRefs := gdAsTableArray(decision["failed_constraint_refs"])

	// INV01: verdict == "pass" iff failed_constraint_refs is empty.
	isPass := verdict == "pass"
	isEmpty := len(failedRefs) == 0
	if isPass != isEmpty {
		defects = append(defects, fmt.Sprintf(
			"%s: INV01 violated: decision.verdict = %q but failed_constraint_refs has %d entries",
			path, verdict, len(failedRefs)))
	}

	// INV02.
	for i, t := range failedRefs {
		cid, _ := t["constraint_id"].(string)
		if !gdAssertionRe.MatchString(cid) {
			defects = append(defects, fmt.Sprintf(
				"%s: INV02 violated: failed_constraint_refs[%d].constraint_id = %q does not match %s",
				path, i, cid, gdAssertionRe.String()))
		}
	}

	// INV03.
	overrides := gdAsTableArray(decision["override_refs"])
	for i, t := range overrides {
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
