package main

import (
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"time"
)

func controls() error {
	if err := connectionControls(); err != nil {
		return err
	}
	for _, value := range []string{"https://storage.googleapis.com/osv-vulnerabilities/Go/all.zip", "https://storage.googleapis.com/osv-vulnerabilities/PyPI/all.zip", "https://storage.googleapis.com/osv-vulnerabilities/crates.io/all.zip"} {
		if !objectURL(value) {
			return errors.New("declared archive identity was lost")
		}
	}
	for _, value := range []string{"http://storage.googleapis.com/osv-vulnerabilities/Go/all.zip", "https://storage.googleapis.com/osv-vulnerabilities/Go/all.zip?extra=1", "https://storage.googleapis.com/osv-vulnerabilities/go/all.zip", "https://other.invalid/osv-vulnerabilities/Go/all.zip", "https://storage.googleapis.com/osv-vulnerabilities/Go/../PyPI/all.zip"} {
		if objectURL(value) {
			return errors.New("undeclared archive identity was admitted")
		}
	}
	cases := []struct{ name, expected string }{
		{"accepted", ""}, {"status", "HTTPS archive status or source differs"}, {"redirect", "HTTPS archive status or source differs"},
		{"empty", "HTTPS archive length is absent or exceeds its bound"}, {"oversize", "HTTPS archive length is absent or exceeds its bound"},
		{"missing-length", "HTTPS archive length is absent or exceeds its bound"}, {"truncated", "HTTPS archive body is incomplete or exceeds its bound"},
		{"encoding", "HTTPS archive encoding or range is unsupported"}, {"range", "HTTPS archive encoding or range is unsupported"},
		{"header-deadline", "HTTPS archive operation did not complete"}, {"body-deadline", "HTTPS archive body is incomplete or exceeds its bound"},
		{"duplicate-evidence", ""},
		{"invalid-header", "HTTPS archive header evidence is not UTF-8"},
	}
	completed := 0
	for _, control := range cases {
		var observed atomic.Int32
		var setup atomic.Bool
		handler := http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
			observed.Add(1)
			if request.Method != http.MethodGet || request.Header.Get("Cache-Control") != "no-cache" || request.TLS == nil {
				setup.Store(true)
				writer.WriteHeader(500)
				return
			}
			if control.name == "header-deadline" {
				<-request.Context().Done()
				return
			}
			writer.Header().Set("Content-Type", "application/zip")
			writer.Header().Set("Content-Length", "3")
			switch control.name {
			case "status":
				writer.WriteHeader(404)
				return
			case "redirect":
				writer.Header().Set("Location", "https://untrusted.invalid/object")
				writer.WriteHeader(302)
				return
			case "empty":
				writer.Header().Set("Content-Length", "0")
				return
			case "oversize":
				writer.Header().Set("Content-Length", "17")
				return
			case "truncated":
				writer.Header().Set("Content-Length", "4")
			case "encoding":
				writer.Header().Set("Content-Encoding", "gzip")
			case "range":
				writer.Header().Set("Content-Range", "bytes 0-2/3")
			case "missing-length":
				writer.Header().Del("Content-Length")
				writer.(http.Flusher).Flush()
			case "duplicate-evidence":
				writer.Header().Add("ETag", "first")
				writer.Header().Add("ETag", "second")
			case "invalid-header":
				writer.Header().Set("ETag", "\"\xff\"")
			case "body-deadline":
				writer.WriteHeader(200)
				writer.(http.Flusher).Flush()
				<-request.Context().Done()
				return
			}
			_, _ = io.WriteString(writer, "ZIP")
		})
		server := httptest.NewUnstartedServer(handler)
		server.Config.ErrorLog = log.New(io.Discard, "", 0)
		server.StartTLS()
		selected := server.Client().Transport.(*http.Transport).Clone()
		selected.DisableCompression = true
		ctx := context.Background()
		cancel := func() {}
		if strings.HasSuffix(control.name, "deadline") {
			ctx, cancel = context.WithTimeout(ctx, 50*time.Millisecond)
		}
		started := time.Now()
		body, receipt, err := retrieve(ctx, server.URL, selected, 16)
		elapsed := time.Since(started)
		cancel()
		selected.CloseIdleConnections()
		server.Close()
		if observed.Load() != 1 || setup.Load() {
			return fmt.Errorf("control setup did not exercise the expected HTTPS request: %s", control.name)
		}
		if control.expected != "" {
			if err == nil || err.Error() != control.expected {
				return fmt.Errorf("control %s did not witness intended refusal: %v", control.name, err)
			}
			if strings.HasSuffix(control.name, "deadline") && elapsed > time.Second {
				return errors.New("HTTPS deadline control exceeded its independent budget")
			}
		} else {
			if err != nil || string(body) != "ZIP" || receipt.Status != 200 || receipt.URL != server.URL || len(receipt.Headers["content-type"]) != 1 || receipt.Headers["content-type"][0] != "application/zip" {
				return errors.New("HTTPS positive control changed exact payload or metadata")
			}
			if control.name == "duplicate-evidence" && (len(receipt.Headers["etag"]) != 2 || receipt.Headers["etag"][0] != "first" || receipt.Headers["etag"][1] != "second") {
				return errors.New("transport silently collapsed duplicate advisory evidence")
			}
		}
		completed++
	}
	if completed != len(cases) {
		return errors.New("HTTPS control population did not execute")
	}
	// A real TLS endpoint succeeds with its pinned test root and fails without it.
	var attempts atomic.Int32
	server := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		attempts.Add(1)
		w.Header().Set("Content-Length", "3")
		_, _ = io.WriteString(w, "ZIP")
	}))
	server.Config.ErrorLog = log.New(io.Discard, "", 0)
	server.StartTLS()
	defer server.Close()
	selected := server.Client().Transport.(*http.Transport).Clone()
	selected.DisableCompression = true
	body, _, err := retrieve(context.Background(), server.URL, selected, 16)
	selected.CloseIdleConnections()
	if err != nil || string(body) != "ZIP" || attempts.Load() != 1 {
		return errors.New("TLS trust control positive setup failed")
	}
	untrusted := transport()
	_, _, err = retrieve(context.Background(), server.URL, untrusted, 16)
	untrusted.CloseIdleConnections()
	if err == nil || err.Error() != "HTTPS archive operation did not complete" || attempts.Load() != 1 {
		return errors.New("HTTPS transport did not enforce certificate trust")
	}
	for _, address := range []string{"http://control.invalid/object", "https://user@control.invalid/object", "https://control.invalid/object#fragment"} {
		_, _, err = retrieve(context.Background(), address, selected, 16)
		if err == nil || err.Error() != "HTTPS archive address is invalid" {
			return errors.New("invalid HTTPS address failed after its admission boundary")
		}
	}
	return nil
}

