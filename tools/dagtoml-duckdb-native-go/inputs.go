// The pinned archives are data inputs, never Python packaging programs.
package main

import (
	"archive/tar"
	"archive/zip"
	"bytes"
	"compress/gzip"
	"context"
	"crypto/sha256"
	"embed"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"io/fs"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
	"unicode/utf8"
)

//go:embed data/inputs.json
var inputs embed.FS

const maxDownload = 128 * 1024 * 1024
const maxMember = 96 * 1024 * 1024
const maxExpansion = 512 * 1024 * 1024

type patch struct {
	Before       string      `json:"before_sha256"`
	After        string      `json:"after_sha256"`
	Replacements [][2]string `json:"replacements"`
}
type retiredHeader struct {
	Path   string `json:"path"`
	Before string `json:"before_sha256"`
}
type versionInput struct {
	Version            string           `json:"version"`
	SDKURL             string           `json:"sdk_url"`
	SDKSHA             string           `json:"sdk_sha256"`
	SupplierRepository string           `json:"supplier_repository"`
	SupplierCommit     string           `json:"supplier_commit"`
	Patches            map[string]patch `json:"patches"`
	Retired            []retiredHeader  `json:"retired_headers"`
	CoreURL            string           `json:"core_url"`
	CoreSHA            string           `json:"core_sha256"`
}
type headerInput struct {
	Version string `json:"version"`
	URL     string `json:"url"`
	SHA     string `json:"sha256"`
}
type sourceInputs struct {
	Schema   int                     `json:"schema_version"`
	Baseline string                  `json:"project_baseline"`
	Versions map[string]versionInput `json:"versions"`
	Pybind   headerInput             `json:"pybind"`
}

func digest(data []byte) string { sum := sha256.Sum256(data); return hex.EncodeToString(sum[:]) }

func identity(value string) bool {
	if len(value) != 64 {
		return false
	}
	for _, character := range value {
		if character < '0' || character > '9' && character < 'a' || character > 'f' {
			return false
		}
	}
	return true
}

func validPath(name string) bool {
	return fs.ValidPath(name) && name != "." && utf8.ValidString(name) && !strings.ContainsAny(name, "\\\x00\r\n\t")
}

func loadInputs() (sourceInputs, error) {
	data, err := inputs.ReadFile("data/inputs.json")
	if err != nil {
		return sourceInputs{}, err
	}
	var record sourceInputs
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err = decoder.Decode(&record); err != nil {
		return record, errors.New("supplier input declarations are malformed")
	}
	if err = decoder.Decode(&struct{}{}); !errors.Is(err, io.EOF) {
		return record, errors.New("supplier input declarations contain trailing data")
	}
	if record.Schema != 1 || len(record.Versions) != 2 || record.Pybind.Version != "2.13.6" {
		return record, errors.New("supplier input population differs")
	}
	if !identity(record.Pybind.SHA) {
		return record, errors.New("header archive identity is invalid")
	}
	for name, item := range record.Versions {
		if name != item.Version || (name != "1.5.0" && name != "1.5.3") || len(item.Patches) != 9 || len(item.Retired) != 3 {
			return record, errors.New("supplier repair population differs")
		}
		if !identity(item.SDKSHA) || !identity(item.CoreSHA) {
			return record, errors.New("native archive identity is invalid")
		}
		for path, change := range item.Patches {
			if !validPath(path) || !strings.HasPrefix(path, "src/duckdb_py/") || len(change.Replacements) == 0 || !identity(change.Before) || !identity(change.After) {
				return record, errors.New("supplier repair path or body is invalid")
			}
		}
	}
	return record, nil
}

