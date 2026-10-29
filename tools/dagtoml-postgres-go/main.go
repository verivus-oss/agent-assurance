// dagtoml-postgres-go owns one PostgreSQL session behind bounded, framed IO.
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"runtime"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/jackc/pgx/v5/pgconn"
)

const protocol = "dagtoml-postgres-v1"
const maxFrame = 32 * 1024 * 1024
const maxRows = 100000
const operationTimeout = 30 * time.Second

// Set only by the audited build command after it has patched supplier sources.
var instrumentSHA string
var dependenciesSHA string
var compiledGraphSHA string

type request struct {
	RequestID   uint64    `json:"request_id"`
	Operation   string    `json:"operation"`
	Destination string    `json:"destination,omitempty"`
	Database    *string   `json:"database,omitempty"`
	SQL         string    `json:"sql,omitempty"`
	Parameters  []*string `json:"parameters,omitempty"`
}

type response struct {
	RequestID        uint64      `json:"request_id"`
	Protocol         string      `json:"protocol"`
	SourceSHA        string      `json:"source_sha256,omitempty"`
	DependenciesSHA  string      `json:"dependencies_sha256,omitempty"`
	CompiledGraphSHA string      `json:"compiled_graph_sha256,omitempty"`
	GoVersion        string      `json:"go_version,omitempty"`
	Success          bool        `json:"success"`
	Closed           bool        `json:"closed"`
	Transaction      string      `json:"transaction"`
	HasRows          bool        `json:"has_rows"`
	Types            []uint32    `json:"types"`
	Rows             [][]*string `json:"rows"`
	SQLState         string      `json:"sqlstate,omitempty"`
	Message          string      `json:"message,omitempty"`
}

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

func scalarEscapes(data []byte) bool {
	inside := false
	hexValue := func(raw []byte) (uint16, bool) {
		if len(raw) != 4 {
			return 0, false
		}
		var value uint16
		for _, character := range raw {
			value *= 16
			switch {
			case character >= '0' && character <= '9':
				value += uint16(character - '0')
			case character >= 'a' && character <= 'f':
				value += uint16(character - 'a' + 10)
			case character >= 'A' && character <= 'F':
				value += uint16(character - 'A' + 10)
			default:
				return 0, false
			}
		}
		return value, true
	}
	for index := 0; index < len(data); index++ {
		if data[index] == '"' {
			inside = !inside
			continue
		}
		if !inside || data[index] != '\\' {
			continue
		}
		index++
		if index >= len(data) {
			return false
		}
		if data[index] != 'u' {
			continue
		}
		if index+5 > len(data) {
			return false
		}
		value, ok := hexValue(data[index+1 : index+5])
		if !ok {
			return false
		}
		index += 4
		if value >= 0xd800 && value <= 0xdbff {
			if index+7 > len(data) || data[index+1] != '\\' || data[index+2] != 'u' {
				return false
			}
			low, ok := hexValue(data[index+3 : index+7])
			if !ok || low < 0xdc00 || low > 0xdfff {
				return false
			}
			index += 6
		} else if value >= 0xdc00 && value <= 0xdfff {
			return false
		}
	}
	return !inside
}

