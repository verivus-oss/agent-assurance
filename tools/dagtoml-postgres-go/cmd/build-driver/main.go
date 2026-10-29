// build-driver prepares a checked supplier tree outside the checkout.
package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

const goVersion = "go1.26.10"

type sourceFile struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
	Data   []byte `json:"-"`
}

func dependencyInventory(files []sourceFile) string {
	names := append([]sourceFile{}, files...)
	sort.Slice(names, func(i, j int) bool { return names[i].Path < names[j].Path })
	digest := sha256.New()
	digest.Write([]byte("dagtoml-postgres-dependencies-v1\x00"))
	for _, file := range names {
		for _, value := range []string{file.Path, file.SHA256} {
			var length [8]byte
			binary.BigEndian.PutUint64(length[:], uint64(len(value)))
			digest.Write(length[:])
			digest.Write([]byte(value))
		}
	}
	return hex.EncodeToString(digest.Sum(nil))
}

func population(root string) (_ []sourceFile, _ string, resultErr error) {
	confined, err := os.OpenRoot(root)
	if err != nil {
		return nil, "", err
	}
	defer func() { resultErr = errors.Join(resultErr, confined.Close()) }()
	var files []sourceFile
	err = fs.WalkDir(confined.FS(), ".", func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.IsDir() {
			return nil
		}
		if !entry.Type().IsRegular() {
			return errors.New("source population contains a nonregular entry")
		}
		data, err := confined.ReadFile(path)
		if err != nil {
			return err
		}
		digest := sha256.Sum256(data)
		files = append(files, sourceFile{Path: path, SHA256: hex.EncodeToString(digest[:]), Data: data})
		return nil
	})
	if err != nil {
		return nil, "", err
	}
	if len(files) == 0 {
		return nil, "", errors.New("source population is absent")
	}
	sort.Slice(files, func(i, j int) bool { return files[i].Path < files[j].Path })
	digest := sha256.New()
	if _, err = digest.Write([]byte("dagtoml-postgres-source-v1\x00")); err != nil {
		return nil, "", err
	}
	for _, file := range files {
		for _, value := range [][]byte{[]byte(file.Path), file.Data} {
			if err := binary.Write(digest, binary.BigEndian, uint64(len(value))); err != nil {
				return nil, "", err
			}
			if _, err := digest.Write(value); err != nil {
				return nil, "", err
			}
		}
	}
	return files, hex.EncodeToString(digest.Sum(nil)), nil
}

type limitedBuffer struct{ bytes.Buffer }

func (b *limitedBuffer) Write(value []byte) (int, error) {
	if b.Len()+len(value) > 32*1024*1024 {
		return 0, errors.New("build output exceeded its bound")
	}
	return b.Buffer.Write(value)
}

func run(root string, arguments ...string) ([]byte, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	command := exec.CommandContext(ctx, "go", arguments...) // #nosec G204 -- All operation vectors are authored here; no shell or connection data is accepted.
	command.Dir = root
	command.Env = append(os.Environ(), "GOTOOLCHAIN="+goVersion, "CGO_ENABLED=0", "GOWORK=off",
		"GOOS=linux", "GOARCH=amd64", "GOAMD64=v1", "GOEXPERIMENT=", "GOFLAGS=")
	var output limitedBuffer
	var diagnostics limitedBuffer
	command.Stdout = &output
	command.Stderr = &diagnostics
	if err := command.Run(); err != nil {
		transcript, recordErr := os.CreateTemp("", "dagtoml-postgres-build-*.json")
		if recordErr != nil {
			return nil, errors.New("cannot retain failed build transcript")
		}
		record := map[string]any{"command": command.Args, "cwd": root, "stdout": output.String(), "stderr": diagnostics.String()}
		encodeErr := json.NewEncoder(transcript).Encode(record)
		closeErr := transcript.Close()
		if encodeErr != nil || closeErr != nil {
			return nil, errors.New("cannot retain complete build transcript")
		}
		return nil, fmt.Errorf("pinned Go %s operation failed; tool transcript: %s", arguments[0], transcript.Name())
	}
	return output.Bytes(), nil
}

