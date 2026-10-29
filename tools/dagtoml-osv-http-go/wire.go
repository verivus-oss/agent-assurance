package main

import (
	"bufio"
	"bytes"
	"context"
	"crypto/tls"
	"encoding/base64"
	"errors"
	"io"
	"net"
	"net/http"
	"net/textproto"
	"net/url"
	"strconv"
)

// The standard transport collapses identical Content-Length fields. Retain the
// original final header block so the consumer can still refuse repeated proof.
type wireTransport struct{ *http.Transport }

type headerConnection struct {
	net.Conn
	header         []byte
	total, interim int
	done           bool
}

func (connection *headerConnection) Read(output []byte) (int, error) {
	n, err := connection.Conn.Read(output)
	for _, value := range output[:n] {
		if connection.done {
			break
		}
		connection.total++
		if connection.total > 65536 {
			return 0, errors.New("HTTPS raw header population exceeds its bound")
		}
		connection.header = append(connection.header, value)
		if bytes.HasSuffix(connection.header, []byte("\r\n\r\n")) {
			status, _, parseErr := capturedHeaders(connection.header)
			if parseErr != nil {
				return 0, parseErr
			}
			if status >= 100 && status <= 199 && status != 101 {
				connection.interim++
				if connection.interim > 8 {
					return 0, errors.New("HTTPS interim response population exceeds its bound")
				}
				connection.header = nil
			} else {
				connection.done = true
			}
		}
	}
	return n, err
}

func capturedHeaders(data []byte) (int, http.Header, error) {
	reader := bufio.NewReader(bytes.NewReader(data))
	status, err := reader.ReadString('\n')
	if err != nil || len(status) < 13 || (status[:9] != "HTTP/1.1 " && status[:9] != "HTTP/1.0 ") || status[12] != ' ' {
		return 0, nil, errors.New("HTTPS raw status evidence is invalid")
	}
	code, err := strconv.Atoi(status[9:12])
	if err != nil || code < 100 || code > 599 {
		return 0, nil, errors.New("HTTPS raw status evidence is invalid")
	}
	headers, err := textproto.NewReader(reader).ReadMIMEHeader()
	if err != nil || reader.Buffered() != 0 {
		return 0, nil, errors.New("HTTPS raw header evidence is invalid")
	}
	return code, http.Header(headers), nil
}

func (selected *wireTransport) RoundTrip(request *http.Request) (*http.Response, error) {
	if request.URL == nil || request.URL.Scheme != "https" || request.URL.Hostname() == "" {
		return nil, errors.New("HTTPS wire request has no declared TLS peer")
	}
	inner := selected.Clone()
	inner.Proxy = nil
	inner.DisableKeepAlives = true
	var captured *headerConnection
	inner.DialTLSContext = func(ctx context.Context, network, address string) (net.Conn, error) {
		connection, err := selected.dial(ctx, request, network, address)
		if err != nil {
			return nil, err
		}
		captured = &headerConnection{Conn: connection}
		return captured, nil
	}
	response, err := inner.RoundTrip(request)
	if err != nil {
		inner.CloseIdleConnections()
		return nil, err
	}
	if captured == nil {
		closeErr := response.Body.Close()
		inner.CloseIdleConnections()
		return nil, errors.Join(errors.New("HTTPS raw header evidence is absent"), closeErr)
	}
	status, headers, proofErr := capturedHeaders(captured.header)
	if !captured.done || proofErr != nil || status != response.StatusCode {
		closeErr := response.Body.Close()
		inner.CloseIdleConnections()
		return nil, errors.Join(errors.New("HTTPS final header evidence differs"), closeErr)
	}
	response.Header = headers
	return response, nil
}

func (selected *wireTransport) dial(ctx context.Context, request *http.Request, network, address string) (_ net.Conn, resultErr error) {
	var proxy *url.URL
	if selected.Proxy != nil {
		var err error
		proxy, err = selected.Proxy(request)
		if err != nil {
			return nil, err
		}
	}
	if proxy != nil {
		if proxy.Hostname() == "" {
			return nil, errors.New("HTTPS proxy identity is absent")
		}
		switch proxy.Scheme {
		case "http", "https", "socks5", "socks5h":
		default:
			return nil, errors.New("HTTPS proxy scheme is unsupported")
		}
	}
	endpoint := address
	if proxy != nil {
		port := proxy.Port()
		if port == "" {
			switch proxy.Scheme {
			case "https":
				port = "443"
			case "socks5", "socks5h":
				port = "1080"
			default:
				port = "80"
			}
		}
		endpoint = net.JoinHostPort(proxy.Hostname(), port)
	}
	connection, err := selected.DialContext(ctx, network, endpoint)
	if err != nil {
		return nil, err
	}
	raw := connection
	stop := context.AfterFunc(ctx, func() { _ = raw.Close() })
	defer stop()
	defer func() {
		if resultErr != nil {
			resultErr = errors.Join(resultErr, raw.Close())
		}
	}()
	secure := func(peer net.Conn, hostname string) (net.Conn, error) {
		config := selected.TLSClientConfig.Clone()
		config.ServerName = hostname
		config.NextProtos = []string{"http/1.1"}
		target := tls.Client(peer, config)
		handshake := ctx
		cancel := func() {}
		if selected.TLSHandshakeTimeout > 0 {
			handshake, cancel = context.WithTimeout(ctx, selected.TLSHandshakeTimeout)
		}
		defer cancel()
		err := target.HandshakeContext(handshake)
		return target, err
	}
	if proxy != nil {
		switch proxy.Scheme {
		case "http", "https":
			if proxy.Scheme == "https" {
				connection, err = secure(connection, proxy.Hostname())
				if err != nil {
					return nil, err
				}
			}
			connection, err = connectTunnel(connection, address, proxy)
		case "socks5", "socks5h":
			err = socksTunnel(connection, address, proxy)
		default:
			err = errors.New("HTTPS proxy scheme is unsupported")
		}
		if err != nil {
			return nil, err
		}
	}
	hostname, _, err := net.SplitHostPort(address)
	if err != nil {
		return nil, err
	}
	return secure(connection, hostname)
}

