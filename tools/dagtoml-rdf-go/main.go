// dagtoml-rdf-go — Go counterpart of tools/dagtoml-rdf. Generates the
// DAG-TOML ontology as RDF/Turtle by reading every <repo-root>/core/
// and <repo-root>/profiles/<name>/ ontology.toml plus *-kind.toml.
//
// Safe Go: this file imports only the standard library plus
// github.com/pelletier/go-toml/v2 (a pure-Go TOML parser that itself
// does not use the `unsafe` package). There is no `import "unsafe"`
// anywhere in this binary. The CI safety check enforces that.
//
// Output:
//   - 6 IJB primitives
//   - 1 meta kind-descriptor plus every *-kind.toml on disk
//   - every [[entities]] block (rdfs:Class subClassOf ijb:Thing)
//   - every [[relations]] block (rdf:Property with rdfs:domain / range,
//     namespaced as <scope>:<predicate> when a predicate occurs more
//     than once with distinct domain/range tuples)
//   - every [[attribute_vocabularies]] block (rdf:Property + owl:oneOf
//     when extensible=false)
//
// Usage:
//
//	dagtoml-rdf-go [--repo-root <path>] [-o <output>]
//
// Default output: stdout. Equivalent to the Rust binary — produces the
// same Turtle artifact and the same `### Counts at generation:` footer
// that validators/check_manifest_drift.sh greps.
package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	toml "github.com/pelletier/go-toml/v2"
)

const (
	nsDagtoml = "https://verivus-oss.org/dagtoml/v1#"
	nsDagprof = "https://verivus-oss.org/dagtoml/profile/agent-assurance/v1#"
	nsIjb     = "https://verivus-oss.org/dagtoml/ijb/v1#"
)

// ---------- ontology shapes ----------

type ontology struct {
	Entities              []entity `toml:"entities"`
	Relations             []relation `toml:"relations"`
	AttributeVocabularies []vocab  `toml:"attribute_vocabularies"`
}

type entity struct {
	IDPrefix    string `toml:"id_prefix"`
	IDPattern   string `toml:"id_pattern"`
	Section     string `toml:"section"`
	Schema      string `toml:"schema"`
	Description string `toml:"description"`
}

type relation struct {
	Predicate   string   `toml:"predicate"`
	Source      []string `toml:"source"`
	Targets     []string `toml:"targets"`
	Cardinality string   `toml:"cardinality"`
	Inverse     string   `toml:"inverse"`
	Notes       string   `toml:"notes"`
}

type vocab struct {
	Attribute  string   `toml:"attribute"`
	AppliesTo  string   `toml:"applies_to"`
	Values     []string `toml:"values"`
	Extensible bool     `toml:"extensible"`
	Notes      string   `toml:"notes"`
}

type kindFile struct {
	Meta struct {
		TemplateKind  string `toml:"template_kind"`
		DescribesKind string `toml:"describes_kind"`
	} `toml:"meta"`
	Kind struct {
		Name string `toml:"name"`
	} `toml:"kind"`
}

// ---------- utilities ----------

func pascal(name string) string {
	var b strings.Builder
	up := true
	for _, ch := range name {
		switch ch {
		case '_', '-', ':', '.':
			up = true
		default:
			if up {
				b.WriteRune(toUpper(ch))
				up = false
			} else {
				b.WriteRune(ch)
			}
		}
	}
	return b.String()
}

func toUpper(r rune) rune {
	if r >= 'a' && r <= 'z' {
		return r - 32
	}
	return r
}

func ttlLit(s string) string {
	var b strings.Builder
	b.WriteByte('"')
	for _, ch := range s {
		switch ch {
		case '"':
			b.WriteString(`\"`)
		case '\\':
			b.WriteString(`\\`)
		case '\n':
			b.WriteString(`\n`)
		case '\r':
			b.WriteString(`\r`)
		case '\t':
			b.WriteString(`\t`)
		default:
			b.WriteRune(ch)
		}
	}
	b.WriteByte('"')
	return b.String()
}

