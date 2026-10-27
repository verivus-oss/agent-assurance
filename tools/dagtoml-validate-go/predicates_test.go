package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestLoadDocAcceptsValidAndReportsInvalidWithoutSourceCoordinates(t *testing.T) {
	path := filepath.Join(t.TempDir(), "input.toml")
	if err := os.WriteFile(path, []byte("valid = 1\n"), 0600); err != nil {
		t.Fatal(err)
	}
	valid, err := loadDoc(path)
	if err != nil {
		t.Fatalf("valid TOML rejected: %v", err)
	}
	if valid["valid"] != int64(1) {
		t.Fatalf("valid value changed: %#v", valid["valid"])
	}
	if err := os.WriteFile(path, []byte("broken = [\n"), 0600); err != nil {
		t.Fatal(err)
	}
	_, err = loadDoc(path)
	if err == nil {
		t.Fatal("malformed TOML accepted")
	}
	message := err.Error()
	if !strings.Contains(message, "TOML parse failed (strict)") ||
		!strings.Contains(message, "sha256:663eb4e5c398fe1ebb16c3d167d0d00027440ff6521dab9f063cd06d476d0dc4") ||
		!strings.Contains(message, "byte span ") ||
		strings.Contains(message, "line ") || strings.Contains(message, "column ") {
		t.Fatalf("unexpected parse diagnostic: %s", message)
	}
}

func TestByteOffsetAtRejectsInvalidPositions(t *testing.T) {
	document := []byte("α = 1\nbad = [")
	if offset, ok := byteOffsetAt(document, 2, 1); !ok || offset != len([]byte("α = 1\n")) {
		t.Fatalf("wrong byte offset for second row: %d, %v", offset, ok)
	}
	for _, position := range [][2]int{{0, 1}, {1, 0}, {3, 1}, {1, 100}, {2, int(^uint(0) >> 1)}} {
		if offset, ok := byteOffsetAt(document, position[0], position[1]); ok {
			t.Fatalf("invalid position accepted at byte %d: %#v", offset, position)
		}
	}
}