func connectionControls() error {
	// Stall a real TLS handshake, rather than delaying an HTTP handler.
	var hellos atomic.Int32
	release := make(chan struct{})
	server := httptest.NewUnstartedServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {}))
	server.Config.ErrorLog = log.New(io.Discard, "", 0)
	server.TLS = &tls.Config{MinVersion: tls.VersionTLS12, GetConfigForClient: func(*tls.ClientHelloInfo) (*tls.Config, error) {
		hellos.Add(1)
		<-release
		return nil, nil
	}}
	server.StartTLS()
	selected := server.Client().Transport.(*http.Transport).Clone()
	started := time.Now()
	_, _, err := retrieveWithin(context.Background(), server.URL, selected, 16, 100*time.Millisecond)
	elapsed := time.Since(started)
	close(release)
	selected.CloseIdleConnections()
	server.Close()
	if err == nil || err.Error() != "HTTPS archive operation did not complete" || hellos.Load() != 1 || elapsed > time.Second {
		return errors.New("connection budget did not cover the actual TLS handshake")
	}
	// Establishing TLS ends the connection budget; a later response is admitted
	// under the independent overall request deadline.
	server = httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		time.Sleep(100 * time.Millisecond)
		w.Header().Set("Content-Length", "3")
		_, _ = io.WriteString(w, "ZIP")
	}))
	server.StartTLS()
	selected = server.Client().Transport.(*http.Transport).Clone()
	body, _, err := retrieveWithin(context.Background(), server.URL, selected, 16, 50*time.Millisecond)
	selected.CloseIdleConnections()
	server.Close()
	if err != nil || string(body) != "ZIP" {
		return errors.New("connection deadline incorrectly governed an established response")
	}
	return nil
}