func download(cache, url, expected string) (_ []byte, resultErr error) {
	if !strings.HasPrefix(url, "https://") || !identity(expected) {
		return nil, errors.New("archive requires its pinned HTTPS identity")
	}
	if err := os.MkdirAll(cache, 0700); err != nil {
		return nil, err
	}
	root, err := os.OpenRoot(cache)
	if err != nil {
		return nil, err
	}
	defer func() { resultErr = errors.Join(resultErr, root.Close()) }()
	if data, err := root.ReadFile(expected); err == nil {
		if digest(data) != expected {
			return nil, errors.New("cached supplier archive differs from its declared identity")
		}
		return data, nil
	} else if !errors.Is(err, fs.ErrNotExist) {
		return nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	request, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, errors.New("cannot create supplier archive request")
	}
	client := http.Client{Timeout: 2 * time.Minute, CheckRedirect: func(request *http.Request, prior []*http.Request) error {
		if request.URL.Scheme != "https" || len(prior) > 8 {
			return errors.New("supplier archive redirect refused")
		}
		return nil
	}}
	response, err := client.Do(request)
	if err != nil {
		return nil, errors.New("pinned supplier archive retrieval failed")
	}
	defer func() { resultErr = errors.Join(resultErr, response.Body.Close()) }()
	if response.StatusCode != http.StatusOK {
		return nil, errors.New("supplier archive did not return a complete object")
	}
	data, err := io.ReadAll(io.LimitReader(response.Body, maxDownload+1))
	if err != nil {
		return nil, errors.New("supplier archive body is incomplete")
	}
	if len(data) > maxDownload || digest(data) != expected {
		return nil, errors.New("supplier archive exceeds its bound or differs from its identity")
	}
	if err = publish(cache, expected, data); err != nil {
		return nil, err
	}
	return data, nil
}

func headerFile(name string) bool {
	for _, suffix := range []string{".h", ".hpp", ".hh", ".hxx", ".inc", ".ipp"} {
		if strings.HasSuffix(name, suffix) {
			return true
		}
	}
	return false
}

func selectedSDK(name string) bool {
	base := name[strings.LastIndexByte(name, '/')+1:]
	if base == "LICENSE" || strings.HasPrefix(base, "LICENSE.") || base == "NOTICE" || strings.HasPrefix(base, "NOTICE.") {
		return true
	}
	if strings.HasPrefix(name, "src/duckdb_py/") {
		return headerFile(name) || strings.HasSuffix(name, ".cpp")
	}
	for _, prefix := range []string{"external/duckdb/src/include/", "external/duckdb/third_party/"} {
		if strings.HasPrefix(name, prefix) {
			return headerFile(name)
		}
	}
	return name == "LICENSE"
}

func writeMember(root *os.Root, name string, data []byte) error {
	if !validPath(name) || len(data) > maxMember {
		return errors.New("prepared member path or size is invalid")
	}
	if parent := filepath.ToSlash(filepath.Dir(name)); parent != "." {
		if err := root.MkdirAll(parent, 0700); err != nil {
			return err
		}
	}
	return root.WriteFile(name, data, 0600)
}