func TestDiscoverDescriptorsRejectsMalformedCandidate(t *testing.T) {
	root := t.TempDir()
	valid := filepath.Join(root, "profiles", "valid", "PROFILE.toml")
	malformed := filepath.Join(root, "profiles", "malformed", "PROFILE.toml")
	for _, path := range []string{valid, malformed} {
		if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(valid, []byte("[meta]\ntemplate_kind = 'profile-descriptor'\n[profile]\nname = 'valid'\n"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(malformed, []byte("broken = [\n"), 0600); err != nil {
		t.Fatal(err)
	}
	descriptors, errors := discoverDescriptors(root)
	if _, ok := descriptors["valid"]; !ok {
		t.Fatal("valid descriptor was skipped")
	}
	if len(errors) != 1 || !strings.Contains(errors[0], "TOML parse failed") {
		t.Fatalf("malformed descriptor was not reported: %#v", errors)
	}
	if err := os.Remove(malformed); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink("missing-profile.toml", malformed); err != nil {
		t.Fatal(err)
	}
	_, errors = discoverDescriptors(root)
	if len(errors) != 1 || !strings.Contains(errors[0], "dangling discovery candidate") {
		t.Fatalf("dangling descriptor was not reported: %#v", errors)
	}
	if err := os.WriteFile(filepath.Join(root, "profiles", "README.md"), []byte("notes\n"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink("missing-directory", filepath.Join(root, "profiles", "ghost")); err != nil {
		t.Fatal(err)
	}
	_, errors = discoverDescriptors(root)
	if len(errors) != 2 {
		t.Fatalf("dangling directory was not reported: %#v", errors)
	}
}

func TestKindDescriptorCandidatesRequireReadableProfiles(t *testing.T) {
	root := t.TempDir()
	profiles := filepath.Join(root, "profiles")
	if err := os.MkdirAll(filepath.Join(profiles, "valid"), 0700); err != nil {
		t.Fatal(err)
	}
	candidates, err := kindDescriptorCandidates(root, "foo", "valid")
	if err != nil {
		t.Fatalf("valid profile directory rejected: %v", err)
	}
	want := filepath.Join(profiles, "valid", "foo-kind.toml")
	found := false
	for _, candidate := range candidates {
		if candidate == want {
			found = true
		}
	}
	if !found {
		t.Fatalf("candidate %s missing from %#v", want, candidates)
	}
	actual := filepath.Join(profiles, "valid", "real.toml")
	if err := os.WriteFile(actual, []byte("valid = 1\n"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink("real.toml", want); err != nil {
		t.Fatal(err)
	}
	if present, err := candidateFile(want); err != nil || !present {
		t.Fatalf("live kind link rejected: %v, %v", present, err)
	}
	if err := os.Remove(want); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink("missing-kind.toml", want); err != nil {
		t.Fatal(err)
	}
	if _, err := candidateFile(want); err == nil || !strings.Contains(err.Error(), "dangling") {
		t.Fatalf("dangling kind link accepted: %v", err)
	}
	if err := os.RemoveAll(profiles); err != nil {
		t.Fatal(err)
	}
	if _, err := kindDescriptorCandidates(root, "foo", "valid"); err == nil {
		t.Fatal("missing profile directory accepted")
	}
	if err := os.Symlink("missing-profiles", profiles); err != nil {
		t.Fatal(err)
	}
	if _, err := kindDescriptorCandidates(root, "foo", "valid"); err == nil || !strings.Contains(err.Error(), "dangling") {
		t.Fatalf("dangling profile directory accepted: %v", err)
	}
}

func TestCandidatePredicatesRejectDanglingAncestors(t *testing.T) {
	root := t.TempDir()
	bridge := filepath.Join(root, "bridge")
	if err := os.Symlink("missing-directory", bridge); err != nil {
		t.Fatal(err)
	}
	for _, candidate := range []string{filepath.Join(bridge, "subdir"), filepath.Join(bridge, "subdir", "file.toml")} {
		if _, err := candidateDirectory(candidate); err == nil || !strings.Contains(err.Error(), "dangling discovery directory") {
			t.Fatalf("nested dangling directory accepted: %s, %v", candidate, err)
		}
		if _, err := candidateFile(candidate); err == nil || !strings.Contains(err.Error(), "dangling discovery directory") {
			t.Fatalf("nested dangling file accepted: %s, %v", candidate, err)
		}
	}
	if err := os.Remove(bridge); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(filepath.Join(root, "real"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink("real", bridge); err != nil {
		t.Fatal(err)
	}
	if present, err := candidateDirectory(bridge); err != nil || !present {
		t.Fatalf("live directory link rejected: %v, %v", present, err)
	}
	if present, err := candidateFile(filepath.Join(bridge, "missing.toml")); err != nil || present {
		t.Fatalf("optional missing file changed: %v, %v", present, err)
	}
}

func TestValueShapes(t *testing.T) {
	cases := []struct {
		name  string
		check func(string) bool
		good  []string
		bad   []string
	}{
		{"semver", validSemver, []string{"0.1.0", "10.0.999"}, []string{"01.0.0", "1.2", "1.2.3.4", "1.2.x"}},
		{"date", validDate, []string{"2026-10-27", "9999-99-99"}, []string{"2026-1-27", "2026/10/27"}},
		{"datetime", validDateTime, []string{"2026-10-27t12:34:56.1Z", "2026-10-27T12:34:56+10:00"}, []string{"2026-10-27T12:34", "2026-10-27T12:34:56", "2026-10-27T12:34:56.", "2026-10-27T12:34:56+10"}},
		{"name", validUnprefixedName, []string{"alpha", "a-0"}, []string{"", "A", "0alpha", "a_b"}},
		{"reverse dns", validReverseDNS, []string{"com.verivus", "a.b-c"}, []string{"a", "a..b", "A.b"}},
		{"closure field", validClosureRecordField, []string{"field", "A_b.9-x"}, []string{"", ".a", "a..b", "a!"}},
		{"hex64", validHex64, []string{"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}, []string{"0", "0123456789ABCDEF0123456789abcdef0123456789abcdef0123456789abcdef"}},
		{"sha256", validSha256, []string{"sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}, []string{"sha256:0", "SHA256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}},
		{"abstraction", validAbstractionID, []string{"x.v1", "0_a.v007", "a..v2"}, []string{"x.v", "A.v1", "x.v-1", "x.1"}},
		{"assertion", validAssertionID, []string{"A-1", "A-Ab_2"}, []string{"A-", "A-_x", "a-1", "A-1.x"}},
		{"observation", validObservedLine, []string{"A-1=observed(x)", "A-Ab_2 \t=\t observed(a=b)  "}, []string{" A-1=observed(x)", "A-1=observed()", "A-1=observed(x))", "A-1=observed(x) extra"}},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			for _, value := range c.good {
				if !c.check(value) {
					t.Errorf("rejected accepted value %q", value)
				}
			}
			for _, value := range c.bad {
				if c.check(value) {
					t.Errorf("accepted rejected value %q", value)
				}
			}
		})
	}
}

func TestDecimalIDShapes(t *testing.T) {
	unit := decimalIDShape{"U", true}
	artifact := decimalIDShape{"A", false}
	for _, value := range []string{"U0", "U01", "U01a"} {
		if !matchesDecimalID(unit, value) {
			t.Errorf("unit ID %q rejected", value)
		}
	}
	for _, value := range []string{"U", "U01A", "U01aa", "U-1", "X01", "U١"} {
		if matchesDecimalID(unit, value) {
			t.Errorf("invalid unit ID %q accepted", value)
		}
	}
	if !matchesDecimalID(artifact, "A12") || matchesDecimalID(artifact, "A12a") {
		t.Error("artifact ID optional suffix boundary is wrong")
	}
}