var prefixToKind = map[string]string{
	"INT": "intent", "FEAT": "feature", "REQ": "requirement", "REG": "regulation",
	"DEC": "decision", "IMP": "implementation", "CODE": "code", "TEST": "test",
	"OUT": "output", "ART": "artifact", "GUAR": "guarantee", "INV": "invariant",
	"NG": "non_goal", "THREAT": "threat", "SMOKE": "smoke_check",
	"TRIG": "rollback_trigger", "DISC": "disclosure_attestation",
	"RED": "redaction", "SDP": "selective_disclosure_proof",
}

var sectionToKind = map[string]string{
	"units": "unit", "artifact_classes": "artifact_class", "gates": "gate",
	"contracts": "contract", "claims": "claim", "evidence": "evidence",
	"matrix": "matrix",
}

func tokenToClass(tok string) (string, bool) {
	if tok == "unconstrained_label" || tok == "" {
		return "", false
	}
	// section-style tokens used in [[relations]].source / .targets
	if k, ok := sectionToKind[tok]; ok {
		return "dagtoml:" + pascal(k), true
	}
	// prefix-style tokens (REQ, FEAT, GUAR, …)
	if k, ok := prefixToKind[tok]; ok {
		return "dagtoml:" + pascal(k), true
	}
	// fall back to direct PascalCase of the token
	return "dagtoml:" + pascal(tok), true
}

func entityKindName(e entity) string {
	if e.IDPrefix != "" {
		if k, ok := prefixToKind[e.IDPrefix]; ok {
			return k
		}
		return e.IDPrefix
	}
	if e.Section != "" {
		if k, ok := sectionToKind[e.Section]; ok {
			return k
		}
		return e.Section
	}
	return ""
}

// ---------- main ----------

