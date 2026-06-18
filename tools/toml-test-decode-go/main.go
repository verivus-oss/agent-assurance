// toml-test decoder shim for the Go primary validator's parser stack.
//
// Reads a TOML document on stdin and emits the toml-test "tagged JSON"
// format on stdout, exiting non-zero on parse rejection. It mirrors the
// stock BurntSushi/toml `cmd/toml-test-decoder` for the JSON emission,
// but FIRST runs a strict pre-parse with `github.com/pelletier/go-toml/v2`.
//
// Why two parsers:
//
//   - The Go primary validator (tools/dagtoml-validate-go) decodes with
//     BurntSushi/toml v1.6.0. BurntSushi is permissive on 13 toml-test 1.1
//     invalid fixtures (all dotted-key / inline-table redefinition cases)
//     that the Rust (`toml` 1.1) and Python (tomli) primaries correctly
//     reject. To close that cross-implementation strictness gap (issue #38,
//     contract C01) the Go side runs pelletier/go-toml/v2 as a STRICT GATE:
//     pelletier rejects all 13, and accepts the full 189-case valid corpus.
//
//   - BurntSushi still does the structural decode for the JSON emission,
//     because the stock BurntSushi decoder already round-trips all 189 valid
//     fixtures into the exact tagged JSON toml-test expects. Reusing that
//     emission path (reimplemented below — the upstream helper lives in an
//     internal package that cannot be imported) keeps the valid-corpus output
//     byte-for-byte identical while pelletier supplies the strictness.
//
// So: pelletier-strict-gate, then BurntSushi-tagged-JSON-emit. On a
// pelletier parse error we exit 1 before BurntSushi ever runs, which is how
// toml-test learns the input was rejected.
//
// This shim is the symmetric Go-side counterpart to
// tools/toml-test-decode-rs/. It has its own go.mod and imports no `unsafe`.
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"math"
	"os"
	"strconv"
	"time"

	burntsushi "github.com/BurntSushi/toml"
	pelletier "github.com/pelletier/go-toml/v2"
)

func main() {
	log.SetFlags(0)

	input, err := io.ReadAll(os.Stdin)
	if err != nil {
		log.Fatalf("toml-test-decode-go: failed to read stdin: %s", err)
	}

	// Strict gate: pelletier/go-toml/v2 is stricter than BurntSushi on the
	// dotted-key / inline-table redefinition cases. A parse error here means
	// "reject", so exit non-zero before touching BurntSushi. This is the
	// strictness that closes the issue #38 gap.
	var sink any
	if err := pelletier.Unmarshal(input, &sink); err != nil {
		log.Fatalf("toml-test-decode-go: strict parse error (pelletier/go-toml/v2): %s", err)
	}

	// Structural decode + tagged-JSON emission via BurntSushi, matching the
	// stock cmd/toml-test-decoder output exactly (it already passes all 189
	// valid fixtures). pelletier already accepted the input, so any error here
	// would be a genuine divergence between the two parsers — still treated as
	// a rejection.
	var decoded any
	if err := burntsushi.Unmarshal(input, &decoded); err != nil {
		log.Fatalf("toml-test-decode-go: structural decode error (BurntSushi/toml): %s", err)
	}

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(addTags(decoded)); err != nil {
		log.Fatalf("toml-test-decode-go: failed to encode JSON: %s", err)
	}
}

// addTags reimplements github.com/BurntSushi/toml/internal/tag.Add, which is
// in an internal package and cannot be imported here. It walks the value
// BurntSushi decoded into `any` and annotates scalars with the toml-test
// tagged-JSON {"type","value"} shape. The four datetime variants are
// distinguished by the time.Location name BurntSushi attaches when decoding
// local datetimes/dates/times (internal/tz.go sets these to FixedZone names
// "datetime-local" / "date-local" / "time-local"; anything else is an
// offset/zoned "datetime").
func addTags(data any) any {
	switch orig := data.(type) {
	case map[string]any:
		typed := make(map[string]any, len(orig))
		for k, v := range orig {
			typed[k] = addTags(v)
		}
		return typed
	case []map[string]any:
		typed := make([]any, len(orig))
		for i, v := range orig {
			typed[i] = addTags(v)
		}
		return typed
	case []any:
		typed := make([]any, len(orig))
		for i, v := range orig {
			typed[i] = addTags(v)
		}
		return typed
	case time.Time:
		switch orig.Location().String() {
		case "datetime-local":
			return tag("datetime-local", orig.Format("2006-01-02T15:04:05.999999999"))
		case "date-local":
			return tag("date-local", orig.Format("2006-01-02"))
		case "time-local":
			return tag("time-local", orig.Format("15:04:05.999999999"))
		default:
			return tag("datetime", orig.Format("2006-01-02T15:04:05.999999999Z07:00"))
		}
	case bool:
		return tag("bool", fmt.Sprintf("%v", orig))
	case string:
		return tag("string", orig)
	case int64:
		return tag("integer", fmt.Sprintf("%d", orig))
	case float64:
		switch {
		case math.IsNaN(orig):
			return tag("float", "nan")
		case math.IsInf(orig, 1):
			return tag("float", "inf")
		case math.IsInf(orig, -1):
			return tag("float", "-inf")
		default:
			return tag("float", strconv.FormatFloat(orig, 'g', -1, 64))
		}
	default:
		log.Fatalf("toml-test-decode-go: unknown decoded type: %T", data)
		return nil
	}
}

func tag(typeName string, data any) map[string]any {
	return map[string]any{
		"type":  typeName,
		"value": data,
	}
}
