package main

import (
	"context"
	"encoding/base64"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strconv"
	"sync/atomic"
	"time"
)

func fixtureRelay(left, right net.Conn) {
	completed := make(chan struct{}, 2)
	// The first EOF ends this one-request fixture. Closing both peers may
	// interrupt the opposite copy; payload and request counters prove delivery.
	go func() { _, _ = io.Copy(left, right); completed <- struct{}{} }()
	go func() { _, _ = io.Copy(right, left); completed <- struct{}{} }()
	<-completed
	_ = left.Close()
	_ = right.Close()
	<-completed
}

func fixtureSOCKS(target *url.URL, actualAddress string, auth, refuse bool, observed *atomic.Int32, done chan<- error) (net.Listener, error) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, err
	}
	go func() {
		err := func() error {
			peer, err := listener.Accept()
			if err != nil {
				return err
			}
			defer func() { _ = peer.Close() }()
			if err = peer.SetDeadline(time.Now().Add(3 * time.Second)); err != nil {
				return err
			}
			var greeting [3]byte
			if _, err = io.ReadFull(peer, greeting[:]); err != nil {
				return err
			}
			method := byte(0)
			if auth {
				method = 2
			}
			if greeting != [3]byte{5, 1, method} {
				return errors.New("SOCKS control received another greeting")
			}
			observed.Add(1)
			if refuse {
				_, err = peer.Write([]byte{5, 255})
				return err
			}
			if _, err = peer.Write([]byte{5, method}); err != nil {
				return err
			}
			if auth {
				var prefix [2]byte
				if _, err = io.ReadFull(peer, prefix[:]); err != nil {
					return err
				}
				if prefix != [2]byte{1, 7} {
					return errors.New("SOCKS control authentication prefix differs")
				}
				user := make([]byte, 7)
				if _, err = io.ReadFull(peer, user); err != nil {
					return err
				}
				var count [1]byte
				if _, err = io.ReadFull(peer, count[:]); err != nil {
					return err
				}
				secret := make([]byte, int(count[0]))
				if _, err = io.ReadFull(peer, secret); err != nil {
					return err
				}
				if string(user) != "fixture" || string(secret) != "control" {
					return errors.New("SOCKS control authentication data differs")
				}
				if _, err = peer.Write([]byte{1, 0}); err != nil {
					return err
				}
			}
			var request [4]byte
			if _, err = io.ReadFull(peer, request[:]); err != nil {
				return err
			}
			if request[0] != 5 || request[1] != 1 || request[2] != 0 {
				return errors.New("SOCKS control target type differs")
			}
			size := 4
			if request[3] == 3 {
				var length [1]byte
				if _, err = io.ReadFull(peer, length[:]); err != nil {
					return err
				}
				size = int(length[0])
			} else if request[3] != 1 {
				return errors.New("SOCKS control target type differs")
			}
			address := make([]byte, size)
			if _, err = io.ReadFull(peer, address); err != nil {
				return err
			}
			actualHost := string(address)
			if request[3] == 1 {
				actualHost = net.IP(address).String()
			}
			var portBytes [2]byte
			if _, err = io.ReadFull(peer, portBytes[:]); err != nil {
				return err
			}
			port, err := strconv.ParseUint(target.Port(), 10, 16)
			if err != nil {
				return err
			}
			if actualHost != target.Hostname() || uint64(portBytes[0])*256+uint64(portBytes[1]) != port {
				return errors.New("SOCKS control target differs")
			}
			if _, err = peer.Write([]byte{5, 0, 0, 1, 127, 0, 0, 1, 0, 0}); err != nil {
				return err
			}
			upstream, err := net.DialTimeout("tcp", actualAddress, time.Second)
			if err != nil {
				return err
			}
			fixtureRelay(peer, upstream)
			return nil
		}()
		done <- err
	}()
	return listener, nil
}