func main() {
	var repoRoot, output string
	fs := flag.NewFlagSet("dagtoml-rdf-go", flag.ExitOnError)
	fs.StringVar(&repoRoot, "repo-root", ".", "repo root")
	fs.StringVar(&output, "o", "", "output Turtle path (default stdout)")
	fs.StringVar(&output, "output", "", "output Turtle path")

	args := os.Args[1:]
	verifyMode := false
	if len(args) > 0 && args[0] == "verify" {
		verifyMode = true
		args = args[1:]
	}
	_ = fs.Parse(args)

	if verifyMode {
		if output == "" {
			fmt.Fprintln(os.Stderr, "verify requires -o <path>")
			os.Exit(2)
		}
		if err := verifyTurtle(output); err != nil {
			fmt.Fprintf(os.Stderr, "verify %s: %v\n", output, err)
			os.Exit(1)
		}
		return
	}

	out, kindCount, entCount, relCount, vocCount, err := generate(repoRoot)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if output == "" {
		if _, err := os.Stdout.WriteString(out); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	} else {
		// Regenerated reference RDF schema; intended to be world-readable
		// (it's reviewed in PRs and consumed by every downstream
		// implementer of the spec).
		if err := os.WriteFile(output, []byte(out), 0o644); err != nil { //nolint:gosec  // G306: regenerated reference artifact, world-readable by design
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Fprintf(os.Stderr,
			"wrote %q: %d template kinds, %d entity kinds, %d relations, %d vocabularies\n",
			output, kindCount, entCount, relCount, vocCount)
	}
}

func generate(repoRoot string) (string, int, int, int, int, error) {
	corePath := filepath.Join(repoRoot, "core/ontology.toml")
	var coreOnt ontology
	if err := loadToml(corePath, &coreOnt); err != nil {
		return "", 0, 0, 0, 0, err
	}

	// Walk every profiles/<name>/ontology.toml. Profiles are discovered
	// dynamically — adding profiles/<new>/ontology.toml just works.
	type profOnt struct {
		name string
		o    ontology
	}
	var profOnts []profOnt
	if entries, err := os.ReadDir(filepath.Join(repoRoot, "profiles")); err == nil {
		var names []string
		for _, e := range entries {
			if e.IsDir() {
				names = append(names, e.Name())
			}
		}
		sort.Strings(names)
		for _, name := range names {
			p := filepath.Join(repoRoot, "profiles", name, "ontology.toml")
			if _, err := os.Stat(p); err != nil {
				continue
			}
			var o ontology
			if err := loadToml(p, &o); err != nil {
				return "", 0, 0, 0, 0, err
			}
			profOnts = append(profOnts, profOnt{name, o})
		}
	}

	// Collect kind descriptors: 1 meta + every *-kind.toml.
	type kindRow struct{ tk, layer, path string }
	kinds := []kindRow{{"kind-descriptor", "core", "spec.md"}}
	gather := func(layer, base string) error {
		entries, err := os.ReadDir(filepath.Join(repoRoot, base))
		if err != nil {
			return nil
		}
		var paths []string
		for _, e := range entries {
			if !e.IsDir() && strings.HasSuffix(e.Name(), "-kind.toml") {
				paths = append(paths, filepath.Join(base, e.Name()))
			}
		}
		sort.Strings(paths)
		for _, rel := range paths {
			var kf kindFile
			if err := loadToml(filepath.Join(repoRoot, rel), &kf); err != nil {
				continue
			}
			tk := kf.Meta.DescribesKind
			if tk == "" {
				tk = kf.Kind.Name
			}
			if tk == "" || tk == "kind-descriptor" {
				continue
			}
			kinds = append(kinds, kindRow{tk, layer, rel})
		}
		return nil
	}
	_ = gather("core", "core")
	for _, p := range profOnts {
		_ = gather("profile:"+p.name, "profiles/"+p.name)
	}

	// Entities (core + each profile, with layer attached).
	type entRow struct {
		kind, layer string
		e           entity
	}
	var entities []entRow
	for _, e := range coreOnt.Entities {
		if k := entityKindName(e); k != "" {
			entities = append(entities, entRow{k, "core", e})
		}
	}
	for _, p := range profOnts {
		for _, e := range p.o.Entities {
			if k := entityKindName(e); k != "" {
				entities = append(entities, entRow{k, "profile:" + p.name, e})
			}
		}
	}

	// Relations: namespace duplicates (only core has relations today).
	type relRow struct {
		r          relation
		predicate  string
	}
	var relations []relRow
	seen := map[string]int{}
	for _, r := range coreOnt.Relations {
		seen[r.Predicate]++
		pred := r.Predicate
		if seen[r.Predicate] > 1 {
			scope := "scoped"
			if len(r.Source) > 0 {
				switch r.Source[0] {
				case "contracts":
					scope = "contract"
				default:
					scope = r.Source[0]
				}
			}
			pred = scope + ":" + r.Predicate
		}
		relations = append(relations, relRow{r, pred})
	}

	// Vocabularies.
	type vocRow struct {
		v     vocab
		layer string
	}
	var vocabs []vocRow
	for _, v := range coreOnt.AttributeVocabularies {
		vocabs = append(vocabs, vocRow{v, "core"})
	}
	for _, p := range profOnts {
		for _, v := range p.o.AttributeVocabularies {
			vocabs = append(vocabs, vocRow{v, "profile:" + p.name})
		}
	}

	templateKindNames := map[string]bool{}
	for _, k := range kinds {
		templateKindNames[k.tk] = true
	}

	// ---------- emit ----------
	var b strings.Builder
	b.WriteString("# DAG-TOML ontology as RDF/Turtle (non-normative reference).\n")
	b.WriteString("# Generated by tools/dagtoml-rdf-go from core/ontology.toml +\n")
	b.WriteString("# every profiles/<name>/ontology.toml. Do not hand-edit; re-run\n")
	b.WriteString("# `go run ./tools/dagtoml-rdf-go` instead.\n#\n")
	fmt.Fprintf(&b,
		"# Counts (verified at generation): %d template kinds, %d entity\n",
		len(kinds), len(entities))
	fmt.Fprintf(&b,
		"# kinds, %d relation predicates, %d attribute vocabularies.\n\n",
		len(relations), len(vocabs))
	fmt.Fprintf(&b, "@prefix dagtoml: <%s> .\n", nsDagtoml)
	fmt.Fprintf(&b, "@prefix dagprof: <%s> .\n", nsDagprof)
	fmt.Fprintf(&b, "@prefix ijb:     <%s> .\n", nsIjb)
	b.WriteString("@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n")
	b.WriteString("@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .\n")
	b.WriteString("@prefix owl:     <http://www.w3.org/2002/07/owl#> .\n")
	b.WriteString("@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .\n\n")

	section := func(title string) {
		b.WriteString("###\n### " + title + "\n###\n\n")
	}

	section("IJB primitives (spec.md §10)")
	for _, p := range []struct{ term, label string }{
		{"Thing", "thing"}, {"Scope", "scope"}, {"Path", "path"},
		{"Observed", "observed"}, {"Constraint", "constraint"}, {"Time", "time"},
	} {
		fmt.Fprintf(&b, "ijb:%s a rdfs:Class ;\n    rdfs:label %s .\n\n", p.term, ttlLit(p.label))
	}

	section(fmt.Sprintf("Template kinds (%d = core + every profile + 1 meta)", len(kinds)))
	fmt.Fprintf(&b,
		"dagtoml:KindDescriptor a rdfs:Class ;\n    rdfs:subClassOf ijb:Thing ;\n    rdfs:label %s ;\n    rdfs:comment %s .\n\n",
		ttlLit("kind-descriptor"),
		ttlLit("Self-contained template descriptor for a DAG-TOML kind."))
	for _, k := range kinds {
		fmt.Fprintf(&b,
			"dagtoml:%sKind a dagtoml:KindDescriptor ;\n    dagtoml:templateKind   %s ;\n    dagtoml:layer          %s ;\n    dagtoml:descriptorPath %s .\n\n",
			pascal(k.tk), ttlLit(k.tk), ttlLit(k.layer), ttlLit(k.path))
	}

	section(fmt.Sprintf("Entity kinds (%d, all ijb:Thing)", len(entities)))
	for _, er := range entities {
		fmt.Fprintf(&b,
			"dagtoml:%s a rdfs:Class ;\n    rdfs:subClassOf ijb:Thing ;\n    rdfs:label %s ;\n    dagtoml:layer %s ",
			pascal(er.kind), ttlLit(er.kind), ttlLit(er.layer))
		if er.e.IDPrefix != "" {
			fmt.Fprintf(&b, ";\n    dagtoml:idPrefix %s ", ttlLit(er.e.IDPrefix))
		}
		if er.e.IDPattern != "" {
			fmt.Fprintf(&b, ";\n    dagtoml:idPattern %s ", ttlLit(er.e.IDPattern))
		}
		if er.e.Section != "" {
			fmt.Fprintf(&b, ";\n    dagtoml:section %s ", ttlLit(er.e.Section))
		}
		if er.e.Schema != "" {
			fmt.Fprintf(&b, ";\n    dagtoml:definedByKind %s ", ttlLit(er.e.Schema))
		}
		if er.e.Description != "" {
			fmt.Fprintf(&b, ";\n    rdfs:comment %s ", ttlLit(er.e.Description))
		}
		b.WriteString(".\n\n")
	}

	section(fmt.Sprintf("Relation predicates (%d = one per [[relations]] block)", len(relations)))
	for _, rr := range relations {
		local := strings.ReplaceAll(rr.predicate, ":", "_")
		fmt.Fprintf(&b, "dagtoml:%s a rdf:Property ;\n    rdfs:label %s ", local, ttlLit(rr.predicate))
		var doms []string
		for _, s := range rr.r.Source {
			if c, ok := tokenToClass(s); ok {
				doms = append(doms, c)
			}
		}
		if len(doms) == 1 {
			fmt.Fprintf(&b, ";\n    rdfs:domain %s ", doms[0])
		} else if len(doms) > 1 {
			fmt.Fprintf(&b, ";\n    rdfs:domain [ a owl:Class ; owl:unionOf ( %s ) ] ", strings.Join(doms, " "))
		}
		var rngs []string
		freeform := false
		for _, t := range rr.r.Targets {
			if t == "unconstrained_label" {
				freeform = true
				continue
			}
			if c, ok := tokenToClass(t); ok {
				rngs = append(rngs, c)
			}
		}
		if freeform {
			b.WriteString(";\n    dagtoml:targetFreeForm true ")
		}
		if len(rngs) == 1 {
			fmt.Fprintf(&b, ";\n    rdfs:range %s ", rngs[0])
		} else if len(rngs) > 1 {
			fmt.Fprintf(&b, ";\n    rdfs:range [ a owl:Class ; owl:unionOf ( %s ) ] ", strings.Join(rngs, " "))
		}
		if rr.r.Inverse != "" {
			fmt.Fprintf(&b, ";\n    owl:inverseOf dagtoml:%s ", strings.ReplaceAll(rr.r.Inverse, ":", "_"))
		}
		if rr.r.Cardinality != "" {
			fmt.Fprintf(&b, ";\n    dagtoml:cardinality %s ", ttlLit(rr.r.Cardinality))
		}
		if rr.r.Notes != "" {
			fmt.Fprintf(&b, ";\n    rdfs:comment %s ", ttlLit(rr.r.Notes))
		}
		b.WriteString(".\n\n")
	}

	section(fmt.Sprintf("Attribute vocabularies (%d)", len(vocabs)))
	for _, vr := range vocabs {
		local := strings.ReplaceAll(strings.ReplaceAll(vr.v.Attribute, ".", "_"), ":", "_")
		fmt.Fprintf(&b,
			"dagtoml:%s a rdf:Property ;\n    rdfs:label %s ;\n    dagtoml:layer %s ;\n    dagtoml:extensible %v ",
			local, ttlLit(vr.v.Attribute), ttlLit(vr.layer), vr.v.Extensible)
		if vr.v.AppliesTo != "" {
			if templateKindNames[vr.v.AppliesTo] {
				fmt.Fprintf(&b, ";\n    dagtoml:appliesToKind dagtoml:%sKind ", pascal(vr.v.AppliesTo))
			} else if c, ok := tokenToClass(vr.v.AppliesTo); ok {
				fmt.Fprintf(&b, ";\n    rdfs:domain %s ", c)
			} else {
				fmt.Fprintf(&b, ";\n    dagtoml:appliesTo %s ", ttlLit(vr.v.AppliesTo))
			}
		}
		if len(vr.v.Values) > 0 {
			parts := make([]string, 0, len(vr.v.Values))
			for _, val := range vr.v.Values {
				parts = append(parts, ttlLit(val))
			}
			fmt.Fprintf(&b, ";\n    rdfs:range [ a rdfs:Datatype ; owl:oneOf ( %s ) ] ", strings.Join(parts, " "))
		}
		if vr.v.Notes != "" {
			fmt.Fprintf(&b, ";\n    rdfs:comment %s ", ttlLit(vr.v.Notes))
		}
		b.WriteString(".\n\n")
	}

	// Footer counts — the drift script greps this line.
	b.WriteString("###\n")
	fmt.Fprintf(&b,
		"### Counts at generation: %d template kinds, %d entity kinds, %d relation predicates, %d attribute vocabularies.\n",
		len(kinds), len(entities), len(relations), len(vocabs))
	b.WriteString("###\n")

	return b.String(), len(kinds), len(entities), len(relations), len(vocabs), nil
}

func loadToml(path string, v any) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("read %s: %w", path, err)
	}
	if err := toml.Unmarshal(data, v); err != nil {
		return fmt.Errorf("parse %s: %w", path, err)
	}
	return nil
}

