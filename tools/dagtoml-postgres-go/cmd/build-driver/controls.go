package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"go/parser"
	"go/token"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type packageInfo struct {
	ImportPath string
	Imports    []string
	Deps       []string
	Match      []string
}

func sourceRoots(sources []sourceFile) ([]string, error) {
	module := ""
	for _, source := range sources {
		if source.Path != "go.mod" {
			continue
		}
		for _, line := range strings.Split(string(source.Data), "\n") {
			fields := strings.Fields(line)
			if len(fields) > 0 && fields[0] == "module" {
				if len(fields) != 2 || module != "" || strings.ContainsAny(fields[1], "\"\\") {
					return nil, errors.New("ambiguous source module identity")
				}
				module = fields[1]
			}
		}
	}
	if module == "" {
		return nil, errors.New("source module identity is absent")
	}
	roots := map[string]bool{}
	for _, source := range sources {
		if !strings.HasSuffix(source.Path, ".go") {
			continue
		}
		tree, err := parser.ParseFile(token.NewFileSet(), source.Path, source.Data, parser.PackageClauseOnly)
		if err != nil {
			return nil, errors.New("source package identity did not parse")
		}
		if tree.Name.Name != "main" {
			continue
		}
		name := module
		if directory := filepath.ToSlash(filepath.Dir(source.Path)); directory != "." {
			name += "/" + directory
		}
		roots[name] = true
	}
	result := make([]string, 0, len(roots))
	for name := range roots {
		result = append(result, name)
	}
	sort.Strings(result)
	if len(result) == 0 {
		return nil, errors.New("source entrypoint population is absent")
	}
	return result, nil
}

func checkedGraph(data []byte, roots []string) (map[string]bool, error) {
	decoder := json.NewDecoder(bytes.NewReader(data))
	packages := map[string]packageInfo{}
	for {
		var item packageInfo
		if err := decoder.Decode(&item); errors.Is(err, io.EOF) {
			break
		} else if err != nil {
			return nil, err
		}
		if item.ImportPath == "" || item.ImportPath == "regexp" || strings.HasPrefix(item.ImportPath, "regexp/") {
			return nil, errors.New("compiled graph has an absent identity or regex package")
		}
		if _, present := packages[item.ImportPath]; present {
			return nil, errors.New("compiled graph repeats a package")
		}
		packages[item.ImportPath] = item
	}
	if len(roots) == 0 {
		return nil, errors.New("compiled roots are absent")
	}
	complete := map[string]bool{}
	for _, root := range roots {
		if _, present := packages[root]; !present {
			return nil, errors.New("compiled root was omitted")
		}
		pending := []string{root}
		for len(pending) > 0 {
			name := pending[len(pending)-1]
			pending = pending[:len(pending)-1]
			if complete[name] {
				continue
			}
			item, present := packages[name]
			if !present {
				return nil, errors.New("compiled import was omitted")
			}
			complete[name] = true
			pending = append(pending, item.Imports...)
		}
	}
	if len(complete) != len(packages) {
		return nil, errors.New("compiled graph contains unaccounted packages")
	}
	for name, item := range packages {
		transitive := map[string]bool{}
		pending := append([]string{}, item.Imports...)
		for len(pending) > 0 {
			next := pending[len(pending)-1]
			pending = pending[:len(pending)-1]
			if next == name {
				return nil, errors.New("compiled graph contains a cycle")
			}
			if transitive[next] {
				continue
			}
			transitive[next] = true
			pending = append(pending, packages[next].Imports...)
		}
		if len(transitive) != len(item.Deps) {
			return nil, errors.New("compiled dependency enumeration differs from import closure")
		}
		seen := map[string]bool{}
		for _, dependency := range item.Deps {
			if seen[dependency] || !transitive[dependency] {
				return nil, errors.New("compiled dependency identity differs from import closure")
			}
			seen[dependency] = true
		}
	}
	return complete, nil
}

