// Build the existing native binding directly from pinned, prepared source.
package main

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"
)

const pinnedGo = "go1.26.10"

type fileIdentity struct {
	Path string `json:"path"`
	SHA  string `json:"sha256"`
}

func absolute(path string) bool {
	return filepath.IsAbs(path) && utf8.ValidString(path) && !strings.ContainsAny(path, "\x00\r\n\t")
}

func files(root string) (_ []fileIdentity, resultErr error) {
	confined, err := os.OpenRoot(root)
	if err != nil {
		return nil, err
	}
	defer func() { resultErr = errors.Join(resultErr, confined.Close()) }()
	var result []fileIdentity
	err = fs.WalkDir(confined.FS(), ".", func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.IsDir() {
			return nil
		}
		if !entry.Type().IsRegular() {
			return errors.New("prepared source has a linked or nonregular entry")
		}
		if !validPath(path) {
			return errors.New("prepared source path is invalid")
		}
		data, err := confined.ReadFile(path)
		if err != nil {
			return err
		}
		result = append(result, fileIdentity{path, digest(data)})
		return nil
	})
	if err != nil {
		return nil, err
	}
	if len(result) == 0 {
		return nil, errors.New("source population is absent")
	}
	sort.Slice(result, func(i, j int) bool { return result[i].Path < result[j].Path })
	return result, nil
}

func inventory(domain string, populations ...[]fileIdentity) string {
	hash := sha256.New()
	hash.Write([]byte(domain + "\x00"))
	for _, population := range populations {
		var size [8]byte
		binary.BigEndian.PutUint64(size[:], uint64(len(population)))
		hash.Write(size[:])
		for _, file := range population {
			for _, value := range []string{file.Path, file.SHA} {
				binary.BigEndian.PutUint64(size[:], uint64(len(value)))
				hash.Write(size[:])
				hash.Write([]byte(value))
			}
		}
	}
	return hex.EncodeToString(hash.Sum(nil))
}

type pythonInfo struct {
	Executable string `json:"executable"`
	ABI        string `json:"abi"`
	Include    string `json:"include"`
}

func python(executable, work string) (pythonInfo, error) {
	if !absolute(executable) {
		return pythonInfo{}, errors.New("python executable must be absolute")
	}
	program := "import sys; print(sys.implementation.name); print(sys.version_info.major); print(sys.version_info.minor); print(sys.implementation.cache_tag); print(sys.base_prefix); print(sys.abiflags); print(sys.maxsize)"
	record, err := commandRun(work, []string{executable, "-B", "-S", "-c", program}, 10*time.Second)
	if err != nil {
		return pythonInfo{}, retainFailure(work, record)
	}
	if !utf8.Valid(record.Stdout) {
		return pythonInfo{}, errors.New("python identity is not UTF-8")
	}
	fields := strings.Split(strings.TrimSuffix(string(record.Stdout), "\n"), "\n")
	if len(fields) != 7 || fields[0] != "cpython" || fields[1] != "3" || (fields[2] != "11" && fields[2] != "12" && fields[2] != "13") ||
		fields[3] != "cpython-3"+fields[2] || fields[5] != "" || fields[6] != "9223372036854775807" || !absolute(fields[4]) {
		return pythonInfo{}, errors.New("binding requires ordinary CPython 3.11 through 3.13 on Linux amd64")
	}
	include := filepath.Join(fields[4], "include", "python3."+fields[2])
	if metadata, err := os.Stat(filepath.Join(include, "Python.h")); err != nil || !metadata.Mode().IsRegular() {
		return pythonInfo{}, errors.New("selected Python installation has no matching development headers")
	}
	return pythonInfo{executable, fields[3], include}, nil
}

func retainFailure(work string, record commandRecord) error {
	data, err := json.Marshal(record)
	if err != nil {
		return err
	}
	path := filepath.Join(work, "failed-command.json")
	if err = os.WriteFile(path, append(data, '\n'), 0600); err != nil {
		return err
	}
	return fmt.Errorf("native build operation failed; raw tool transcript: %s", path)
}

func sameFiles(before, after []fileIdentity) bool {
	if len(before) != len(after) {
		return false
	}
	for index := range before {
		if before[index] != after[index] {
			return false
		}
	}
	return true
}

