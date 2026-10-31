package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"go/parser"
	"go/token"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

func capsuleModule(files []sourceFile) (string, error) {
	module, version := "", ""
	for _, file := range files {
		if file.Path == "go.mod" {
			for _, line := range strings.Split(string(file.Data), "\n") {
				line = strings.TrimSpace(line)
				if line == "" || strings.HasPrefix(line, "//") {
					continue
				}
				fields := strings.Fields(line)
				if len(fields) != 2 {
					return "", errors.New("standard-library capsule module directive is unsupported")
				}
				switch {
				case fields[0] == "module" && module == "":
					module = fields[1]
				case fields[0] == "go" && version == "":
					version = fields[1]
				default:
					return "", errors.New("standard-library capsule contains a dependency or repeated directive")
				}
			}
		}
		for _, suffix := range []string{".s", ".S", ".c", ".h", ".cc", ".cpp", ".syso"} {
			if strings.HasSuffix(file.Path, suffix) {
				return "", errors.New("standard-library capsule retains unsupported native source")
			}
		}
		if !strings.HasSuffix(file.Path, ".go") {
			continue
		}
		tree, err := parser.ParseFile(token.NewFileSet(), file.Path, file.Data, parser.ImportsOnly)
		if err != nil {
			return "", errors.New("standard-library capsule Go source did not parse")
		}
		for _, imported := range tree.Imports {
			name, err := strconv.Unquote(imported.Path.Value)
			if err != nil || name == "unsafe" || name == "regexp" || strings.HasPrefix(name, "regexp/") {
				return "", errors.New("standard-library capsule retains an unsupported import")
			}
		}
	}
	if module == "" || strings.ContainsAny(module, "\"\\") || version != "1.26.10" {
		return "", errors.New("standard-library capsule module identity or Go pin is invalid")
	}
	return module, nil
}

func buildCapsule(builderRoot, source, output string) (resultErr error) {
	if err := capsuleControls(); err != nil {
		return err
	}
	if !filepath.IsAbs(source) || !filepath.IsAbs(output) {
		return errors.New("capsule source and output must be absolute")
	}
	for _, root := range []string{builderRoot, source} {
		relative, err := filepath.Rel(root, output)
		if err != nil || !strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
			return errors.New("capsule output must be outside both source modules")
		}
	}
	builderSources, builderStamp, err := population(builderRoot)
	if err != nil {
		return err
	}
	sources, stamp, err := population(source)
	if err != nil {
		return err
	}
	module, err := capsuleModule(sources)
	if err != nil {
		return err
	}
	roots, err := sourceRoots(sources)
	if err != nil || len(roots) != 1 || roots[0] != module {
		return errors.New("standard-library capsule requires exactly its root command")
	}
	work, err := os.MkdirTemp("", "dagtoml-stdlib-capsule-")
	if err != nil {
		return err
	}
	defer func() { resultErr = errors.Join(resultErr, os.RemoveAll(work)) }()
	prepared := filepath.Join(work, "source")
	if err = os.Mkdir(prepared, 0700); err != nil {
		return err
	}
	confined, err := os.OpenRoot(prepared)
	if err != nil {
		return err
	}
	defer func() { resultErr = errors.Join(resultErr, confined.Close()) }()
	for _, file := range sources {
		name := filepath.FromSlash(file.Path)
		if err = confined.MkdirAll(filepath.Dir(name), 0700); err != nil {
			return err
		}
		if err = confined.WriteFile(name, file.Data, 0600); err != nil {
			return err
		}
	}
	metadata, err := run(prepared, "list", "-buildvcs=false", "-mod=readonly", "-deps", "-json", module)
	if err != nil {
		return err
	}
	packages, err := checkedGraph(metadata, roots)
	if err != nil {
		return err
	}
	decoder := json.NewDecoder(bytes.NewReader(metadata))
	for {
		var item struct {
			ImportPath string
			Standard   bool
		}
		if err = decoder.Decode(&item); errors.Is(err, io.EOF) {
			break
		} else if err != nil {
			return err
		}
		if !item.Standard && item.ImportPath != module && !strings.HasPrefix(item.ImportPath, module+"/") {
			return errors.New("standard-library capsule compiled an external package")
		}
	}
	names := make([]string, 0, len(packages))
	for name := range packages {
		names = append(names, name)
	}
	sort.Strings(names)
	graph := sha256.New()
	graph.Write([]byte("dagtoml-stdlib-capsule-graph-v1\x00"))
	for _, name := range names {
		if err = binary.Write(graph, binary.BigEndian, uint64(len(name))); err != nil {
			return err
		}
		graph.Write([]byte(name))
	}
	graphStamp := hex.EncodeToString(graph.Sum(nil))
	if _, err = run(prepared, "vet", "-buildvcs=false", "-mod=readonly", "./..."); err != nil {
		return err
	}
	if err = os.MkdirAll(filepath.Dir(output), 0700); err != nil {
		return err
	}
	flags := "-X main.sourceSHA=" + stamp + " -X main.builderSHA=" + builderStamp + " -X main.graphSHA=" + graphStamp
	if _, err = run(prepared, "build", "-buildvcs=false", "-mod=readonly", "-trimpath", "-ldflags", flags, "-o", output, "."); err != nil {
		return err
	}
	observed, err := commandRun(work, []string{output, "--identity"}, 10*time.Second)
	if err != nil || len(observed.Stderr) != 0 {
		return errors.New("capsule did not execute its compiled identity operation")
	}
	var native struct {
		GoVersion string `json:"go_version"`
		Source    string `json:"source_sha256"`
		Builder   string `json:"builder_sha256"`
		Graph     string `json:"compiled_graph_sha256"`
	}
	if err = json.Unmarshal(observed.Stdout, &native); err != nil || native.GoVersion != goVersion || native.Source != stamp || native.Builder != builderStamp || native.Graph != graphStamp {
		return errors.New("capsule compiled identity differs from its complete build inputs")
	}
	for _, input := range []struct{ root, stamp string }{{builderRoot, builderStamp}, {source, stamp}, {prepared, stamp}} {
		_, after, err := population(input.root)
		if err != nil || after != input.stamp {
			return errors.New("capsule source or builder moved during compilation")
		}
	}
	data, err := os.ReadFile(output) // #nosec G304 -- The just-built executable at the explicit operator-selected output path.
	if err != nil {
		return err
	}
	digest := sha256.Sum256(data)
	report := map[string]any{"protocol": "dagtoml-stdlib-capsule-v1", "go_version": goVersion, "source_sha256": stamp, "builder_sha256": builderStamp, "compiled_graph_sha256": graphStamp, "sources": sources, "builder_sources": builderSources, "compiled_packages": names, "binary_sha256": hex.EncodeToString(digest[:])}
	encoded, err := json.Marshal(report)
	if err != nil {
		return err
	}
	return os.WriteFile(output+".build.json", append(encoded, '\n'), 0600)
}