func graphControls() error {
	encode := func(values []packageInfo) []byte {
		var data bytes.Buffer
		for _, value := range values {
			encoded, err := json.Marshal(value)
			if err != nil {
				return nil
			}
			data.Write(encoded)
		}
		return data.Bytes()
	}
	valid := []packageInfo{{ImportPath: "root", Imports: []string{"leaf"}, Deps: []string{"leaf"}}, {ImportPath: "leaf"}}
	if result, err := checkedGraph(encode(valid), []string{"root"}); err != nil || len(result) != 2 || !result["root"] || !result["leaf"] {
		return errors.New("graph positive control failed")
	}
	invalid := [][]packageInfo{nil, valid[:1], valid[1:], append(append([]packageInfo{}, valid...), packageInfo{ImportPath: "unaccounted"}),
		{{ImportPath: "root", Imports: []string{"leaf"}}, {ImportPath: "leaf"}},
		{{ImportPath: "root", Imports: []string{"leaf"}, Deps: []string{"other"}}, {ImportPath: "leaf"}},
		{{ImportPath: "root", Imports: []string{"regexp"}, Deps: []string{"regexp"}}, {ImportPath: "regexp"}},
		{{ImportPath: "root", Imports: []string{"leaf"}, Deps: []string{"leaf"}}, {ImportPath: "leaf", Imports: []string{"root"}, Deps: []string{"root"}}}}
	for _, values := range invalid {
		if _, err := checkedGraph(encode(values), []string{"root"}); err == nil {
			return errors.New("incomplete or unsafe graph control was accepted")
		}
	}
	if _, err := checkedGraph(encode(valid), nil); err == nil {
		return errors.New("absent root control was accepted")
	}
	return nil
}

func prepareSupplierControls(work string) error {
	path := filepath.Join(work, "cmd/supplier-controls/main.go")
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	return os.WriteFile(path, []byte(supplierControls), 0600)
}

const supplierControls = `package main

import (
 "errors"
 "fmt"
 "os"
 "strings"
 "github.com/jackc/pgpassfile"
 "github.com/jackc/pgx/v5/pgconn"
)

func controls() error {
 cases:=[]struct{source string;expected []string}{
  {"host:5432:db:user:example",[]string{"host","5432","db","user","example"}},
  {"::::",[]string{"","","","",""}},
  {"host:5432:db:user: example ",[]string{"host","5432","db","user"," example "}},
  {"ho\\:st:5432:db:user:exa\\:mple\\\\tail",[]string{"ho:st","5432","db","user","exa:mple\\tail"}},
  {"\\host:5432:db:user:exa\\mple",[]string{"host","5432","db","user","example"}},
  {"#host:5432:db:user:example",nil},
  {"host:5432:db:user",nil},
  {"host:5432:db:user:example:extra",nil},
  {"host:5432:db:user:bad\x00value",nil},
 }
 executed:=0
 for _,control:=range cases {
  result,err:=pgpassfile.ParsePassfile(strings.NewReader(control.source+"\n"))
  if err!=nil { return errors.New("passfile fixture setup failed") }
  if control.expected==nil {
   if len(result.Entries)!=0 { return errors.New("invalid passfile record was accepted") }
  } else {
   if len(result.Entries)!=1 { return errors.New("accepted passfile record disappeared") }
   entry:=result.Entries[0]
   actual:=[]string{entry.Hostname,entry.Port,entry.Database,entry.Username,entry.Password}
   for index,value:=range actual { if value!=control.expected[index] { return errors.New("passfile value differs from independent expected bytes") } }
  }
  executed++
 }
 if executed!=len(cases) { return errors.New("passfile fixture population was incomplete") }
 literal,err:=pgpassfile.ParsePassfile(strings.NewReader("\\*:5432:db:user:example\n"))
 if err!=nil || literal.FindPassword("other","5432","db","user")!="" || literal.FindPassword("*","5432","db","user")!="example" { return errors.New("escaped wildcard lost its literal meaning") }
 wildcard,err:=pgpassfile.ParsePassfile(strings.NewReader("*:5432:db:user:example\n"))
 if err!=nil || wildcard.FindPassword("other","5432","db","user")!="example" { return errors.New("unescaped passfile wildcard stopped matching") }
 file,err:=os.CreateTemp("","dagtoml-passfile-control-")
 if err!=nil { return err }
 name:=file.Name()
 defer func(){_ = os.Remove(name)}()
 if _,err=file.WriteString("host:5432:db:user:example\n");err!=nil { _ = file.Close();return err }
 if err=file.Close();err!=nil { return err }
 if result,err:=pgpassfile.ReadPassfile(name);err!=nil || len(result.Entries)!=1 { return errors.New("private password file was refused") }
 if err=os.Chmod(name,0644);err!=nil { return err }
 if _,err:=pgpassfile.ReadPassfile(name);err==nil { return errors.New("insecure password file was accepted") }
 for _,source:=range []string{"postgres://example:example-value@host","host=example password='example-malformed"} {
  err:=pgconn.NewParseConfigError(source,source,errors.New(source))
  if err.Error()!="cannot parse PostgreSQL connection parameters" { return errors.New("parse error exposed connection input") }
 }
 return nil
}

func main(){
 if err:=controls();err!=nil { fmt.Fprintln(os.Stderr,err);os.Exit(1) }
 fmt.Println("native supplier controls passed")
}
`
