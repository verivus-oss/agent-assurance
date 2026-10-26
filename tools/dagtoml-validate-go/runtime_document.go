package main

import (
	"fmt"
	"path/filepath"
	"reflect"
	"strings"
)

// rdArray preserves every element, including malformed scalar entries.
func rdArray(value any) ([]any, bool) {
	if value == nil {
		return nil, false
	}
	v := reflect.ValueOf(value)
	if v.Kind() != reflect.Slice {
		return nil, false
	}
	out := make([]any, v.Len())
	for i := range out {
		out[i] = v.Index(i).Interface()
	}
	return out, true
}

func rdVocab(root, attribute string) ([]string, bool, bool) {
	paths, err := filepath.Glob(filepath.Join(root, "profiles", "*", "ontology.toml"))
	if err != nil || !containsString(paths, filepath.Join(root, "profiles/agent-assurance/ontology.toml")) {
		return nil, false, false
	}
	paths = append(paths, filepath.Join(root, "core/ontology.toml"))
	seen := map[string]bool{}
	var found []string
	var foundExtensible, foundOK bool
	for _, path := range paths {
		doc, err := loadDoc(path)
		if err != nil {
			return nil, false, false
		}
		entries, ok := rdArray(doc["attribute_vocabularies"])
		if !ok || len(entries) == 0 {
			return nil, false, false
		}
		for _, raw := range entries {
			entry, ok := raw.(map[string]any)
			if !ok {
				return nil, false, false
			}
			name, nameOK := entry["attribute"].(string)
			extensible, extOK := entry["extensible"].(bool)
			values, valuesOK := rdArray(entry["values"])
			if !nameOK || name == "" || seen[name] || !extOK || !valuesOK {
				return nil, false, false
			}
			seen[name] = true
			tokens := []string{}
			for _, value := range values {
				token, ok := value.(string)
				if !ok || containsString(tokens, token) {
					return nil, false, false
				}
				tokens = append(tokens, token)
			}
			if name == attribute {
				found, foundExtensible, foundOK = tokens, extensible, true
			}
		}
	}
	return found, foundExtensible, foundOK
}

func validateRuntimeFields(doc rawDoc, kind, root string) []string {
	var errors []string
	meta, _ := tableOf(doc, "meta")
	if meta["template_kind"] != kind {
		errors = append(errors, "RDMETA: meta.template_kind must match the selected kind")
	}
	profile, _ := meta["framework_profile"].(string)
	if profile != "agent-assurance" && profile != "AGDF" {
		errors = append(errors, "RDMETA: meta.framework_profile must identify agent-assurance")
	}
	bindings := []struct {
		kind, section, field, attribute string
		required                        bool
	}{
		{"adapter-contract", "adapter", "runtime_kind", "runtime_kind", true},
		{"adapter-contract", "adapter", "runtime_network_policy", "runtime_network_policy", true},
		{"adapter-contract", "adapter", "runtime_clock_policy", "runtime_clock_policy", true},
		{"adapter-contract", "adapter", "id_derivation", "adapter_id_derivation", false},
		{"adapter-registry-binding", "binding", "adapter_ref_syntax", "adapter_ref_syntax", true},
		{"gate-decision", "decision", "verdict", "gate_decision_verdict", true},
	}
	for _, b := range bindings {
		if b.kind != kind {
			continue
		}
		table, ok := tableOf(doc, b.section)
		if !ok {
			errors = append(errors, fmt.Sprintf("RDVOCAB %s: %s must be a table", b.attribute, b.section))
			continue
		}
		value, present := table[b.field]
		if !b.required && !present {
			continue
		}
		values, extensible, loaded := rdVocab(root, b.attribute)
		if !loaded || extensible || len(values) == 0 {
			errors = append(errors, "RDLOAD: missing/invalid closed vocabulary "+b.attribute)
			continue
		}
		token, stringOK := value.(string)
		if !stringOK || !containsString(values, token) {
			errors = append(errors, fmt.Sprintf("RDVOCAB %s: %s.%s must be a declared string", b.attribute, b.section, b.field))
		}
	}
	return errors
}

func rdNonempty(table map[string]any, field, location string, errors *[]string) {
	value, ok := table[field].(string)
	if !ok || strings.TrimSpace(value) == "" {
		*errors = append(*errors, fmt.Sprintf("RDSTRUCT: %s.%s must be a nonempty string", location, field))
	}
}

