// Safe Rust only: deny any `unsafe` block. This crate has zero
// third-party dependencies and uses only std::process / std::fs — no
// FFI, no raw pointer arithmetic, no SIMD intrinsics.
#![forbid(unsafe_code)]

//! dagtoml-duckdb — build a .duckdb artifact from the checked-in
//! reference/database/duckdb/{schema,seed}.sql by orchestrating the
//! duckdb CLI. Verifies counts after load.
//!
//! Usage:
//!     dagtoml-duckdb [--repo-root <path>] [-o <output.duckdb>] [--duckdb <cli>]
//!     dagtoml-duckdb verify -o <output.duckdb>
//!
//! Non-normative reference tooling. Requires the `duckdb` CLI on PATH
//! (or pass --duckdb <cli>); install from https://duckdb.org/.

use std::{
    fs,
    path::PathBuf,
    process::{Command, ExitCode, Stdio},
};

// Mirrors reference/database/MANIFEST.toml `[verification.duckdb]
// expected_seed_counts` (the per-engine row counts after the duckdb
// seed loads). Gated by `validators/check_attribute_values.py` —
// drift here vs MANIFEST or vs the actual seed file rows is a CI
// failure.
const EXPECTED_COUNTS: &[(&str, i64)] = &[
    ("kind_descriptor", 23),
    ("entity_kind_descriptor", 27),
    ("relation_descriptor", 31),
    ("attribute_vocabulary", 50),
    ("attribute_value_allowed", 144),
];

fn die(msg: impl std::fmt::Display) -> ExitCode {
    eprintln!("dagtoml-duckdb: {msg}");
    ExitCode::FAILURE
}

fn run_sql_file(duckdb_cli: &str, db: &PathBuf, sql_file: &PathBuf) -> Result<(), String> {
    let sql = fs::read(sql_file).map_err(|e| format!("read {sql_file:?}: {e}"))?;
    let mut child = Command::new(duckdb_cli)
        .arg(db)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("spawn {duckdb_cli}: {e}"))?;
    {
        use std::io::Write as _;
        let stdin = child.stdin.as_mut().ok_or("no stdin")?;
        stdin
            .write_all(&sql)
            .map_err(|e| format!("write stdin: {e}"))?;
    }
    let out = child.wait_with_output().map_err(|e| format!("wait: {e}"))?;
    if !out.status.success() {
        return Err(format!(
            "duckdb non-zero on {sql_file:?}: status {:?}\nstderr:\n{}",
            out.status,
            String::from_utf8_lossy(&out.stderr),
        ));
    }
    Ok(())
}

fn count_table(duckdb_cli: &str, db: &PathBuf, table: &str) -> Result<i64, String> {
    let sql = format!("SELECT count(*) FROM dagtoml.{table};");
    let out = Command::new(duckdb_cli)
        .arg(db)
        .arg("-noheader")
        .arg("-list")
        .arg("-c")
        .arg(&sql)
        .output()
        .map_err(|e| format!("spawn duckdb: {e}"))?;
    if !out.status.success() {
        return Err(format!(
            "duckdb non-zero on count {table}: status {:?}\nstderr:\n{}",
            out.status,
            String::from_utf8_lossy(&out.stderr),
        ));
    }
    let text = String::from_utf8_lossy(&out.stdout);
    text.trim()
        .parse::<i64>()
        .map_err(|e| format!("count parse {table:?}: {e} (raw: {text:?})"))
}

fn verify(duckdb_cli: &str, db: &PathBuf) -> ExitCode {
    let mut fail = 0;
    for (table, expected) in EXPECTED_COUNTS {
        match count_table(duckdb_cli, db, table) {
            Ok(actual) if actual == *expected => {
                println!("  {table:<26}  {actual:>4} == {expected}");
            }
            Ok(actual) => {
                println!("  {table:<26}  {actual:>4} != {expected}   <-- DRIFT");
                fail += 1;
            }
            Err(e) => {
                println!("  {table:<26}  ERROR: {e}");
                fail += 1;
            }
        }
    }
    if fail > 0 {
        eprintln!("\nDRIFT detected: regenerate the .duckdb or update the seed.");
        return ExitCode::FAILURE;
    }
    println!(
        "\nOK — counts match expected ({})",
        EXPECTED_COUNTS
            .iter()
            .map(|(_, n)| n.to_string())
            .collect::<Vec<_>>()
            .join(" / ")
    );
    ExitCode::SUCCESS
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().collect();
    let mut repo_root = PathBuf::from(".");
    let mut output: Option<PathBuf> = None;
    let mut duckdb_cli = "duckdb".to_string();
    let mut subcommand: Option<String> = None;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "verify" => subcommand = Some("verify".into()),
            "--repo-root" => {
                i += 1;
                repo_root = PathBuf::from(&args[i]);
            }
            "-o" | "--output" => {
                i += 1;
                output = Some(PathBuf::from(&args[i]));
            }
            "--duckdb" => {
                i += 1;
                duckdb_cli = args[i].clone();
            }
            "-h" | "--help" => {
                eprintln!(
                    "dagtoml-duckdb — build/verify a .duckdb artifact for DAG-TOML.\n\nUsage:\n    dagtoml-duckdb [--repo-root <path>] [-o <output.duckdb>] [--duckdb <cli>]\n    dagtoml-duckdb verify -o <output.duckdb> [--duckdb <cli>]\n\nDefault output: <repo-root>/reference/database/duckdb/dagtoml.duckdb\nDefault duckdb CLI: `duckdb` from PATH."
                );
                return ExitCode::SUCCESS;
            }
            other => return die(format!("unknown argument: {other}")),
        }
        i += 1;
    }

    // Default output stem must NOT collide with the `dagtoml` schema
    // name — DuckDB derives the catalog name from the file stem and
    // would then refuse `dagtoml.kind_descriptor` as ambiguous between
    // catalog and schema. We use `agent_assurance.duckdb` so the
    // catalog/schema names stay distinct.
    let output = output
        .unwrap_or_else(|| repo_root.join("reference/database/duckdb/agent_assurance.duckdb"));

    if subcommand.as_deref() == Some("verify") {
        return verify(&duckdb_cli, &output);
    }

    let schema = repo_root.join("reference/database/duckdb/schema.sql");
    let seed = repo_root.join("reference/database/duckdb/seed.sql");

    if !schema.is_file() {
        return die(format!("missing {schema:?}"));
    }
    if !seed.is_file() {
        return die(format!("missing {seed:?}"));
    }

    // Start from a fresh file every time — the artifact is meant to be
    // reproducible and binary, not append-only.
    if output.exists() {
        if let Err(e) = fs::remove_file(&output) {
            return die(format!("remove {output:?}: {e}"));
        }
    }

    eprintln!("loading schema.sql ...");
    if let Err(e) = run_sql_file(&duckdb_cli, &output, &schema) {
        return die(e);
    }
    eprintln!("loading seed.sql ...");
    if let Err(e) = run_sql_file(&duckdb_cli, &output, &seed) {
        return die(e);
    }
    eprintln!("verifying counts ...");
    verify(&duckdb_cli, &output)
}