func build(sourceRoot, cache, output, version, interpreter string) (resultErr error) {
	if runtime.GOOS != "linux" || runtime.GOARCH != "amd64" || runtime.Version() != pinnedGo {
		return errors.New("native binding builder requires its pinned Linux amd64 Go toolchain")
	}
	declarations, err := loadInputs()
	if err != nil {
		return err
	}
	selected, present := declarations.Versions[version]
	if !present {
		return errors.New("native DuckDB version is unsupported")
	}
	own, err := files(sourceRoot)
	if err != nil {
		return err
	}
	work, err := os.MkdirTemp("", "dagtoml-duckdb-client-")
	if err != nil {
		return err
	}
	// Retain failures and their exact command transcripts for inspection.
	defer func() {
		if resultErr == nil {
			resultErr = os.RemoveAll(work)
		}
	}()
	python, err := python(interpreter, work)
	if err != nil {
		return err
	}
	sdkData, err := download(cache, selected.SDKURL, selected.SDKSHA)
	if err != nil {
		return err
	}
	coreData, err := download(cache, selected.CoreURL, selected.CoreSHA)
	if err != nil {
		return err
	}
	pybindData, err := download(cache, declarations.Pybind.URL, declarations.Pybind.SHA)
	if err != nil {
		return err
	}
	sdk, core, headers := filepath.Join(work, "sdk"), filepath.Join(work, "core"), filepath.Join(work, "pybind")
	if err = extractSDK(sdkData, sdk, selected); err != nil {
		return err
	}
	if err = extractZIP(coreData, core, func(name string) (string, bool) { return "libduckdb.so", name == "libduckdb.so" }); err != nil {
		return err
	}
	if err = extractZIP(pybindData, headers, func(name string) (string, bool) {
		if strings.HasPrefix(name, "pybind11/include/") && headerFile(name) {
			return strings.TrimPrefix(name, "pybind11/include/"), true
		}
		return "LICENSE", name == "pybind11-"+declarations.Pybind.Version+".dist-info/LICENSE"
	}); err != nil {
		return err
	}
	if err = stampModule(sdk); err != nil {
		return err
	}
	prepared, err := files(sdk)
	if err != nil {
		return err
	}
	pybindFiles, err := files(headers)
	if err != nil {
		return err
	}
	pythonFiles, err := files(python.Include)
	if err != nil {
		return err
	}
	coreFiles, err := files(core)
	if err != nil {
		return err
	}
	compiler, err := exec.LookPath("c++")
	if err != nil || !absolute(compiler) {
		return errors.New("a native C++ compiler is required for the existing binding")
	}
	compilerData, err := os.ReadFile(compiler) // #nosec G304 -- Fingerprint the resolved compiler executable.
	if err != nil {
		return err
	}
	compilerSHA := digest(compilerData)
	marker := inventory("dagtoml-duckdb-binding-v1", own, prepared, pybindFiles, pythonFiles, coreFiles, []fileIdentity{{"compiler", compilerSHA}, {"python-abi", digest([]byte(python.ABI))}})
	var sources []string
	for _, file := range prepared {
		if strings.HasPrefix(file.Path, "src/duckdb_py/") && strings.HasSuffix(file.Path, ".cpp") {
			sources = append(sources, file.Path)
		}
	}
	if len(sources) == 0 {
		return errors.New("native binding has no C++ source targets")
	}
	base := []string{compiler, "-O2", "-DNDEBUG", "-std=c++11", "-fPIC", "-fvisibility=hidden", "-fno-strict-aliasing", "-DDUCKDB_PYTHON_LIB_NAME=_duckdb", "-DDAGTOML_BINDING_IDENTITY=" + strconv.Quote(marker), "-ffile-prefix-map=" + work + "=/dagtoml/duckdb-client"}
	for _, path := range []string{"src/duckdb_py/include", "external/duckdb/src/include", "external/duckdb/third_party", "external/duckdb/third_party/re2", "external/duckdb/third_party/fast_float", "external/duckdb/third_party/utf8proc/include", "external/duckdb/third_party/libpg_query/include", "external/duckdb/third_party/fmt/include"} {
		base = append(base, "-I"+filepath.Join(sdk, path))
	}
	base = append(base, "-isystem", headers, "-isystem", python.Include)
	var objects []string
	for index, name := range sources {
		object := filepath.Join(work, fmt.Sprintf("binding-%03d.o", index))
		arguments := append(append([]string{}, base...), "-c", filepath.Join(sdk, name), "-o", object)
		record, err := commandRun(work, arguments, 5*time.Minute)
		if err != nil {
			return retainFailure(work, record)
		}
		metadata, err := os.Stat(object)
		if err != nil || !metadata.Mode().IsRegular() || metadata.Size() == 0 {
			return errors.New("compiler did not produce its selected object")
		}
		objects = append(objects, object)
	}
	if len(objects) != len(sources) {
		return errors.New("compiled source population is incomplete")
	}
	client := filepath.Join(work, "_duckdb.so")
	link := append([]string{compiler, "-shared", "-Wl,-z,relro,-z,now", "-o", client}, objects...)
	link = append(link, "-L"+core, "-lduckdb", "-Wl,--disable-new-dtags,-rpath,$ORIGIN")
	record, err := commandRun(work, link, 5*time.Minute)
	if err != nil {
		return retainFailure(work, record)
	}
	after, err := files(sdk)
	if err != nil || !sameFiles(prepared, after) {
		return errors.New("prepared native source moved during compilation")
	}
	for _, population := range []struct {
		root   string
		before []fileIdentity
	}{{headers, pybindFiles}, {python.Include, pythonFiles}, {core, coreFiles}} {
		after, err = files(population.root)
		if err != nil || !sameFiles(population.before, after) {
			return errors.New("native header or core input moved during compilation")
		}
	}
	after, err = files(sourceRoot)
	if err != nil || !sameFiles(own, after) {
		return errors.New("owned native recipe moved during compilation")
	}
	compilerAfter, err := os.ReadFile(compiler) // #nosec G304 -- Recheck the same resolved compiler executable.
	if err != nil || digest(compilerAfter) != compilerSHA {
		return errors.New("compiler executable moved during compilation")
	}
	if err = os.MkdirAll(output, 0700); err != nil {
		return err
	}
	clientData, err := os.ReadFile(client) // #nosec G304 -- Read the just-linked private native module.
	if err != nil {
		return err
	}
	coreBody, err := os.ReadFile(filepath.Join(core, "libduckdb.so")) // #nosec G304 -- Read the verified selected core member.
	if err != nil {
		return err
	}
	if err = publish(output, "_duckdb.so", clientData); err != nil {
		return err
	}
	if err = publish(output, "libduckdb.so", coreBody); err != nil {
		return err
	}
	for _, file := range prepared {
		name := filepath.Base(file.Path)
		if name != "LICENSE" && !strings.HasPrefix(name, "LICENSE.") && name != "NOTICE" && !strings.HasPrefix(name, "NOTICE.") {
			continue
		}
		data, err := os.ReadFile(filepath.Join(sdk, filepath.FromSlash(file.Path))) // #nosec G304 -- Captured regular supplier notice within the private prepared tree.
		if err != nil {
			return err
		}
		target := filepath.Join(output, "licenses", "sdk", filepath.FromSlash(filepath.Dir(file.Path)))
		if err = os.MkdirAll(target, 0700); err != nil {
			return err
		}
		if err = publish(target, name, data); err != nil {
			return err
		}
	}
	license, err := os.ReadFile(filepath.Join(headers, "LICENSE")) // #nosec G304 -- Fixed selected Pybind11 notice in the private header tree.
	if err != nil {
		return err
	}
	if err = os.MkdirAll(filepath.Join(output, "licenses", "pybind11"), 0700); err != nil {
		return err
	}
	if err = publish(filepath.Join(output, "licenses", "pybind11"), "LICENSE", license); err != nil {
		return err
	}
	proof := map[string]any{"schema_version": 1, "protocol": "dagtoml-duckdb-native-v1", "binding_identity": marker, "go_version": pinnedGo, "version": version, "python": python, "compiler_sha256": compilerSHA, "owned_sources": own, "prepared_sources": prepared, "pybind_headers": pybindFiles, "python_headers": pythonFiles, "core_files": coreFiles, "compiled_sources": sources, "binary_sha256": digest(clientData), "core_sha256": digest(coreBody), "sdk_archive_sha256": selected.SDKSHA, "core_archive_sha256": selected.CoreSHA, "pybind_archive_sha256": declarations.Pybind.SHA}
	encoded, err := json.Marshal(proof)
	if err != nil {
		return err
	}
	return publish(output, "binding-build.json", append(encoded, '\n'))
}