type edit struct {
	start, end int
	text       string
}

func transform(path string, passfile bool) error {
	source, err := os.ReadFile(path) // #nosec G304 -- Both callers select fixed supplier files within this build's private tree.
	if err != nil {
		return err
	}
	positions := token.NewFileSet()
	tree, err := parser.ParseFile(positions, path, source, parser.ParseComments)
	if err != nil {
		return errors.New("supplier Go source did not parse")
	}
	var edits []edit
	remove := func(node ast.Node) {
		edits = append(edits, edit{positions.Position(node.Pos()).Offset, positions.Position(node.End()).Offset, ""})
	}
	imports, handlers, removed, entries := 0, 0, 0, 0
	for _, declaration := range tree.Decls {
		if group, ok := declaration.(*ast.GenDecl); ok {
			for _, specification := range group.Specs {
				if specification, ok := specification.(*ast.TypeSpec); ok && passfile && specification.Name.Name == "Entry" {
					structure, ok := specification.Type.(*ast.StructType)
					if !ok {
						return errors.New("supplier passfile entry is not a struct")
					}
					at := positions.Position(structure.Fields.Closing).Offset
					edits = append(edits, edit{at, at, "\n literalStars [4]bool\n"})
					entries++
				}
				if dependency, ok := specification.(*ast.ImportSpec); ok {
					name, err := strconv.Unquote(dependency.Path.Value)
					if err != nil {
						return err
					}
					if name == "regexp" {
						remove(dependency)
						imports++
					}
				}
				if value, ok := specification.(*ast.ValueSpec); ok && passfile && len(value.Names) == 1 && value.Names[0].Name == "colonSplitterRegexp" {
					remove(group)
					removed++
				}
			}
		}
		function, ok := declaration.(*ast.FuncDecl)
		if !ok {
			continue
		}
		if passfile {
			body, found := map[string]string{"parseLine": passfileBody, "ReadPassfile": readPassfileBody, "FindPassword": findPasswordBody}[function.Name.Name]
			if found {
				edits = append(edits, edit{positions.Position(function.Body.Pos()).Offset, positions.Position(function.Body.End()).Offset, body})
				handlers++
			}
		}
		if !passfile {
			switch function.Name.Name {
			case "redactPW", "redactURLPassword", "uriStructureUnambiguous", "uriQueryStart":
				remove(function)
				removed++
			case "Error":
				if function.Recv == nil || len(function.Recv.List) != 1 {
					continue
				}
				pointer, ok := function.Recv.List[0].Type.(*ast.StarExpr)
				if !ok {
					continue
				}
				name, ok := pointer.X.(*ast.Ident)
				if ok && name.Name == "ParseConfigError" {
					edits = append(edits, edit{positions.Position(function.Body.Pos()).Offset, positions.Position(function.Body.End()).Offset, `{ return "cannot parse PostgreSQL connection parameters" }`})
					handlers++
				}
			}
		}
	}
	expectedRemoved, expectedHandlers, expectedEntries := 4, 1, 0
	if passfile {
		expectedRemoved, expectedHandlers, expectedEntries = 1, 3, 1
	}
	if imports != 1 || handlers != expectedHandlers || removed != expectedRemoved || entries != expectedEntries {
		return errors.New("supplier transformation population changed")
	}
	sort.Slice(edits, func(i, j int) bool { return edits[i].start > edits[j].start })
	for _, change := range edits {
		source = append(append(append([]byte{}, source[:change.start]...), []byte(change.text)...), source[change.end:]...)
	}
	return os.WriteFile(path, source, 0600) // #nosec G703 -- Rewrite the same fixed supplier file in the private build tree, never an input-selected output path.
}

