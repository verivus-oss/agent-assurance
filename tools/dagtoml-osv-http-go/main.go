package main

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptrace"
	"net/url"
	"os"
	"runtime"
	"strings"
	"time"
	"unicode/utf8"
)

const maxArchive = 256 * 1024 * 1024
const footer = "\nDAGTOML_HTTP_META:"

type receipt struct {
	Status  int                 `json:"status"`
	URL     string              `json:"url"`
	Headers map[string][]string `json:"headers"`
}

const protocol = "dagtoml-osv-https-v1"

var sourceSHA, builderSHA, graphSHA string

type executableIdentity struct {
	Protocol   string `json:"protocol"`
	GoVersion  string `json:"go_version"`
	SourceSHA  string `json:"source_sha256"`
	BuilderSHA string `json:"builder_sha256"`
	GraphSHA   string `json:"compiled_graph_sha256"`
}

func validDigest(value string) bool {
	if len(value) != 64 {
		return false
	}
	for _, character := range value {
		if !(character >= '0' && character <= '9' || character >= 'a' && character <= 'f') {
			return false
		}
	}
	return true
}

func identity() (executableIdentity, error) {
	result := executableIdentity{protocol, runtime.Version(), sourceSHA, builderSHA, graphSHA}
	if runtime.GOOS != "linux" || runtime.GOARCH != "amd64" || result.GoVersion != "go1.26.10" || !validDigest(sourceSHA) || !validDigest(builderSHA) || !validDigest(graphSHA) {
		return result, errors.New("HTTPS executable lacks its pinned current build identity")
	}
	return result, nil
}

type objectID uint8

const (
	objectGo objectID = iota + 1
	objectPython
	objectRust
)

func selectObject(value string) (objectID, bool) {
	switch value {
	case "https://storage.googleapis.com/osv-vulnerabilities/Go/all.zip":
		return objectGo, true
	case "https://storage.googleapis.com/osv-vulnerabilities/PyPI/all.zip":
		return objectPython, true
	case "https://storage.googleapis.com/osv-vulnerabilities/crates.io/all.zip":
		return objectRust, true
	default:
		return 0, false
	}
}
func (id objectID) address() string {
	switch id {
	case objectGo:
		return "https://storage.googleapis.com/osv-vulnerabilities/Go/all.zip"
	case objectPython:
		return "https://storage.googleapis.com/osv-vulnerabilities/PyPI/all.zip"
	case objectRust:
		return "https://storage.googleapis.com/osv-vulnerabilities/crates.io/all.zip"
	default:
		return ""
	}
}
func objectURL(value string) bool { _, ok := selectObject(value); return ok }

func transport() *http.Transport {
	return &http.Transport{Proxy: http.ProxyFromEnvironment, DialContext: (&net.Dialer{Timeout: 10 * time.Second}).DialContext,
		TLSClientConfig: &tls.Config{MinVersion: tls.VersionTLS12}, TLSHandshakeTimeout: 10 * time.Second,
		ResponseHeaderTimeout: 10 * time.Second, DisableCompression: true, MaxResponseHeaderBytes: 65536}
}

func retrieve(ctx context.Context, address string, selected http.RoundTripper, limit int64) (_ []byte, _ receipt, resultErr error) {
	return retrieveWithin(ctx, address, selected, limit, 10*time.Second)
}

func retrieveWithin(ctx context.Context, address string, selected http.RoundTripper, limit int64, connectionBudget time.Duration) (_ []byte, _ receipt, resultErr error) {
	empty := receipt{}
	parsed, err := url.Parse(address)
	if err != nil || parsed.Scheme != "https" || parsed.Host == "" || parsed.User != nil || parsed.Fragment != "" {
		return nil, empty, errors.New("HTTPS archive address is invalid")
	}
	client := &http.Client{Transport: selected, Timeout: 90 * time.Second, CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return http.ErrUseLastResponse }}
	// The connection budget includes pool wait, DNS, TCP, proxies and TLS.
	// A separate overall client deadline still governs headers and body.
	connecting, cancel := context.WithCancel(ctx)
	defer cancel()
	connectionTimer := time.AfterFunc(connectionBudget, cancel)
	defer connectionTimer.Stop()
	connecting = httptrace.WithClientTrace(connecting, &httptrace.ClientTrace{
		GotConn: func(httptrace.GotConnInfo) { connectionTimer.Stop() },
	})
	request, err := http.NewRequestWithContext(connecting, http.MethodGet, address, nil)
	if err != nil {
		return nil, empty, errors.New("cannot construct archive request")
	}
	request.Header.Set("Cache-Control", "no-cache")
	response, err := client.Do(request)
	if err != nil {
		return nil, empty, errors.New("HTTPS archive operation did not complete")
	}
	defer func() { resultErr = errors.Join(resultErr, response.Body.Close()) }()
	if response.StatusCode != http.StatusOK || response.Request.URL.String() != address {
		return nil, empty, errors.New("HTTPS archive status or source differs")
	}
	if response.ContentLength <= 0 || response.ContentLength > limit {
		return nil, empty, errors.New("HTTPS archive length is absent or exceeds its bound")
	}
	if response.Header.Get("Content-Encoding") != "" || response.Header.Get("Content-Range") != "" {
		return nil, empty, errors.New("HTTPS archive encoding or range is unsupported")
	}
	body, err := io.ReadAll(io.LimitReader(response.Body, limit+1))
	if err != nil || int64(len(body)) != response.ContentLength || len(body) == 0 || int64(len(body)) > limit {
		return nil, empty, errors.New("HTTPS archive body is incomplete or exceeds its bound")
	}
	headers := map[string][]string{}
	for name, values := range response.Header {
		if !utf8.ValidString(name) {
			return nil, empty, errors.New("HTTPS archive header evidence is not UTF-8")
		}
		for _, value := range values {
			if !utf8.ValidString(value) {
				return nil, empty, errors.New("HTTPS archive header evidence is not UTF-8")
			}
		}
		headers[strings.ToLower(name)] = append([]string{}, values...)
	}
	return body, receipt{response.StatusCode, address, headers}, nil
}

func main() {
	if len(os.Args) == 2 && os.Args[1] == "--self-check" {
		if err := controls(); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		fmt.Println("HTTPS controls: exact bytes and headers, TLS/address/status/length/encoding/range and deadline controls; live archives, artifact identity and advisory equivalence skipped")
		return
	}
	stamp, identityErr := identity()
	if identityErr != nil {
		fmt.Fprintln(os.Stderr, identityErr)
		os.Exit(2)
	}
	if len(os.Args) == 2 && os.Args[1] == "--identity" {
		if err := json.NewEncoder(os.Stdout).Encode(stamp); err != nil {
			os.Exit(2)
		}
		return
	}

	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "requires one exact declared OSV ecosystem archive")
		os.Exit(2)
	}
	object, valid := selectObject(os.Args[1])
	if !valid {
		os.Exit(2)
	}
	selected := transport()
	defer selected.CloseIdleConnections()
	body, proof, err := retrieve(context.Background(), object.address(), selected, maxArchive)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	metadata, err := json.Marshal(proof)
	if err != nil || len(metadata)+len(footer) > 65536 {
		fmt.Fprintln(os.Stderr, "archive receipt exceeds its bound")
		os.Exit(2)
	}
	if _, err = os.Stdout.Write(body); err == nil {
		_, err = io.WriteString(os.Stdout, footer)
	}
	if err == nil {
		_, err = os.Stdout.Write(metadata)
	}
	if err != nil {
		os.Exit(2)
	}
}
