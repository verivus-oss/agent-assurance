package main

import (
	"errors"
)

func cppClose(tokens []cppToken, start int, open, close string) (int, error) {
	if start < 0 || start >= len(tokens) || tokens[start].text != open {
		return 0, errors.New("native source delimiter subject differs")
	}
	depth := 0
	for index := start; index < len(tokens); index++ {
		if tokens[index].text == open {
			depth++
		}
		if tokens[index].text == close {
			depth--
			if depth == 0 {
				return index, nil
			}
		}
	}
	return 0, errors.New("native source delimiter is unfinished")
}
func cppSequence(tokens []cppToken, start int, words ...string) bool {
	if start < 0 || len(words) > len(tokens)-start {
		return false
	}
	for index, word := range words {
		if tokens[start+index].text != word {
			return false
		}
	}
	return true
}
func retireHTTPImplementation(data []byte) ([]byte, error) {
	tokens, err := cppTokens(data)
	if err != nil {
		return nil, err
	}
	classes := []sourceRegion{}
	for index := 0; index < len(tokens); index++ {
		if !cppSequence(tokens, index, "class", "HTTPLibClient", ":", "public", "HTTPClient", "{") {
			continue
		}
		end, err := cppClose(tokens, index+5, "{", "}")
		if err != nil {
			return nil, err
		}
		if end+1 >= len(tokens) || tokens[end+1].text != ";" {
			return nil, errors.New("retired native HTTP class boundary changed")
		}
		classes = append(classes, sourceRegion{Start: tokens[index].start, End: tokens[end+1].end})
		index = end + 1
	}
	if len(classes) == 0 {
		for _, token := range tokens {
			if token.text == "duckdb_httplib" || token.text == "HTTPLibClient" {
				return nil, errors.New("native HTTP implementation is partially retired")
			}
		}
		return data, nil
	}
	if len(classes) != 1 {
		return nil, errors.New("native HTTP implementation class population changed")
	}
	region := classes[0]
	data = append(append([]byte{}, data[:region.Start]...), data[region.End:]...)
	tokens, err = cppTokens(data)
	if err != nil {
		return nil, err
	}
	helpers := []sourceRegion{}
	for index := 0; index < len(tokens); index++ {
		if !cppSequence(tokens, index, "unique_ptr", "<", "HTTPResponse", ">", "TransformResponse", "(", "duckdb_httplib", ":", ":", "Result") {
			continue
		}
		end, err := cppClose(tokens, index+5, "(", ")")
		if err != nil {
			return nil, err
		}
		if end+1 >= len(tokens) || tokens[end+1].text != "{" {
			continue
		}
		end, err = cppClose(tokens, end+1, "{", "}")
		if err != nil {
			return nil, err
		}
		helpers = append(helpers, sourceRegion{Start: tokens[index].start, End: tokens[end].end})
		index = end
	}
	if len(helpers) != 1 {
		return nil, errors.New("retired native HTTP response helper population changed")
	}
	region = helpers[0]
	data = append(append([]byte{}, data[:region.Start]...), data[region.End:]...)
	tokens, err = cppTokens(data)
	if err != nil {
		return nil, err
	}
	factories := []sourceRegion{}
	for index := 0; index < len(tokens); index++ {
		if !cppSequence(tokens, index, "HTTPUtil", ":", ":", "InitializeClient", "(") {
			continue
		}
		end, err := cppClose(tokens, index+4, "(", ")")
		if err != nil {
			return nil, err
		}
		if end+1 >= len(tokens) || tokens[end+1].text != "{" {
			continue
		}
		start := end + 1
		end, err = cppClose(tokens, start, "{", "}")
		if err != nil {
			return nil, err
		}
		factories = append(factories, sourceRegion{Start: tokens[start].start, End: tokens[end].end})
		index = end
	}
	if len(factories) != 1 {
		return nil, errors.New("retired native HTTP factory population changed")
	}
	region = factories[0]
	refusal := []byte(`{ throw NotImplementedException("built-in HTTP transport is retired in the DAG-TOML database driver"); }`)
	result := append(append(append([]byte{}, data[:region.Start]...), refusal...), data[region.End:]...)
	tokens, err = cppTokens(result)
	if err != nil {
		return nil, err
	}
	for _, token := range tokens {
		if token.text == "duckdb_httplib" || token.text == "HTTPLibClient" {
			return nil, errors.New("retired native HTTP implementation still has a type consumer")
		}
	}
	return result, nil
}
