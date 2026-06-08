//! toml-test decoder shim for the `toml` 1.1 crate.
//!
//! Reads a TOML document on stdin, parses it with the same `toml`
//! crate that `tools/dagtoml-validate-rs` depends on, walks the
//! parsed `Value`, and emits the toml-test "tagged JSON" format on
//! stdout.
//!
//! Tagged JSON format (per toml-lang/toml-test):
//!
//!   - scalar values become `{"type": "<typename>", "value": "<string>"}`
//!     where typename is one of: `string`, `integer`, `float`, `bool`,
//!     `datetime`, `datetime-local`, `date-local`, `time-local`.
//!   - arrays become JSON arrays of recursively-encoded values.
//!   - tables become JSON objects of recursively-encoded values.
//!
//! On parse failure the shim writes an error to stderr and exits 1
//! (toml-test treats any non-zero exit as "parser rejected this
//! input", which is the correct behaviour for invalid fixtures).

#![forbid(unsafe_code)]
#![deny(clippy::all)]

use std::io::{self, Read, Write};
use std::process::ExitCode;

use serde_json::{Map, Value as JsonValue, json};
use toml::Value as TomlValue;

fn main() -> ExitCode {
    let mut input = String::new();
    if let Err(e) = io::stdin().read_to_string(&mut input) {
        eprintln!("toml-test-decode-rs: failed to read stdin: {e}");
        return ExitCode::from(1);
    }
    let parsed: TomlValue = match toml::from_str(&input) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("toml-test-decode-rs: parse error: {e}");
            return ExitCode::from(1);
        }
    };
    let tagged = encode(&parsed);
    let mut out = io::stdout().lock();
    if let Err(e) = serde_json::to_writer(&mut out, &tagged) {
        eprintln!("toml-test-decode-rs: failed to write stdout: {e}");
        return ExitCode::from(1);
    }
    let _ = writeln!(&mut out);
    ExitCode::SUCCESS
}

fn encode(v: &TomlValue) -> JsonValue {
    match v {
        TomlValue::String(s) => json!({"type": "string", "value": s}),
        TomlValue::Integer(i) => json!({"type": "integer", "value": i.to_string()}),
        TomlValue::Float(f) => json!({"type": "float", "value": float_repr(*f)}),
        TomlValue::Boolean(b) => json!({"type": "bool", "value": b.to_string()}),
        TomlValue::Datetime(dt) => {
            let kind = match (dt.date.is_some(), dt.time.is_some(), dt.offset.is_some()) {
                (true, true, true) => "datetime",
                (true, true, false) => "datetime-local",
                (true, false, false) => "date-local",
                (false, true, false) => "time-local",
                _ => "datetime",
            };
            json!({"type": kind, "value": dt.to_string()})
        }
        TomlValue::Array(arr) => JsonValue::Array(arr.iter().map(encode).collect()),
        TomlValue::Table(tbl) => {
            let mut obj = Map::with_capacity(tbl.len());
            for (k, val) in tbl {
                obj.insert(k.clone(), encode(val));
            }
            JsonValue::Object(obj)
        }
    }
}

fn float_repr(f: f64) -> String {
    if f.is_nan() {
        return "nan".to_string();
    }
    if f.is_infinite() {
        return if f.is_sign_negative() { "-inf" } else { "inf" }.to_string();
    }
    // {:?} preserves the trailing ".0" for whole-number floats and
    // emits the shortest round-tripping representation otherwise.
    // Either form is parseable by toml-test as a JSON float string.
    format!("{f:?}")
}