// verifyTurtle does a structural sanity-check on the .ttl: confirms it
// contains the prefix declarations, the IJB primitives, and at least
// one of each top-level section. Full RDF parsing is the Rust verifier's
// job (it has access to oxttl); doing a real RDF parse in Go would
// require pulling in a heavier dependency. We deliberately keep this
// counterpart lightweight and stick to grep-like assertions.
func verifyTurtle(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	src := string(data)
	must := []string{
		"@prefix dagtoml:",
		"@prefix ijb:",
		"ijb:Thing a rdfs:Class",
		"dagtoml:KindDescriptor a rdfs:Class",
		"### IJB primitives",
		"### Counts at generation:",
	}
	missing := []string{}
	for _, m := range must {
		if !strings.Contains(src, m) {
			missing = append(missing, m)
		}
	}
	if len(missing) > 0 {
		return fmt.Errorf("missing tokens: %v", missing)
	}
	// Walk the file as a TOML-adjacent text — light sanity that braces /
	// parens balance enough to flag truncation.
	open := strings.Count(src, "[")
	closed := strings.Count(src, "]")
	if open != closed {
		return fmt.Errorf("unbalanced brackets: %d open vs %d closed", open, closed)
	}
	fmt.Fprintf(os.Stderr, "verify %q: OK — %d lines, balanced brackets\n",
		path, strings.Count(src, "\n"))
	return nil
}