func extractSDK(data []byte, output string, item versionInput) (resultErr error) {
	if err := os.Mkdir(output, 0700); err != nil {
		return err
	}
	root, err := os.OpenRoot(output)
	if err != nil {
		return err
	}
	defer func() { resultErr = errors.Join(resultErr, root.Close()) }()
	compressed, err := gzip.NewReader(bytes.NewReader(data))
	if err != nil {
		return errors.New("SDK is not its declared gzip archive")
	}
	defer func() { resultErr = errors.Join(resultErr, compressed.Close()) }()
	bounded := &io.LimitedReader{R: compressed, N: maxExpansion + 1}
	archive := tar.NewReader(bounded)
	seen := map[string]bool{}
	selected := 0
	expanded := int64(0)
	prefix := "duckdb-" + item.Version + "/"
	for {
		header, err := archive.Next()
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			return errors.New("SDK tar member is incomplete")
		}
		name := strings.TrimSuffix(header.Name, "/")
		if name == strings.TrimSuffix(prefix, "/") && header.Typeflag == tar.TypeDir {
			continue
		}
		if !strings.HasPrefix(name, prefix) {
			return errors.New("SDK member is outside its declared version root")
		}
		name = strings.TrimPrefix(name, prefix)
		if !validPath(name) || seen[name] || len(seen) >= 100000 {
			return errors.New("SDK member identity is invalid, repeated or exceeds its population bound")
		}
		seen[name] = true
		if header.Typeflag == tar.TypeDir {
			continue
		}
		if header.Typeflag != tar.TypeReg {
			return errors.New("SDK contains a linked or nonregular member")
		}
		expanded += header.Size
		if header.Size < 0 || header.Size > maxMember || expanded > maxExpansion {
			return errors.New("SDK expansion exceeds its bound")
		}
		if !selectedSDK(name) {
			continue
		}
		body, err := io.ReadAll(io.LimitReader(archive, maxMember+1))
		if err != nil || int64(len(body)) != header.Size {
			return errors.New("selected SDK member is incomplete")
		}
		if err = writeMember(root, name, body); err != nil {
			return err
		}
		selected++
	}
	tail, err := io.ReadAll(io.LimitReader(bounded, 1024*1024+1))
	if err != nil || len(tail) > 1024*1024 || bounded.N <= 0 {
		return errors.New("SDK gzip trailer is invalid or exceeds its expansion/padding bound")
	}
	for _, value := range tail {
		if value != 0 {
			return errors.New("SDK retains unaccounted data after its tar population")
		}
	}
	if selected == 0 {
		return errors.New("selected SDK source population is absent")
	}
	for name, change := range item.Patches {
		body, err := root.ReadFile(name)
		if err != nil {
			return err
		}
		if digest(body) != change.Before {
			return errors.New("supplier repair input differs from its captured source")
		}
		text := string(body)
		for _, replacement := range change.Replacements {
			if replacement[0] == "" || strings.Count(text, replacement[0]) == 0 {
				return errors.New("supplier repair did not select its declared source")
			}
			text = strings.ReplaceAll(text, replacement[0], replacement[1])
		}
		if digest([]byte(text)) != change.After {
			return errors.New("supplier repair differs from its captured result")
		}
		if err = root.WriteFile(name, []byte(text), 0600); err != nil {
			return err
		}
	}
	for _, retired := range item.Retired {
		if !validPath(retired.Path) {
			return errors.New("retired supplier header path is invalid")
		}
		body, err := root.ReadFile(retired.Path)
		if err != nil {
			return err
		}
		if digest(body) != retired.Before {
			return errors.New("retired supplier header identity differs")
		}
		if err = root.Remove(retired.Path); err != nil {
			return err
		}
	}
	return nil
}

func extractZIP(data []byte, output string, selectName func(string) (string, bool)) (resultErr error) {
	if err := os.Mkdir(output, 0700); err != nil {
		return err
	}
	root, err := os.OpenRoot(output)
	if err != nil {
		return err
	}
	defer func() { resultErr = errors.Join(resultErr, root.Close()) }()
	archive, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		return errors.New("supplier ZIP directory is invalid")
	}
	seen := map[string]bool{}
	selected := 0
	expanded := uint64(0)
	for _, member := range archive.File {
		name := strings.TrimSuffix(member.Name, "/")
		if !validPath(name) || seen[name] || len(seen) >= 100000 {
			return errors.New("supplier ZIP identity is invalid, repeated or exceeds its bound")
		}
		seen[name] = true
		if member.FileInfo().IsDir() {
			continue
		}
		if !member.Mode().IsRegular() {
			return errors.New("supplier ZIP contains a linked or nonregular member")
		}
		if member.UncompressedSize64 > maxMember || member.UncompressedSize64 > maxExpansion-expanded {
			return errors.New("supplier ZIP expansion exceeds its bound")
		}
		expanded += member.UncompressedSize64
		target, accepted := selectName(name)
		if !accepted {
			continue
		}
		reader, err := member.Open()
		if err != nil {
			return errors.New("supplier ZIP member cannot be opened")
		}
		body, readErr := io.ReadAll(io.LimitReader(reader, maxMember+1))
		closeErr := reader.Close()
		if readErr != nil || closeErr != nil || uint64(len(body)) != member.UncompressedSize64 {
			return errors.New("supplier ZIP member is incomplete")
		}
		if err = writeMember(root, target, body); err != nil {
			return err
		}
		selected++
	}
	if selected == 0 {
		return errors.New("selected supplier ZIP population is absent")
	}
	return nil
}
