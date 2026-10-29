package main

import (
	"bytes"
	"errors"
)

func sourceControls() error {
	accepted := []struct {
		source string
		count  int
	}{
		{`namespace duckdb_re2 { class Item {}; }`, 1},
		{`namespace duckdb_re2 { const char *text="}"; char value='{'; /* } */ }`, 1},
		{`namespace duckdb_re2 { auto text=R"tag({ " } )tag"; namespace nested {struct Item{};} }`, 1},
		{`namespace duckdb_re2 { class Item {}; } namespace duckdb_re2 { void Other() {} }`, 2},
		{`namespace other {const char *text="namespace duckdb_re2 {";} namespace duckdb_re2 {}`, 1},
	}
	for _, control := range accepted {
		regions, err := namespaceRegions([]byte(control.source), "duckdb_re2")
		if err != nil || len(regions) != control.count {
			return errors.New("native C++ namespace capture changed its declared accepted population")
		}
		previous := 0
		for _, region := range regions {
			if region.Start < previous || region.End <= region.Start || region.End > len(control.source) || digest([]byte(control.source[region.Start:region.End])) != region.SHA {
				return errors.New("native C++ namespace capture lost its byte identity")
			}
			previous = region.End
		}
	}
	for _, source := range []string{`namespace duckdb_re2 {`, `namespace duckdb_re2 { "unfinished`, `namespace duckdb_re2 { /* unfinished`, `namespace duckdb_re2 { R"tag(unfinished`, `namespace unrelated {}`} {
		if _, err := namespaceRegions([]byte(source), "duckdb_re2"); err == nil {
			return errors.New("native C++ namespace capture accepted an absent or unfinished subject")
		}
	}
	// Exercise the complete transformation over a synthetic, explicitly bounded
	// population. Literal brace text cannot change the selected namespace set.
	declarations := []string{`class RE2;`, `class Regex {};`, `class StringPiece {};`, `class Prog;`, `class RE2 {};`}
	var input []byte
	input = append(input, []byte("outside_before();\n")...)
	for index := 0; index < 47; index++ {
		body := `void RetiredMatcherBody() {const char *text="}";}`
		if index < len(declarations) {
			body = declarations[index]
		}
		input = append(input, []byte("namespace duckdb_re2 {"+body+"}\n")...)
	}
	input = append(input, []byte("namespace duckdb_libpgquery { int yy_accept[]={1}; void GeneratedScanner() {} }\noutside_after();")...)
	refusal := []byte("namespace duckdb_re2 { void UnsupportedPatternOperation(); }")
	lexer := []byte("namespace duckdb_libpgquery { void OwnedByteScanner(); }")
	output, err := prepareCore(input, refusal, lexer)
	if err != nil {
		return err
	}
	for _, text := range [][]byte{[]byte("outside_before();"), []byte("outside_after();"), refusal, lexer} {
		if bytes.Count(output, text) != 1 {
			return errors.New("native source preparation changed its retained or replacement population")
		}
	}
	for _, text := range [][]byte{[]byte("RetiredMatcherBody"), []byte("GeneratedScanner"), []byte("yy_accept")} {
		found, err := sourceToken(output, string(text))
		if err != nil || found {
			return errors.New("native source preparation retained a retired body")
		}
	}
	if _, err := prepareCore([]byte(`namespace duckdb_re2 {}`), refusal, lexer); err == nil {
		return errors.New("native source preparation accepted a changed matcher population")
	}
	return nil
}