// #nosec G101 -- These strings contain maintained parser source, with no credential values.
const passfileBody = `{
	if line=="" || strings.HasPrefix(line, "#") || strings.IndexByte(line,0)>=0 { return nil }
	parts := make([]string, 0, 5)
	literals:=make([]bool,0,5)
	start:=0
	var value strings.Builder
	for index := 0; index < len(line); index++ {
		character := line[index]
		if character == '\\' && index + 1 < len(line) {
			index++
			value.WriteByte(line[index])
		} else if character == ':' {
			parts = append(parts, value.String())
			literals=append(literals,value.String()=="*" && line[start:index]!="*")
			start=index+1
			value.Reset()
			if len(parts) > 4 { return nil }
		} else { value.WriteByte(character) }
	}
	parts = append(parts, value.String())
	if len(parts) != 5 { return nil }
	return &Entry{Hostname: parts[0], Port: parts[1], Database: parts[2], Username: parts[3], Password: parts[4],literalStars:[4]bool{literals[0],literals[1],literals[2],literals[3]}}
}`

// #nosec G101 -- This is the maintained file-reader body, not credential data.
const readPassfileBody = `{
	before,err:=os.Stat(path)
	if err!=nil { return nil,err }
	refused:=func() (*Passfile,error) { return nil,&os.PathError{Op:"read",Path:path,Err:os.ErrPermission} }
	if !before.Mode().IsRegular() || before.Mode().Perm()&0077!=0 { return refused() }
	file,err:=os.Open(path)
	if err!=nil { return nil,err }
	after,err:=file.Stat()
	if err!=nil || !os.SameFile(before,after) || !after.Mode().IsRegular() || after.Mode().Perm()&0077!=0 {
		if closeErr:=file.Close();closeErr!=nil { return nil,closeErr }
		return refused()
	}
	result,parseErr:=ParsePassfile(file)
	closeErr:=file.Close()
	if parseErr!=nil { return nil,parseErr }
	if closeErr!=nil { return nil,closeErr }
	return result,nil
}`

// #nosec G101 -- This is the maintained field-comparison body, not a password value.
const findPasswordBody = `{
	for _,entry:=range pf.Entries {
		values:=[4]string{entry.Hostname,entry.Port,entry.Database,entry.Username}
		wanted:=[4]string{hostname,port,database,username}
		matched:=true
		for index,value:=range values { if value!=wanted[index] && !(value=="*" && !entry.literalStars[index]) { matched=false;break } }
		if matched { return entry.Password }
	}
	return ""
}`

func requireNoMatcherImports(root string) error {
	count := 0
	err := filepath.WalkDir(root, func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.IsDir() || !strings.HasSuffix(path, ".go") {
			return nil
		}
		count++
		tree, err := parser.ParseFile(token.NewFileSet(), path, nil, parser.ParseComments)
		if err != nil {
			return errors.New("prepared supplier source is not valid Go")
		}
		for _, specification := range tree.Imports {
			name, err := strconv.Unquote(specification.Path.Value)
			if err != nil {
				return err
			}
			if name == "regexp" || strings.HasPrefix(name, "regexp/") {
				return errors.New("prepared supplier source retains a regex import")
			}
		}
		return nil
	})
	if err == nil && count == 0 {
		return errors.New("prepared Go source population is absent")
	}
	return err
}

