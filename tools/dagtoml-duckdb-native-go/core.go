package main

import (
	"bytes"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

const extensionHook = `#include <duckdb.hpp>
#include "duckdb/main/extension_helper.hpp"
#include "core_functions_extension.hpp"
#include "json_extension.hpp"
namespace duckdb {
void ExtensionHelper::LoadAllExtensions(DuckDB &db) {
 db.LoadStaticExtension<CoreFunctionsExtension>();
 db.LoadStaticExtension<JsonExtension>();
}
}
`

type coreBuild struct {
	Sources   []fileIdentity
	Targets   []string
	Directory string
}

func sourceToken(data []byte, name string) (bool, error) {
	tokens, err := cppTokens(data)
	if err != nil {
		return false, err
	}
	for _, token := range tokens {
		if token.text == name {
			return true, nil
		}
	}
	return false, nil
}

func prepareCore(data, refusal, lexer []byte) ([]byte, error) {
	regions, err := namespaceRegions(data, "duckdb_re2")
	if err != nil {
		return nil, err
	}
	if len(regions) != 47 {
		return nil, errors.New("native matcher namespace population differs from both pinned source versions")
	}
	var prepared []byte
	start := 0
	for index, region := range regions {
		prepared = append(prepared, data[start:region.Start]...)
		// The first five source regions declare the forward types and existing
		// public ABI. All subsequent matcher implementation regions are retired.
		if index < 5 {
			expected := []string{"RE2", "Regex", "StringPiece", "Prog", "RE2"}[index]
			found, err := sourceToken(data[region.Start:region.End], expected)
			if err != nil || !found {
				return nil, errors.New("native matcher public declaration population changed")
			}
			prepared = append(prepared, data[region.Start:region.End]...)
		}
		if index == 4 {
			prepared = append(prepared, refusal...)
		}
		start = region.End
	}
	prepared = append(prepared, data[start:]...)
	namespaces, err := namespaceRegions(prepared, "duckdb_libpgquery")
	if err != nil {
		return nil, err
	}
	var selected []sourceRegion
	for _, region := range namespaces {
		found, err := sourceToken(prepared[region.Start:region.End], "yy_accept")
		if err != nil {
			return nil, err
		}
		if found {
			selected = append(selected, region)
		}
	}
	if len(selected) != 1 {
		return nil, errors.New("native generated SQL scanner population changed")
	}
	scanner := selected[0]
	result := append(append(append([]byte{}, prepared[:scanner.Start]...), lexer...), prepared[scanner.End:]...)
	return result, nil
}

func buildCore(work, sdk, core, compiler string, data []byte) (result coreBuild, resultErr error) {
	workRoot, err := os.OpenRoot(work)
	if err != nil {
		return coreBuild{}, err
	}
	defer func() { resultErr = errors.Join(resultErr, workRoot.Close()) }()
	raw := filepath.Join(work, "core-archive")
	if err := extractZIP(data, raw, func(name string) (string, bool) {
		switch name {
		case "duckdb.cpp", "duckdb.hpp", "duckdb.h", "duckdb_extension.h":
			return name, true
		default:
			return "", false
		}
	}); err != nil {
		return coreBuild{}, err
	}
	members, err := files(raw)
	if err != nil || len(members) != 4 {
		return coreBuild{}, errors.New("native source core archive member population differs")
	}
	original, err := workRoot.ReadFile("core-archive/duckdb.cpp")
	if err != nil {
		return coreBuild{}, err
	}
	const noticeAnchor = "/*\n\n\n\n### THIRD PARTY LICENSE #1 ###"
	if bytes.Count(original, []byte(noticeAnchor)) != 1 {
		return coreBuild{}, errors.New("native core third-party notice boundary changed")
	}
	notice := append([]byte{}, original[bytes.Index(original, []byte(noticeAnchor)):]...)
	const stub = "void ExtensionHelper::LoadAllExtensions(DuckDB &db) {\n\t// nop\n}"
	if bytes.Count(original, []byte(stub)) != 1 || bytes.Count(original, []byte("#include <regex>")) != 1 {
		return coreBuild{}, errors.New("native source core preparation anchors differ")
	}
	original = bytes.Replace(original, []byte(stub), nil, 1)
	original = bytes.Replace(original, []byte("#include <regex>"), nil, 1)
	intermediate := filepath.Join(raw, "core-intermediate.cpp")
	if err = workRoot.WriteFile("core-archive/core-intermediate.cpp", original, 0600); err != nil {
		return coreBuild{}, err
	}
	engine := filepath.Join(sdk, "external/duckdb")
	include := []string{filepath.Join(engine, "src/include"), filepath.Join(engine, "extension/core_functions/include"), filepath.Join(engine, "extension/json/include")}
	third, err := os.ReadDir(filepath.Join(engine, "third_party"))
	if err != nil {
		return coreBuild{}, err
	}
	for _, entry := range third {
		if entry.IsDir() {
			include = append(include, filepath.Join(engine, "third_party", entry.Name()), filepath.Join(engine, "third_party", entry.Name(), "include"))
		}
	}
	base := []string{compiler, "-O0", "-g0", "-std=c++11", "-fPIC", "-pthread", "-DNDEBUG", "-DDUCKDB_BUILD_LIBRARY", "-DDUCKDB_DISABLE_EXTENSION_LOAD=1", "-DDUCKDB_EXTENSION_MAIN", "-DDUCKDB_EXTENSION_AUTOINSTALL_DEFAULT=0", "-DDUCKDB_EXTENSION_AUTOLOAD_DEFAULT=0", "-ffile-prefix-map=" + work + "=/dagtoml/duckdb-core"}
	for _, path := range include {
		base = append(base, "-I", path)
	}
	preprocessed := filepath.Join(work, "core-preprocessed.cpp")
	args := append(append([]string{}, base...), "-E", "-P", intermediate, "-o", preprocessed)
	record, err := commandRun(work, args, 10*time.Minute)
	if err != nil {
		return coreBuild{}, retainFailure(work, record)
	}
	body, err := workRoot.ReadFile("core-preprocessed.cpp")
	if err != nil || len(body) == 0 || len(body) > 128*1024*1024 {
		return coreBuild{}, errors.New("native preprocessed core subject is absent or exceeds its bound")
	}
	refusal, err := inputs.ReadFile("data/retired-matcher.hpp")
	if err != nil {
		return coreBuild{}, err
	}
	lexer, err := inputs.ReadFile("data/sql-lexer.hpp")
	if err != nil {
		return coreBuild{}, err
	}
	prepared, err := prepareCore(body, refusal, lexer)
	if err != nil {
		return coreBuild{}, err
	}
	sources := filepath.Join(work, "core-sources")
	if err = os.Mkdir(sources, 0700); err != nil {
		return coreBuild{}, err
	}
	if err = workRoot.WriteFile("core-sources/prepared.cpp", prepared, 0600); err != nil {
		return coreBuild{}, err
	}
	if err = workRoot.WriteFile("core-sources/static_extensions.cpp", []byte(extensionHook), 0600); err != nil {
		return coreBuild{}, err
	}
	if err = workRoot.WriteFile("core-sources/NOTICE", notice, 0600); err != nil {
		return coreBuild{}, err
	}
	before, err := files(sources)
	if err != nil {
		return coreBuild{}, err
	}
	targets := map[string]string{"core/prepared.cpp": filepath.Join(sources, "prepared.cpp"), "core/static_extensions.cpp": filepath.Join(sources, "static_extensions.cpp")}
	for _, extension := range []string{"core_functions", "json"} {
		count := 0
		err = filepath.WalkDir(filepath.Join(engine, "extension", extension), func(path string, entry fs.DirEntry, err error) error {
			if err != nil {
				return err
			}
			if entry.Type()&os.ModeSymlink != 0 {
				return errors.New("native extension source link refused")
			}
			if entry.Type().IsRegular() && strings.HasSuffix(path, ".cpp") {
				relative, err := filepath.Rel(sdk, path)
				if err != nil {
					return err
				}
				targets[filepath.ToSlash(relative)] = path
				count++
			}
			return nil
		})
		if err != nil {
			return coreBuild{}, err
		}
		if count == 0 {
			return coreBuild{}, errors.New("native required extension source population is absent")
		}
	}
	names := make([]string, 0, len(targets))
	for name := range targets {
		names = append(names, name)
	}
	sort.Strings(names)
	objects := filepath.Join(work, "core-objects")
	if err = os.Mkdir(objects, 0700); err != nil {
		return coreBuild{}, err
	}
	type outcome struct {
		name   string
		record commandRecord
		err    error
	}
	jobs := make(chan string, len(names))
	results := make(chan outcome, len(names))
	var failed atomic.Bool
	for _, name := range names {
		jobs <- name
	}
	close(jobs)
	var workers sync.WaitGroup
	// Keep the large core unit separate from the smaller supplier units while
	// retaining bounded ownership for every compiler process.
	for range 3 {
		workers.Go(func() {
			for name := range jobs {
				if failed.Load() {
					continue
				}
				args := append(append([]string{}, base...), "-c", targets[name], "-o", filepath.Join(objects, digest([]byte(name))+".o"))
				record, err := commandRun(work, args, 10*time.Minute)
				if err != nil {
					failed.Store(true)
				}
				results <- outcome{name, record, err}
			}
		})
	}
	workers.Wait()
	close(results)
	completed := map[string]bool{}
	var failures []outcome
	for result := range results {
		if result.err != nil {
			failures = append(failures, result)
			continue
		}
		path := filepath.Join(objects, digest([]byte(result.name))+".o")
		metadata, err := os.Stat(path)
		if err != nil || !metadata.Mode().IsRegular() || metadata.Size() == 0 {
			return coreBuild{}, errors.New("native core compiler did not produce its selected object")
		}
		completed[result.name] = true
	}
	if len(failures) > 0 {
		sort.Slice(failures, func(i, j int) bool { return failures[i].name < failures[j].name })
		return coreBuild{}, retainFailure(work, failures[0].record)
	}
	if len(completed) != len(names) {
		return coreBuild{}, errors.New("native core compilation population is incomplete")
	}
	if err = os.Mkdir(core, 0700); err != nil {
		return coreBuild{}, err
	}
	args = []string{compiler, "-shared", "-pthread", "-Wl,-z,relro,-z,now,-z,defs", "-Wl,--strip-all", "-o", filepath.Join(core, "libduckdb.so")}
	for _, name := range names {
		args = append(args, filepath.Join(objects, digest([]byte(name))+".o"))
	}
	args = append(args, "-ldl")
	record, err = commandRun(work, args, 10*time.Minute)
	if err != nil {
		return coreBuild{}, retainFailure(work, record)
	}
	after, err := files(sources)
	if err != nil || !sameFiles(before, after) {
		return coreBuild{}, errors.New("prepared native core source moved during compilation")
	}
	fmt.Printf("prepared source-built core and both required extensions from %d complete translation units\n", len(names))
	return coreBuild{before, names, sources}, nil
}
