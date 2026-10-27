package main

import (
	"crypto/sha256"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestLoadTomlDiagnostic(t *testing.T) {
	path := filepath.Join(t.TempDir(), "kind.toml")
	if err := os.WriteFile(path, []byte("[kind]\nname = 'valid'\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	var valid kindFile
	if err := loadToml(path, &valid); err != nil || valid.Kind.Name != "valid" {
		t.Fatalf("valid declaration rejected: %v, %+v", err, valid)
	}
	invalid := []byte("[kind]\nname = \xff\n")
	if err := os.WriteFile(path, invalid, 0o600); err != nil {
		t.Fatal(err)
	}
	var rejected kindFile
	err := loadToml(path, &rejected)
	if err == nil {
		t.Fatal("invalid declaration accepted")
	}
	message := err.Error()
	if !strings.Contains(message, fmt.Sprintf("source sha256 %x", sha256.Sum256(invalid))) {
		t.Fatalf("source digest missing from diagnostic: %s", message)
	}
	for _, coordinate := range []string{"line ", "column ", " at ("} {
		if strings.Contains(message, coordinate) {
			t.Fatalf("parser coordinate leaked into diagnostic: %s", message)
		}
	}
}

func TestDeclaredKindRequiresMatchingFields(t *testing.T) {
	cases := []struct {
		name         string
		templateKind string
		describes    string
		kindName     string
		accepted     bool
	}{
		{"matching", "kind-descriptor", "cost-record", "cost-record", true},
		{"wrong type", "implementation-dag", "cost-record", "cost-record", false},
		{"missing type", "", "cost-record", "cost-record", false},
		{"missing declaration", "kind-descriptor", "", "cost-record", false},
		{"mismatch", "kind-descriptor", "cost-record", "other", false},
	}
	for _, item := range cases {
		var file kindFile
		file.Meta.TemplateKind = item.templateKind
		file.Meta.DescribesKind = item.describes
		file.Kind.Name = item.kindName
		_, accepted := declaredKind(file)
		if accepted != item.accepted {
			t.Errorf("%s: accepted=%t, want %t", item.name, accepted, item.accepted)
		}
	}
}
