// dagtoml-duckdb-go — Go counterpart of tools/dagtoml-duckdb. Builds a
// .duckdb artifact from the checked-in reference/database/duckdb/{schema,
// seed}.sql by orchestrating the duckdb CLI and verifies the resulting
// row counts.
//
// Safe Go: this file imports only the standard library. There is no
// `import "unsafe"`. The CI safety check (validators/check_safe_tools.sh)
// greps for `"unsafe"` imports across tools/ and fails the build if any
// appear. Do not introduce one without removing this comment AND
// updating the policy.
//
// Usage:
//
//	dagtoml-duckdb-go [--repo-root <path>] [-o <output.duckdb>] [--duckdb <cli>]
//	dagtoml-duckdb-go verify -o <output.duckdb> [--duckdb <cli>]
//
// Requires the `duckdb` CLI on PATH (or pass --duckdb <cli>); install
// from https://duckdb.org/.
package main

import (
	"bytes"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

// expectedCounts mirrors reference/database/MANIFEST.toml
// `[verification.duckdb] expected_seed_counts` and the Rust binary's
// EXPECTED_COUNTS. Gated by `validators/check_attribute_values.py` —
// drift here vs MANIFEST or vs the actual seed file rows is a CI
// failure.
var expectedCounts = []struct {
	table string
	want  int64
}{
	{"kind_descriptor", 23},
	{"entity_kind_descriptor", 27},
	{"relation_descriptor", 31},
	{"attribute_vocabulary", 50},
	{"attribute_value_allowed", 152},
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "dagtoml-duckdb-go:", err)
		os.Exit(1)
	}
}

func run() error {
	var (
		repoRoot   string
		output     string
		duckdbCLI  string
		subcommand string
	)
	fs := flag.NewFlagSet("dagtoml-duckdb-go", flag.ContinueOnError)
	fs.StringVar(&repoRoot, "repo-root", ".", "path to the repo root")
	fs.StringVar(&output, "o", "", "output .duckdb path (default <repo-root>/reference/database/duckdb/agent_assurance.duckdb)")
	fs.StringVar(&output, "output", "", "output .duckdb path")
	fs.StringVar(&duckdbCLI, "duckdb", "duckdb", "duckdb CLI binary on PATH")

	// Manual subcommand detection (the verb is the first non-flag arg).
	args := os.Args[1:]
	if len(args) > 0 && args[0] == "verify" {
		subcommand = "verify"
		args = args[1:]
	}
	if err := fs.Parse(args); err != nil {
		return err
	}

	if output == "" {
		// Stem must NOT be "dagtoml" — DuckDB derives the catalog name
		// from the file stem and would collide with the schema name.
		output = filepath.Join(repoRoot, "reference/database/duckdb/agent_assurance.duckdb")
	}

	if subcommand == "verify" {
		return verify(duckdbCLI, output)
	}

	schema := filepath.Join(repoRoot, "reference/database/duckdb/schema.sql")
	seed := filepath.Join(repoRoot, "reference/database/duckdb/seed.sql")
	if _, err := os.Stat(schema); err != nil {
		return fmt.Errorf("schema: %w", err)
	}
	if _, err := os.Stat(seed); err != nil {
		return fmt.Errorf("seed: %w", err)
	}

	// Always start from a fresh file — artifact is reproducible & binary.
	_ = os.Remove(output)

	fmt.Fprintln(os.Stderr, "loading schema.sql ...")
	if err := runSQLFile(duckdbCLI, output, schema); err != nil {
		return err
	}
	fmt.Fprintln(os.Stderr, "loading seed.sql ...")
	if err := runSQLFile(duckdbCLI, output, seed); err != nil {
		return err
	}
	fmt.Fprintln(os.Stderr, "verifying counts ...")
	return verify(duckdbCLI, output)
}

func runSQLFile(cli, db, sqlPath string) error {
	sql, err := os.ReadFile(sqlPath)
	if err != nil {
		return fmt.Errorf("read %s: %w", sqlPath, err)
	}
	cmd := exec.Command(cli, db)
	cmd.Stdin = bytes.NewReader(sql)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	cmd.Stdout = &bytes.Buffer{}
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("duckdb non-zero on %s: %w\nstderr:\n%s", sqlPath, err, stderr.String())
	}
	return nil
}

func countTable(cli, db, table string) (int64, error) {
	cmd := exec.Command(cli, db, "-noheader", "-list", "-c",
		fmt.Sprintf("SELECT count(*) FROM dagtoml.%s;", table))
	var out, stderr bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return 0, fmt.Errorf("duckdb count %s: %w\nstderr:\n%s", table, err, stderr.String())
	}
	text := strings.TrimSpace(out.String())
	n, err := strconv.ParseInt(text, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("count parse %s: %w (raw: %q)", table, err, text)
	}
	return n, nil
}

func verify(cli, db string) error {
	var fails int
	for _, ec := range expectedCounts {
		got, err := countTable(cli, db, ec.table)
		switch {
		case err != nil:
			fmt.Printf("  %-26s  ERROR: %v\n", ec.table, err)
			fails++
		case got != ec.want:
			fmt.Printf("  %-26s  %4d != %d   <-- DRIFT\n", ec.table, got, ec.want)
			fails++
		default:
			fmt.Printf("  %-26s  %4d == %d\n", ec.table, got, ec.want)
		}
	}
	if fails > 0 {
		fmt.Fprintln(os.Stderr, "\nDRIFT detected: regenerate the .duckdb or update the seed.")
		return errors.New("count drift")
	}
	wants := make([]string, 0, len(expectedCounts))
	for _, ec := range expectedCounts {
		wants = append(wants, strconv.FormatInt(ec.want, 10))
	}
	fmt.Printf("\nOK — counts match expected (%s)\n", strings.Join(wants, " / "))
	return nil
}