type bufferedConnection struct {
	net.Conn
	reader *bufio.Reader
}

func (connection *bufferedConnection) Read(output []byte) (int, error) {
	return connection.reader.Read(output)
}

func connectTunnel(connection net.Conn, address string, proxy *url.URL) (net.Conn, error) {
	request := &http.Request{Method: http.MethodConnect, URL: &url.URL{Opaque: address}, Host: address, Header: make(http.Header)}
	if proxy.User != nil {
		password, _ := proxy.User.Password()
		request.Header.Set("Proxy-Authorization", "Basic "+base64.StdEncoding.EncodeToString([]byte(proxy.User.Username()+":"+password)))
	}
	if err := request.Write(connection); err != nil {
		return nil, err
	}
	reader := bufio.NewReader(connection)
	var block []byte
	for !bytes.HasSuffix(block, []byte("\r\n\r\n")) {
		if len(block) >= 65536 {
			return nil, errors.New("HTTPS proxy response exceeds its bound")
		}
		value, err := reader.ReadByte()
		if err != nil {
			return nil, err
		}
		block = append(block, value)
	}
	status, _, err := capturedHeaders(block)
	if err != nil || status != http.StatusOK {
		return nil, errors.New("HTTPS proxy did not establish the declared tunnel")
	}
	return &bufferedConnection{Conn: connection, reader: reader}, nil
}

func socksTunnel(connection net.Conn, address string, proxy *url.URL) error {
	method := byte(0)
	if proxy.User != nil {
		method = 2
	}
	if _, err := connection.Write([]byte{5, 1, method}); err != nil {
		return err
	}
	var response [2]byte
	if _, err := io.ReadFull(connection, response[:]); err != nil {
		return err
	}
	if response != [2]byte{5, method} {
		return errors.New("HTTPS SOCKS authentication method differs")
	}
	if proxy.User != nil {
		user := proxy.User.Username()
		password, _ := proxy.User.Password()
		if len(user) == 0 || len(user) > 255 || len(password) > 255 {
			return errors.New("HTTPS SOCKS credentials exceed their bounds")
		}
		message := append([]byte{1, byte(len(user))}, []byte(user)...)
		message = append(message, byte(len(password)))
		message = append(message, []byte(password)...)
		if _, err := connection.Write(message); err != nil {
			return err
		}
		if _, err := io.ReadFull(connection, response[:]); err != nil {
			return err
		}
		if response != [2]byte{1, 0} {
			return errors.New("HTTPS SOCKS authentication was refused")
		}
	}
	host, portText, err := net.SplitHostPort(address)
	if err != nil {
		return err
	}
	port, err := strconv.ParseUint(portText, 10, 16)
	if err != nil || port == 0 {
		return errors.New("HTTPS SOCKS port is invalid")
	}
	message := []byte{5, 1, 0}
	ip := net.ParseIP(host)
	switch {
	case ip.To4() != nil:
		message = append(message, 1)
		message = append(message, ip.To4()...)
	case ip.To16() != nil:
		message = append(message, 4)
		message = append(message, ip.To16()...)
	case len(host) > 0 && len(host) <= 255:
		message = append(message, 3, byte(len(host)))
		message = append(message, []byte(host)...)
	default:
		return errors.New("HTTPS SOCKS target is invalid")
	}
	message = append(message, byte(port>>8), byte(port))
	if _, err := connection.Write(message); err != nil {
		return err
	}
	var result [4]byte
	if _, err := io.ReadFull(connection, result[:]); err != nil {
		return err
	}
	if result[0] != 5 || result[1] != 0 || result[2] != 0 {
		return errors.New("HTTPS SOCKS tunnel was refused")
	}
	size := 0
	switch result[3] {
	case 1:
		size = 4
	case 4:
		size = 16
	case 3:
		var length [1]byte
		if _, err := io.ReadFull(connection, length[:]); err != nil {
			return err
		}
		size = int(length[0])
		if size == 0 {
			return errors.New("HTTPS SOCKS bound address is absent")
		}
	default:
		return errors.New("HTTPS SOCKS bound address is invalid")
	}
	if _, err := io.ReadFull(connection, make([]byte, size+2)); err != nil {
		return err
	}
	return nil
}