func rdEntries(table map[string]any, field, location string, required bool, errors *[]string) []map[string]any {
	value, present := table[field]
	if !present && !required {
		return nil
	}
	entries, ok := rdArray(value)
	if !ok || (required && len(entries) == 0) {
		*errors = append(*errors, fmt.Sprintf("RDSTRUCT: %s.%s must be an array of tables%s", location, field, map[bool]string{true: " with at least one entry", false: ""}[required]))
		return nil
	}
	var out []map[string]any
	for _, entry := range entries {
		row, ok := entry.(map[string]any)
		if !ok {
			*errors = append(*errors, fmt.Sprintf("RDSTRUCT: every %s.%s entry must be a table", location, field))
			continue
		}
		out = append(out, row)
	}
	return out
}

func validateRuntimeAdapter(doc rawDoc, root string, binding bool) []string {
	kind, section := "adapter-contract", "adapter"
	if binding {
		kind, section = "adapter-registry-binding", "binding"
	}
	errors := validateRuntimeFields(doc, kind, root)
	table, ok := tableOf(doc, section)
	if !ok {
		return errors
	}
	if binding {
		rdNonempty(table, "adapter_ref", section, &errors)
		rdNonempty(table, "registry_url", section, &errors)
		scheme, schemeOK := table["registry_url_scheme"].(string)
		url, urlOK := table["registry_url"].(string)
		values, _, loaded := rdVocab(root, "registry_scheme")
		if !loaded {
			errors = append(errors, "RDLOAD: invalid registry_scheme declaration")
		} else if !schemeOK || !containsString(values, scheme) {
			errors = append(errors, "INV01: binding.registry_url_scheme must be declared in registry_scheme")
		}
		if !schemeOK || !urlOK || !strings.HasPrefix(url, scheme+"://") {
			errors = append(errors, "INV02: binding.registry_url must start with the declared scheme followed by ://")
		}
		for _, entry := range rdEntries(table, "trust_anchor_refs", section, false, &errors) {
			rdNonempty(entry, "anchor_id", "binding.trust_anchor_refs[]", &errors)
		}
		for _, entry := range rdEntries(table, "policy_constraint_refs", section, false, &errors) {
			value, ok := entry["constraint_id"].(string)
			if !ok || !gdAssertionRe.MatchString(value) {
				errors = append(errors, "INV03: binding.policy_constraint_refs[].constraint_id must match the whole ASCII assertion-ID grammar")
			}
		}
	} else {
		rdNonempty(table, "input_source", section, &errors)
		values, extensible, loaded := rdVocab(root, "input_hash_method")
		if !loaded {
			return append(errors, "RDLOAD: invalid input_hash_method declaration")
		}
		if raw, present := table["input_hash_method"]; present {
			value, ok := raw.(string)
			if !ok || (!extensible && !containsString(values, value)) {
				errors = append(errors, "RDVOCAB input_hash_method: adapter.input_hash_method must satisfy its declared string vocabulary")
			}
		}
		runtimeKind, _ := table["runtime_kind"].(string)
		field := map[string]string{"wasi-component": "component_digest", "oci-action": "oci_image_digest", "os-sandbox": "profile_args_digest"}[runtimeKind]
		artifact, ok := table["runtime_artifact"].(map[string]any)
		if !ok {
			errors = append(errors, "INV02: adapter.runtime_artifact must be a table")
		} else if field != "" {
			value, ok := artifact[field].(string)
			if !ok || !gdHex64Re.MatchString(value) {
				errors = append(errors, "INV02: adapter.runtime_artifact."+field+" must be exactly 64 lowercase ASCII hex characters")
			}
		}
		for _, entry := range rdEntries(table, "emits", section, true, &errors) {
			value, ok := entry["ijb_primitive"].(string)
			if !ok || !containsString([]string{"thing", "scope", "path", "observed", "constraint", "time"}, value) {
				errors = append(errors, "INV03: adapter.emits[].ijb_primitive must be one of the six IJB primitives")
			}
		}
		for _, entry := range rdEntries(table, "conformance_fixtures", section, true, &errors) {
			for _, field := range []string{"raw_input_ref", "expected_bundle_ref"} {
				rdNonempty(entry, field, "adapter.conformance_fixtures[]", &errors)
			}
		}
		for _, entry := range rdEntries(table, "declared_invariants", section, false, &errors) {
			for _, field := range []string{"id", "description", "enforced_by"} {
				rdNonempty(entry, field, "adapter.declared_invariants[]", &errors)
			}
		}
		if value, present := table["runtime_env_allowlist"]; present {
			entries, ok := rdArray(value)
			valid := ok
			for _, entry := range entries {
				if _, ok := entry.(string); !ok {
					valid = false
				}
			}
			if !valid {
				errors = append(errors, "RDSTRUCT: adapter.runtime_env_allowlist must be an array of strings")
			}
		}
	}
	return errors
}
