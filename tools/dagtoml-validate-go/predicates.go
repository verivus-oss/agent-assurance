package main

import "strings"

func asciiDigit(c byte) bool    { return c >= '0' && c <= '9' }
func asciiLower(c byte) bool    { return c >= 'a' && c <= 'z' }
func asciiUpper(c byte) bool    { return c >= 'A' && c <= 'Z' }
func asciiAlpha(c byte) bool    { return asciiLower(c) || asciiUpper(c) }
func asciiAlnum(c byte) bool    { return asciiAlpha(c) || asciiDigit(c) }
func asciiHexLower(c byte) bool { return asciiDigit(c) || c >= 'a' && c <= 'f' }

func everyByte(s string, predicate func(byte) bool) bool {
	for i := 0; i < len(s); i++ {
		if !predicate(s[i]) {
			return false
		}
	}
	return true
}

func validSemver(s string) bool {
	parts := strings.Split(s, ".")
	if len(parts) != 3 {
		return false
	}
	for _, part := range parts {
		if part == "" || len(part) > 1 && part[0] == '0' || !everyByte(part, asciiDigit) {
			return false
		}
	}
	return true
}

func validDate(s string) bool {
	return len(s) == 10 && s[4] == '-' && s[7] == '-' &&
		everyByte(s[:4], asciiDigit) && everyByte(s[5:7], asciiDigit) &&
		everyByte(s[8:], asciiDigit)
}

func validDateTime(s string) bool {
	if len(s) < 19 || !validDate(s[:10]) || s[10] != 'T' && s[10] != 't' ||
		s[13] != ':' || s[16] != ':' ||
		!everyByte(s[11:13], asciiDigit) || !everyByte(s[14:16], asciiDigit) ||
		!everyByte(s[17:19], asciiDigit) {
		return false
	}
	pos := 19
	if pos < len(s) && s[pos] == '.' {
		pos++
		start := pos
		for pos < len(s) && asciiDigit(s[pos]) {
			pos++
		}
		if pos == start {
			return false
		}
	}
	if pos == len(s) {
		return false
	}
	if (s[pos] == 'Z' || s[pos] == 'z') && pos+1 == len(s) {
		return true
	}
	return pos+6 == len(s) && (s[pos] == '+' || s[pos] == '-') &&
		s[pos+3] == ':' && everyByte(s[pos+1:pos+3], asciiDigit) &&
		everyByte(s[pos+4:], asciiDigit)
}

func validUnprefixedName(s string) bool {
	if s == "" || !asciiLower(s[0]) {
		return false
	}
	return everyByte(s[1:], func(c byte) bool { return asciiLower(c) || asciiDigit(c) || c == '-' })
}

func validReverseDNS(s string) bool {
	parts := strings.Split(s, ".")
	if len(parts) < 2 {
		return false
	}
	for _, part := range parts {
		if !validUnprefixedName(part) {
			return false
		}
	}
	return true
}

func validClosureRecordField(s string) bool {
	parts := strings.Split(s, ".")
	for _, part := range parts {
		if part == "" || !everyByte(part, func(c byte) bool {
			return asciiAlnum(c) || c == '_' || c == '-'
		}) {
			return false
		}
	}
	return true
}

func validHex64(s string) bool { return len(s) == 64 && everyByte(s, asciiHexLower) }

func validSha256(s string) bool {
	return strings.HasPrefix(s, "sha256:") && validHex64(strings.TrimPrefix(s, "sha256:"))
}

func validAbstractionID(s string) bool {
	sep := strings.LastIndex(s, ".v")
	if sep < 1 || sep+2 >= len(s) || !everyByte(s[sep+2:], asciiDigit) {
		return false
	}
	base := s[:sep]
	if !asciiLower(base[0]) && !asciiDigit(base[0]) {
		return false
	}
	return everyByte(base[1:], func(c byte) bool {
		return asciiLower(c) || asciiDigit(c) || c == '.' || c == '_' || c == '-'
	})
}

func validAssertionID(s string) bool {
	if !strings.HasPrefix(s, "A-") || len(s) < 3 || !asciiAlnum(s[2]) {
		return false
	}
	return everyByte(s[3:], func(c byte) bool { return asciiAlnum(c) || c == '_' || c == '-' })
}

func asciiSpace(c byte) bool {
	return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f'
}

func trimASCIISpace(s string) string {
	start, end := 0, len(s)
	for start < end && asciiSpace(s[start]) {
		start++
	}
	for end > start && asciiSpace(s[end-1]) {
		end--
	}
	return s[start:end]
}

func validObservedLine(s string) bool {
	equal := strings.IndexByte(s, '=')
	if equal < 0 || !validAssertionID(strings.TrimRightFunc(s[:equal], func(r rune) bool {
		return r == ' ' || r == '\t' || r == '\n' || r == '\r' || r == '\f'
	})) {
		return false
	}
	right := trimASCIISpace(s[equal+1:])
	if !strings.HasPrefix(right, "observed(") || !strings.HasSuffix(right, ")") {
		return false
	}
	content := right[len("observed(") : len(right)-1]
	return content != "" && !strings.ContainsRune(content, ')')
}