func readRequest(reader io.Reader) (request, error) {
	var size uint32
	if err := binary.Read(reader, binary.BigEndian, &size); err != nil {
		return request{}, err
	}
	if size == 0 || size > maxFrame {
		return request{}, errors.New("invalid request frame size")
	}
	data := make([]byte, size)
	if _, err := io.ReadFull(reader, data); err != nil {
		return request{}, err
	}
	if !utf8.Valid(data) || !scalarEscapes(data) {
		return request{}, errors.New("request is not UTF-8")
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	var value request
	opening, err := decoder.Token()
	if err != nil || opening != json.Delim('{') {
		return request{}, errors.New("request is not an object")
	}
	seen := map[string]bool{}
	for decoder.More() {
		keyToken, err := decoder.Token()
		key, ok := keyToken.(string)
		if err != nil || !ok || seen[key] {
			return request{}, errors.New("ambiguous request member")
		}
		seen[key] = true
		var raw json.RawMessage
		if err = decoder.Decode(&raw); err != nil {
			return request{}, errors.New("invalid request value")
		}
		var target any
		switch key {
		case "request_id":
			target = &value.RequestID
		case "operation":
			target = &value.Operation
		case "destination":
			target = &value.Destination
		case "database":
			target = &value.Database
		case "sql":
			target = &value.SQL
		case "parameters":
			target = &value.Parameters
		default:
			return request{}, errors.New("unsupported request member")
		}
		if bytes.Equal(raw, []byte("null")) && key != "database" {
			return request{}, errors.New("null request member")
		}
		if err = json.Unmarshal(raw, target); err != nil {
			return request{}, errors.New("invalid request member type")
		}
	}
	closing, err := decoder.Token()
	if err != nil || closing != json.Delim('}') || !seen["operation"] || !seen["request_id"] || value.RequestID == 0 {
		return request{}, errors.New("incomplete request object")
	}
	allowed := map[string]bool{"operation": true, "request_id": true}
	switch value.Operation {
	case "connect":
		allowed["destination"], allowed["database"] = true, true
		if !seen["destination"] {
			return request{}, errors.New("connection destination is absent")
		}
	case "execute":
		allowed["sql"], allowed["parameters"] = true, true
		if !seen["sql"] {
			return request{}, errors.New("execution SQL is absent")
		}
	case "close":
	default:
		return request{}, errors.New("unsupported request operation")
	}
	for key := range seen {
		if !allowed[key] {
			return request{}, errors.New("request member belongs to a different operation")
		}
	}
	var extra any
	if decoder.Decode(&extra) != io.EOF {
		return request{}, errors.New("trailing request JSON")
	}
	return value, nil
}

func writeResponse(writer io.Writer, value response) error {
	value.Protocol = protocol
	data, err := json.Marshal(value)
	if err != nil {
		return errors.New("cannot encode response")
	}
	if len(data) > maxFrame {
		return errors.New("response exceeds frame bound")
	}
	if err := binary.Write(writer, binary.BigEndian, uint32(len(data))); err != nil {
		return err
	}
	_, err = writer.Write(data)
	return err
}

type session struct{ connection *pgconn.PgConn }

func (s *session) state() response {
	result := response{Success: true, Closed: s.connection == nil || s.connection.IsClosed(), Types: []uint32{}, Rows: [][]*string{}}
	if s.connection != nil {
		result.Transaction = string(s.connection.TxStatus())
	}
	return result
}

func (s *session) failure(err error) response {
	result := s.state()
	result.Success = false
	result.Message = "PostgreSQL operation failed"
	var databaseError *pgconn.PgError
	if errors.As(err, &databaseError) {
		result.SQLState = databaseError.Code
		result.Message = databaseError.Message
	}
	return result
}

func (s *session) close() {
	if s.connection != nil {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		// Failure to acknowledge close still abandons this private session.
		_ = s.connection.Close(ctx)
	}
}

func (s *session) connect(ctx context.Context, value request) response {
	if s.connection != nil || value.Destination == "" || strings.ContainsRune(value.Destination, 0) ||
		(value.Database != nil && strings.ContainsRune(*value.Database, 0)) {
		return s.failure(errors.New("invalid connection request"))
	}
	config, err := pgconn.ParseConfig(value.Destination)
	if err != nil {
		return s.failure(err)
	}
	if value.Database != nil {
		config.Database = *value.Database
	}
	config.ConnectTimeout = operationTimeout
	config.MaxProtocolMessageBodyLen = maxFrame
	config.RuntimeParams["client_encoding"] = "UTF8"
	connection, err := pgconn.ConnectConfig(ctx, config)
	if err != nil {
		return s.failure(err)
	}
	s.connection = connection
	return s.state()
}

func collect(reader *pgconn.ResultReader) (response, error) {
	result := response{Types: []uint32{}, Rows: [][]*string{}}
	for _, field := range reader.FieldDescriptions() {
		result.Types = append(result.Types, field.DataTypeOID)
	}
	result.HasRows = reader.FieldDescriptions() != nil
	bytesRead := len(result.Types) * 16
	for reader.NextRow() {
		if len(result.Rows) >= maxRows {
			return result, errors.New("row count exceeds its bound")
		}
		row := make([]*string, 0, len(result.Types))
		values := reader.Values()
		if len(values) != len(result.Types) {
			return result, errors.New("row shape differs from description")
		}
		for _, value := range values {
			bytesRead += len(value) + 8
			if bytesRead > maxFrame/8 {
				return result, errors.New("row bytes exceed response bound")
			}
			if value == nil {
				row = append(row, nil)
				continue
			}
			if !utf8.Valid(value) {
				return result, errors.New("result is not UTF-8")
			}
			text := string(value)
			row = append(row, &text)
		}
		result.Rows = append(result.Rows, row)
	}
	_, err := reader.Close()
	return result, err
}

func (s *session) execute(ctx context.Context, value request) response {
	if s.connection == nil || s.connection.IsClosed() || strings.ContainsRune(value.SQL, 0) {
		return s.failure(errors.New("invalid execution request"))
	}
	parameters := make([][]byte, len(value.Parameters))
	for index, parameter := range value.Parameters {
		if parameter != nil {
			if strings.ContainsRune(*parameter, 0) {
				return s.failure(errors.New("NUL in parameter"))
			}
			parameters[index] = []byte(*parameter)
		}
	}
	result := response{Types: []uint32{}, Rows: [][]*string{}}
	var err error
	if len(parameters) != 0 {
		result, err = collect(s.connection.ExecParams(ctx, value.SQL, parameters, nil, nil, nil))
	} else {
		results := s.connection.Exec(ctx, value.SQL)
		for results.NextResult() {
			result, err = collect(results.ResultReader())
			if err != nil {
				break
			}
		}
		if closeError := results.Close(); err == nil {
			err = closeError
		}
	}
	if err != nil {
		// If bounded collection fails, never reuse a partly consumed session.
		var databaseError *pgconn.PgError
		if !errors.As(err, &databaseError) {
			s.close()
		}
		return s.failure(err)
	}
	state := s.state()
	state.Types, state.Rows, state.HasRows = result.Types, result.Rows, result.HasRows
	return state
}

func serve(input io.Reader, output io.Writer) error {
	if !identity(instrumentSHA) || !identity(dependenciesSHA) || !identity(compiledGraphSHA) || runtime.Version() != "go1.26.10" {
		return errors.New("driver requires its pinned audited build")
	}
	s := &session{}
	defer s.close()
	if err := writeResponse(output, response{Success: true, Closed: true, SourceSHA: instrumentSHA,
		DependenciesSHA: dependenciesSHA, CompiledGraphSHA: compiledGraphSHA, GoVersion: runtime.Version()}); err != nil {
		return err
	}
	reader := bufio.NewReader(input)
	var previous uint64
	for {
		value, err := readRequest(reader)
		if errors.Is(err, io.EOF) {
			return nil
		}
		if err != nil {
			return errors.New("invalid driver request")
		}
		if previous == ^uint64(0) || value.RequestID != previous+1 {
			return errors.New("out of order driver request")
		}
		previous = value.RequestID
		ctx, cancel := context.WithTimeout(context.Background(), operationTimeout)
		var result response
		switch value.Operation {
		case "connect":
			result = s.connect(ctx, value)
		case "execute":
			result = s.execute(ctx, value)
		case "close":
			s.close()
			result = s.state()
		default:
			cancel()
			return errors.New("unsupported driver operation")
		}
		cancel()
		result.RequestID = value.RequestID
		if err := writeResponse(output, result); err != nil {
			return err
		}
		if value.Operation == "close" {
			return nil
		}
	}
}

func main() {
	if len(os.Args) != 1 {
		fmt.Fprintln(os.Stderr, "driver accepts framed standard input only")
		os.Exit(2)
	}
	if err := serve(os.Stdin, os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, "PostgreSQL driver could not complete its bounded protocol")
		os.Exit(2)
	}
}