func build(root, output string) (resultErr error) {
	sources, stamp, err := population(root)
	if err != nil {
		return err
	}
	work, err := os.MkdirTemp("", "dagtoml-postgres-build-")
	if err != nil {
		return err
	}
	defer func() { resultErr = errors.Join(resultErr, os.RemoveAll(work)) }()
	for _, source := range sources {
		target := filepath.Join(work, filepath.FromSlash(source.Path))
		if err := os.MkdirAll(filepath.Dir(target), 0700); err != nil {
			return err
		}
		if err := os.WriteFile(target, source.Data, 0600); err != nil {
			return err
		}
	}
	if _, err = run(work, "mod", "verify"); err != nil {
		return err
	}
	if _, err = run(work, "mod", "vendor"); err != nil {
		return err
	}
	if err = transform(filepath.Join(work, "vendor/github.com/jackc/pgx/v5/pgconn/errors.go"), false); err != nil {
		return err
	}
	if err = transform(filepath.Join(work, "vendor/github.com/jackc/pgpassfile/pgpass.go"), true); err != nil {
		return err
	}
	if err = graphControls(); err != nil {
		return err
	}
	if err = prepareSupplierControls(work); err != nil {
		return err
	}
	if err = requireNoMatcherImports(work); err != nil {
		return err
	}
	dependencies, _, err := population(filepath.Join(work, "vendor"))
	if err != nil {
		return err
	}
	vendorStamp := dependencyInventory(dependencies)
	roots, err := sourceRoots(append(append([]sourceFile{}, sources...), sourceFile{Path: "cmd/supplier-controls/main.go", Data: []byte(supplierControls)}))
	if err != nil {
		return err
	}
	metadata, err := run(work, append([]string{"list", "-buildvcs=false", "-mod=vendor", "-deps", "-json"}, roots...)...)
	if err != nil {
		return err
	}
	packages, err := checkedGraph(metadata, roots)
	if err != nil {
		return err
	}
	if _, err = run(work, append([]string{"vet", "-buildvcs=false", "-mod=vendor"}, roots...)...); err != nil {
		return err
	}
	control, err := run(work, "run", "-buildvcs=false", "-mod=vendor", "./cmd/supplier-controls")
	if err != nil {
		return err
	}
	if !bytes.Equal(control, []byte("native supplier controls passed\n")) {
		return errors.New("supplier controls did not report their executed success")
	}
	if err = os.MkdirAll(filepath.Dir(output), 0700); err != nil {
		return err
	}
	packageNames := make([]string, 0, len(packages))
	for name := range packages {
		packageNames = append(packageNames, name)
	}
	sort.Strings(packageNames)
	graphDigest := sha256.New()
	graphDigest.Write([]byte("dagtoml-postgres-graph-v1\x00"))
	for _, name := range packageNames {
		if err := binary.Write(graphDigest, binary.BigEndian, uint64(len(name))); err != nil {
			return err
		}
		graphDigest.Write([]byte(name))
	}
	graphStamp := hex.EncodeToString(graphDigest.Sum(nil))
	flags := "-X main.instrumentSHA=" + stamp + " -X main.dependenciesSHA=" + vendorStamp + " -X main.compiledGraphSHA=" + graphStamp
	if _, err = run(work, "build", "-buildvcs=false", "-mod=vendor", "-trimpath", "-ldflags", flags, "-o", output, "."); err != nil {
		return err
	}
	_, after, err := population(root)
	if err != nil || after != stamp {
		return errors.New("driver source moved during its build")
	}
	binaryData, err := os.ReadFile(output) // #nosec G304 -- Identify the executable just built at the operator-selected output path.
	if err != nil {
		return err
	}
	binarySHA := sha256.Sum256(binaryData)
	report := map[string]any{"source_sha256": stamp, "dependencies_sha256": vendorStamp, "compiled_graph_sha256": graphStamp, "binary_sha256": hex.EncodeToString(binarySHA[:]), "go_version": goVersion, "sources": sources, "prepared_dependencies": dependencies, "compiled_packages": packages, "transformations": []string{"pgconn ParseConfigError fixed diagnostic and retired redactors", "pgpassfile explicit escaped-field parser and retired matcher"}}
	data, err := json.Marshal(report)
	if err != nil {
		return err
	}
	return os.WriteFile(output+".build.json", append(data, '\n'), 0600)
}

func main() {
	output := flag.String("output", "", "absolute output path outside this source module")
	flag.Parse()
	root, err := os.Getwd()
	if err != nil || !filepath.IsAbs(*output) || flag.NArg() != 0 {
		fmt.Fprintln(os.Stderr, "build requires an absolute output path")
		os.Exit(2)
	}
	relative, err := filepath.Rel(root, *output)
	if err != nil || relative == ".." || !strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		fmt.Fprintln(os.Stderr, "build output must be outside source module")
		os.Exit(2)
	}
	if err = build(root, *output); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	fmt.Println("prepared native PostgreSQL driver and complete build identity")
}