func publish(root, name string, data []byte) (resultErr error) {
	file, err := os.CreateTemp(root, ".native-client-")
	if err != nil {
		return err
	}
	temporary := file.Name()
	defer func() {
		if err := os.Remove(temporary); err != nil && !errors.Is(err, fs.ErrNotExist) {
			resultErr = errors.Join(resultErr, err)
		}
	}()
	_, writeErr := file.Write(data)
	closeErr := file.Close()
	if writeErr != nil || closeErr != nil {
		return errors.Join(writeErr, closeErr)
	}
	return os.Rename(temporary, filepath.Join(root, name))
}

func main() {
	version := flag.String("version", "", "exact declared native core version")
	interpreter := flag.String("python", "", "absolute CPython executable")
	output := flag.String("output", "", "absolute native artifact directory outside this source module")
	cache := flag.String("cache", "", "absolute digest-keyed supplier archive cache")
	selfCheck := flag.Bool("self-check", false, "execute current archive and process boundary controls")
	producer := flag.String("instrument-producer", "", "private producer for boundary controls")
	flag.Parse()
	if *producer != "" {
		if err := instrumentProducer(*producer); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		return
	}
	if *selfCheck {
		if err := controls(); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println("native build controls: current process/stream ownership and archive admission; SDK compilation, live database lanes and compiler/core policy audit skipped")
		return
	}
	root, err := os.Getwd()
	if err != nil {
		fmt.Fprintln(os.Stderr, "cannot identify native recipe root")
		os.Exit(2)
	}
	if flag.NArg() != 0 || !absolute(*output) || !absolute(*cache) || !absolute(*interpreter) {
		fmt.Fprintln(os.Stderr, "native build requires absolute Python, output and cache paths")
		os.Exit(2)
	}
	relative, err := filepath.Rel(root, *output)
	if err != nil || !strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		fmt.Fprintln(os.Stderr, "native artifacts must be outside the recipe module")
		os.Exit(2)
	}
	relative, err = filepath.Rel(root, *cache)
	if err != nil || !strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		fmt.Fprintln(os.Stderr, "native archive cache must be outside the recipe module")
		os.Exit(2)
	}
	if err = build(root, *cache, *output, *version, *interpreter); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println("built current prepared DuckDB binding, pinned native core and complete artifact proof")
}
