package main

import "testing"

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
