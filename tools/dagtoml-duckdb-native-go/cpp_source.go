package main

import (
	"bytes"
	"errors"
	"strings"
)

type cppToken struct {
	start, end int
	text       string
}
type sourceRegion struct {
	Start int    `json:"start_byte"`
	End   int    `json:"end_byte"`
	SHA   string `json:"sha256"`
	File  string `json:"capture"`
}

func cppWord(value byte) bool {
	return value == '_' || value >= 'a' && value <= 'z' || value >= 'A' && value <= 'Z' || value >= '0' && value <= '9' || value >= 128
}
func cppLiteral(data []byte, quote int, raw bool) (int, error) {
	if raw {
		open := quote + 1
		for open < len(data) && data[open] != '(' {
			if open-quote > 16 || data[open] <= 32 || data[open] == '\\' || data[open] == ')' {
				return 0, errors.New("invalid C++ raw literal delimiter")
			}
			open++
		}
		if open >= len(data) {
			return 0, errors.New("native C++ raw literal is unfinished")
		}
		closing := append(append([]byte{')'}, data[quote+1:open]...), '"')
		end := bytes.Index(data[open+1:], closing)
		if end < 0 {
			return 0, errors.New("native C++ raw literal is unfinished")
		}
		return open + 1 + end + len(closing), nil
	}
	delimiter := data[quote]
	for index := quote + 1; index < len(data); index++ {
		if data[index] == '\\' {
			index++
			continue
		}
		if data[index] == delimiter {
			return index + 1, nil
		}
	}
	return 0, errors.New("native C++ quoted literal is unfinished")
}
func cppTokens(data []byte) ([]cppToken, error) {
	var tokens []cppToken
	for index := 0; index < len(data); {
		value := data[index]
		if value == ' ' || value == '\n' || value == '\r' || value == '\t' || value == '\v' || value == '\f' {
			index++
			continue
		}
		if value == '#' {
			for index < len(data) && data[index] != '\n' {
				index++
			}
			continue
		}
		if index+1 < len(data) && string(data[index:index+2]) == "//" {
			index += 2
			for index < len(data) && data[index] != '\n' {
				index++
			}
			continue
		}
		if index+1 < len(data) && string(data[index:index+2]) == "/*" {
			end := bytes.Index(data[index+2:], []byte("*/"))
			if end < 0 {
				return nil, errors.New("native C++ block comment is unfinished")
			}
			index += end + 4
			continue
		}
		start := index
		if value == '\'' || value == '"' {
			end, err := cppLiteral(data, index, false)
			if err != nil {
				return nil, err
			}
			tokens = append(tokens, cppToken{start, end, "literal"})
			index = end
			continue
		}
		if value >= '0' && value <= '9' {
			index++
			for index < len(data) && (cppWord(data[index]) || data[index] == '.' || data[index] == '\'' && index+1 < len(data) && cppWord(data[index+1])) {
				index++
			}
			tokens = append(tokens, cppToken{start, index, "number"})
			continue
		}
		if cppWord(value) {
			index++
			for index < len(data) && cppWord(data[index]) {
				index++
			}
			word := string(data[start:index])
			if index < len(data) && (data[index] == '\'' || data[index] == '"') && (word == "L" || word == "u" || word == "U" || word == "u8" || word == "R" || word == "LR" || word == "uR" || word == "UR" || word == "u8R") {
				end, err := cppLiteral(data, index, strings.HasSuffix(word, "R"))
				if err != nil {
					return nil, err
				}
				tokens = append(tokens, cppToken{start, end, "literal"})
				index = end
				continue
			}
			tokens = append(tokens, cppToken{start, index, word})
			continue
		}
		token := string(value)
		index++
		if index < len(data) {
			pair := string(data[start : index+1])
			switch pair {
			case "<%":
				token = "{"
				index++
			case "%>":
				token = "}"
				index++
			}
		}
		tokens = append(tokens, cppToken{start, index, token})
	}
	return tokens, nil
}
func namespaceRegions(data []byte, name string) ([]sourceRegion, error) {
	tokens, err := cppTokens(data)
	if err != nil {
		return nil, err
	}
	var regions []sourceRegion
	for index := 0; index < len(tokens); index++ {
		if tokens[index].text != "namespace" || index+1 >= len(tokens) || tokens[index+1].text != name {
			continue
		}
		open := index + 2
		for open < len(tokens) && tokens[open].text != "{" && tokens[open].text != ";" && tokens[open].text != "=" {
			open++
		}
		if open == len(tokens) {
			return nil, errors.New("native C++ namespace declaration is unfinished")
		}
		if tokens[open].text != "{" {
			continue
		}
		depth := 1
		end := open + 1
		for ; end < len(tokens); end++ {
			if tokens[end].text == "{" {
				depth++
			}
			if tokens[end].text == "}" {
				depth--
				if depth == 0 {
					break
				}
			}
		}
		if depth != 0 {
			return nil, errors.New("native C++ namespace region is unbalanced")
		}
		region := sourceRegion{Start: tokens[index].start, End: tokens[end].end}
		region.SHA = digest(data[region.Start:region.End])
		regions = append(regions, region)
		index = end
	}
	if len(regions) == 0 {
		return nil, errors.New("the expected source namespace is absent")
	}
	return regions, nil
}