func proxyControls() error {
	var received atomic.Int32
	var invalid atomic.Bool
	target := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		received.Add(1)
		if r.TLS == nil || r.Header.Get("Proxy-Authorization") != "" {
			invalid.Store(true)
		}
		w.Header().Set("Content-Length", "3")
		_, _ = io.WriteString(w, "ZIP")
	}))
	defer target.Close()
	targetURL, err := url.Parse(target.URL)
	if err != nil {
		return err
	}
	actualAddress := targetURL.Host
	if len(target.Certificate().DNSNames) == 0 {
		return errors.New("TLS proxy fixture lacks a declared DNS identity")
	}
	for _, proxy := range []*url.URL{{Scheme: "ftp", Host: "control.invalid"}, {Scheme: "http"}} {
		selected := trustedTransport(target)
		selected.Proxy = http.ProxyURL(proxy)
		var dials atomic.Int32
		selected.DialContext = func(context.Context, string, string) (net.Conn, error) {
			dials.Add(1)
			return nil, errors.New("invalid proxy reached a dial")
		}
		_, _, err := retrieve(context.Background(), target.URL, selected, 16)
		selected.CloseIdleConnections()
		if err == nil || err.Error() != "HTTPS archive operation did not complete" || dials.Load() != 0 {
			return errors.New("invalid proxy admission did not precede network effects")
		}
	}
	completed := 0
	for _, scheme := range []string{"http", "https", "socks5", "socks5h"} {
		for _, mode := range []string{"plain", "auth", "refused", "domain"} {
			auth, refuse := mode == "auth", mode == "refused"
			declared := *targetURL
			if mode == "domain" {
				declared.Host = net.JoinHostPort(target.Certificate().DNSNames[0], targetURL.Port())
			}
			var observed atomic.Int32
			done := make(chan error, 1)
			selected := trustedTransport(target)
			var proxyURL *url.URL
			var closeProxy func()
			if scheme == "socks5" || scheme == "socks5h" {
				listener, err := fixtureSOCKS(&declared, actualAddress, auth, refuse, &observed, done)
				if err != nil {
					return err
				}
				proxyURL = &url.URL{Scheme: scheme, Host: listener.Addr().String()}
				closeProxy = func() { _ = listener.Close() }
			} else {
				handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
					observed.Add(1)
					expected := ""
					if auth {
						expected = "Basic " + base64.StdEncoding.EncodeToString([]byte("fixture:control"))
					}
					if r.Method != http.MethodConnect || r.Host != declared.Host || r.Header.Get("Proxy-Authorization") != expected {
						w.WriteHeader(500)
						done <- errors.New("HTTP proxy control request differs")
						return
					}
					if refuse {
						w.WriteHeader(407)
						done <- nil
						return
					}
					peer, _, err := w.(http.Hijacker).Hijack()
					if err != nil {
						done <- err
						return
					}
					upstream, err := net.DialTimeout("tcp", actualAddress, time.Second)
					if err != nil {
						_ = peer.Close()
						done <- err
						return
					}
					if _, err = io.WriteString(peer, "HTTP/1.1 200 Connection established\r\n\r\n"); err != nil {
						_ = peer.Close()
						_ = upstream.Close()
						done <- err
						return
					}
					fixtureRelay(peer, upstream)
					done <- nil
				})
				proxy := httptest.NewUnstartedServer(handler)
				proxy.Config.ErrorLog = log.New(io.Discard, "", 0)
				if scheme == "https" {
					proxy.StartTLS()
					selected.TLSClientConfig.RootCAs.AddCert(proxy.Certificate())
				} else {
					proxy.Start()
				}
				proxyURL, err = url.Parse(proxy.URL)
				if err != nil {
					proxy.Close()
					return err
				}
				closeProxy = proxy.Close
			}
			if auth {
				proxyURL.User = url.UserPassword("fixture", "control")
			}
			selected.Proxy = http.ProxyURL(proxyURL)
			selected.DialContext = func(ctx context.Context, network, address string) (net.Conn, error) {
				if address != proxyURL.Host {
					return nil, errors.New("proxy fixture attempted a direct or substituted route")
				}
				return (&net.Dialer{Timeout: time.Second}).DialContext(ctx, network, address)
			}
			before := received.Load()
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			body, _, requestErr := retrieve(ctx, declared.String(), selected, 16)
			cancel()
			selected.CloseIdleConnections()
			closeProxy()
			select {
			case setupErr := <-done:
				if setupErr != nil {
					return setupErr
				}
			case <-time.After(4 * time.Second):
				return errors.New("proxy control did not finish its owned relay")
			}
			if observed.Load() != 1 || invalid.Load() {
				return errors.New("proxy control skipped the declared tunnel or exposed proxy authentication to the target")
			}
			if refuse {
				if requestErr == nil || requestErr.Error() != "HTTPS archive operation did not complete" || received.Load() != before {
					return errors.New("refused proxy control reached the HTTPS target")
				}
			} else if requestErr != nil || string(body) != "ZIP" || received.Load() != before+1 {
				return fmt.Errorf("HTTPS proxy control failed: %s %s", scheme, mode)
			}
			completed++
		}
	}
	if completed != 16 || received.Load() != 12 {
		return errors.New("HTTPS proxy control population differs")
	}
	return nil
}
