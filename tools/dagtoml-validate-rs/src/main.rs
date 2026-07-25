//! Safe-Rust primary validator for DAG-TOML canonical examples,
//! profiles, ontologies, kind descriptors, and semantic invariants.
//!
//! This binary is the **primary** validator for the new artifacts.
//! The reference Python validators under `validators/` are retained
//! as a cross-check; CI runs Rust + Go first and treats divergence
//! as a build break.
//!
//! Safety posture: this crate sets `#![forbid(unsafe_code)]` and has no
//! FFI (enforced by `validators/check_safe_tools.sh`). Transitive parser
//! dependencies — the widely-vetted `toml`/`toml_parser`/`winnow` and
//! `serde` crates — may use `unsafe` internally; that is out of scope of
//! the safe-tools policy, which governs the code WE write, not our deps.

#![forbid(unsafe_code)]
#![deny(clippy::all)]

use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use sha2::{Digest, Sha256, Sha384, Sha512};
use toml::Value;

mod cli {
    use std::path::PathBuf;
    use std::process::ExitCode;

    pub struct Args {
        pub repo_root: PathBuf,
        pub files: Vec<PathBuf>,
        pub mode: Mode,
    }

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    pub enum Mode {
        /// Auto-detect from each file's [meta].template_kind.
        Auto,
        /// Force profile-descriptor validation.
        Profile,
        /// Force disclosure-instance validation.
        Disclosure,
        /// Force provenance.encryption sub-table validation.
        Provenance,
        /// Force §2.2 / §2.7 meta-field validation only.
        Meta,
        /// Force gate-decision INV01..INV06 validation.
        GateDecision,
        /// Force kind-descriptor structural validation.
        KindDescriptor,
        /// Force IJB conformance validation.
        Ijb,
        /// Force full [provenance] source binding validation.
        ProvenanceBinding,
        /// Force implementation-dag validation.
        ImplementationDag,
        /// Force traceability validation.
        Traceability,
        /// Force review-readiness/readiness-gate/contract/evidence validation.
        ReviewReadiness,
        /// Force cost-record validation.
        CostRecord,
        /// Force rollback-plan validation.
        RollbackPlan,
        /// Force SPEC §13 abstraction_class/capability_envelope validation.
        AbstractionClass,
    }

    pub fn print_usage() {
        eprintln!(
            "usage: dagtoml-validate-rs --repo-root <path> [--mode auto|profile|disclosure|provenance|meta|gate-decision|kind-descriptor|ijb|provenance-binding|implementation-dag|traceability|review-readiness|cost-record|rollback-plan|abstraction-class] <file.toml> ..."
        );
    }

    pub fn parse(args: impl IntoIterator<Item = String>) -> Result<Args, ExitCode> {
        let mut repo_root: Option<PathBuf> = None;
        let mut files: Vec<PathBuf> = Vec::new();
        let mut mode = Mode::Auto;
        let mut it = args.into_iter().peekable();
        while let Some(arg) = it.next() {
            match arg.as_str() {
                "--repo-root" => match it.next() {
                    Some(v) => repo_root = Some(PathBuf::from(v)),
                    None => {
                        eprintln!("error: --repo-root requires a value");
                        return Err(ExitCode::from(2));
                    }
                },
                "--mode" => match it.next().as_deref() {
                    Some("auto") => mode = Mode::Auto,
                    Some("profile") => mode = Mode::Profile,
                    Some("disclosure") => mode = Mode::Disclosure,
                    Some("provenance") => mode = Mode::Provenance,
                    Some("meta") => mode = Mode::Meta,
                    Some("gate-decision") => mode = Mode::GateDecision,
                    Some("kind-descriptor") => mode = Mode::KindDescriptor,
                    Some("ijb") => mode = Mode::Ijb,
                    Some("provenance-binding") => mode = Mode::ProvenanceBinding,
                    Some("implementation-dag") => mode = Mode::ImplementationDag,
                    Some("traceability") => mode = Mode::Traceability,
                    Some("review-readiness") => mode = Mode::ReviewReadiness,
                    Some("cost-record") => mode = Mode::CostRecord,
                    Some("rollback-plan") => mode = Mode::RollbackPlan,
                    Some("abstraction-class") => mode = Mode::AbstractionClass,
                    other => {
                        eprintln!(
                            "error: --mode value must be auto|profile|disclosure|provenance|meta|gate-decision|kind-descriptor|ijb|provenance-binding|implementation-dag|traceability|review-readiness|cost-record|rollback-plan|abstraction-class (got {:?})",
                            other
                        );
                        return Err(ExitCode::from(2));
                    }
                },
                "-h" | "--help" => {
                    print_usage();
                    return Err(ExitCode::SUCCESS);
                }
                other if other.starts_with("--") => {
                    eprintln!("error: unknown flag {}", other);
                    return Err(ExitCode::from(2));
                }
                _ => files.push(PathBuf::from(arg)),
            }
        }
        let Some(root) = repo_root else {
            eprintln!("error: --repo-root is required");
            return Err(ExitCode::from(2));
        };
        if files.is_empty() {
            eprintln!("error: at least one input file is required");
            return Err(ExitCode::from(2));
        }
        Ok(Args {
            repo_root: root,
            files,
            mode,
        })
    }
}

// ------------------------------------------------------------
// TOML loading
// ------------------------------------------------------------

fn load(path: &Path) -> Result<Value, String> {
    let raw = std::fs::read_to_string(path)
        .map_err(|e| format!("{}: read failed: {}", path.display(), e))?;
    // toml 1.1: `str::parse::<Value>()` parses a single *value* expression,
    // not a whole document (it routes through `ValueDeserializer`). Document
    // parsing is `toml::from_str`, which deserializes the full table. (In
    // toml 0.8 `FromStr for Value` parsed a document; the 1.1 line split the
    // two, so this call site shifts.)
    toml::from_str::<Value>(&raw)
        .map_err(|e| format!("{}: TOML parse failed: {}", path.display(), e))
}

fn is_semver(s: &str) -> bool {
    let parts: Vec<&str> = s.split('.').collect();
    parts.len() == 3
        && parts.iter().all(|part| {
            !part.is_empty()
                && part.chars().all(|c| c.is_ascii_digit())
                && (*part == "0" || !part.starts_with('0'))
        })
}

fn table<'a>(value: &'a Value, key: &str) -> Option<&'a toml::map::Map<String, Value>> {
    value.get(key).and_then(Value::as_table)
}

fn array<'a>(value: &'a Value, key: &str) -> &'a [Value] {
    value
        .get(key)
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or(&[])
}

fn is_non_empty_string(value: Option<&Value>) -> bool {
    value
        .and_then(Value::as_str)
        .is_some_and(|s| !s.trim().is_empty())
}

// ------------------------------------------------------------
// Kind-descriptor structural validation
// ------------------------------------------------------------

mod kind_descriptor {
    use super::{Value, array, is_non_empty_string, table};
    use std::path::Path;

    const REQUIRED_META_FIELDS: &[&str] =
        &["schema_version", "template_kind", "describes_kind", "title"];
    const REQUIRED_KIND_FIELDS: &[&str] = &["name", "summary", "prose"];
    const PLACEHOLDER_MARKERS: &[&str] = &["<", ">", "YYYY-MM-DD"];

    fn has_placeholder(value: &str) -> bool {
        PLACEHOLDER_MARKERS
            .iter()
            .any(|marker| value.contains(marker))
    }

    fn is_prose_field(path: &str) -> bool {
        matches!(path, "kind.prose" | "kind.summary")
            || path.ends_with(".inline")
            || path.ends_with(".inline_summary")
            || path.ends_with(".description")
            || path.ends_with(".statement")
            || path.ends_with(".notes")
            || path.ends_with(".note")
    }

    fn iter_strings(value: &Value, prefix: &str, out: &mut Vec<(String, String)>) {
        match value {
            Value::String(s) => out.push((prefix.to_string(), s.clone())),
            Value::Array(arr) => {
                for (idx, item) in arr.iter().enumerate() {
                    iter_strings(item, &format!("{prefix}[{idx}]"), out);
                }
            }
            Value::Table(t) => {
                for (k, v) in t {
                    let sub = if prefix.is_empty() {
                        k.to_string()
                    } else {
                        format!("{prefix}.{k}")
                    };
                    iter_strings(v, &sub, out);
                }
            }
            _ => {}
        }
    }

    pub fn validate(
        path: &Path,
        doc: &Value,
        repo_root: &Path,
        check_references_exist: bool,
        allow_placeholders: bool,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        let Some(meta) = table(doc, "meta") else {
            errors.push("missing required `[meta]` table".to_string());
            return errors;
        };
        for field in REQUIRED_META_FIELDS {
            if !meta.contains_key(*field) {
                errors.push(format!("meta: missing required field `{field}`"));
            }
        }
        if meta.get("template_kind").and_then(Value::as_str) != Some("kind-descriptor") {
            errors.push(format!(
                "meta.template_kind: expected `\"kind-descriptor\"`, got `{:?}`",
                meta.get("template_kind")
            ));
        }
        let describes_kind = meta.get("describes_kind").and_then(Value::as_str);
        if meta.contains_key("describes_kind") && describes_kind.is_none() {
            errors.push("meta.describes_kind: must be a string".to_string());
        }

        let Some(kind) = table(doc, "kind") else {
            errors.push("missing required `[kind]` table".to_string());
            return errors;
        };
        for field in REQUIRED_KIND_FIELDS {
            if !kind.contains_key(*field) {
                errors.push(format!("kind: missing required field `{field}`"));
            }
        }
        if let (Some(name), Some(describes)) =
            (kind.get("name").and_then(Value::as_str), describes_kind)
        {
            if name != describes {
                errors.push(format!(
                    "kind.name `{name}` does not match meta.describes_kind `{describes}`"
                ));
            }
        }
        if let Some(summary) = kind.get("summary").and_then(Value::as_str) {
            if summary.trim().len() < 10 {
                errors.push("kind.summary: must be at least 10 characters".to_string());
            }
        }
        if let Some(prose) = kind.get("prose").and_then(Value::as_str) {
            if prose.trim().len() < 50 {
                errors.push("kind.prose: must be at least 50 characters".to_string());
            }
        }

        if !allow_placeholders {
            let mut strings = Vec::new();
            iter_strings(doc, "", &mut strings);
            for (field_path, value) in strings {
                if !is_prose_field(&field_path) && has_placeholder(&value) {
                    errors.push(format!("{field_path}: placeholder value not allowed"));
                }
            }
        }

        if check_references_exist {
            for entry in array(&Value::Table(kind.clone()), "example") {
                let Some(t) = entry.as_table() else { continue };
                let Some(file) = t.get("file").and_then(Value::as_str) else {
                    continue;
                };
                if file.is_empty() {
                    continue;
                }
                if !allow_placeholders && has_placeholder(file) {
                    errors.push(format!(
                        "kind.example.file: placeholder path not allowed: {file}"
                    ));
                    continue;
                }
                if !repo_root.join(file).exists() {
                    errors.push(format!(
                        "kind.example.file: path does not exist under repo root: {file}"
                    ));
                }
            }
            for entry in array(&Value::Table(kind.clone()), "hard_invariants") {
                let Some(t) = entry.as_table() else { continue };
                let Some(enforced_by) = t.get("enforced_by").and_then(Value::as_str) else {
                    continue;
                };
                if !is_non_empty_string(t.get("enforced_by")) {
                    continue;
                }
                let lowered = enforced_by.to_ascii_lowercase();
                if lowered.contains("(planned)")
                    || lowered.contains("(tbd)")
                    || lowered.contains("prose review")
                {
                    continue;
                }
                let looks_path = (enforced_by.contains('/')
                    || enforced_by.ends_with(".py")
                    || enforced_by.ends_with(".toml")
                    || enforced_by.ends_with(".json"))
                    && !enforced_by.contains(' ')
                    && !enforced_by.contains('(');
                if looks_path && !repo_root.join(enforced_by).exists() {
                    errors.push(format!(
                        "kind.hard_invariants.enforced_by: path does not exist under repo root: {enforced_by}"
                    ));
                }
            }
            for reference in array(&Value::Table(kind.clone()), "references") {
                let Some(raw) = reference.as_str() else {
                    continue;
                };
                let bare = raw.split('#').next().unwrap_or("").trim();
                if bare.is_empty() {
                    continue;
                }
                if has_placeholder(bare) && !allow_placeholders {
                    continue;
                }
                if !repo_root.join(bare).exists() {
                    errors.push(format!(
                        "kind.references: path does not exist under repo root: {bare}"
                    ));
                }
            }
        }

        if path.as_os_str().is_empty() {
            errors.push("internal error: empty path".to_string());
        }
        errors
    }
}

// ------------------------------------------------------------
// IJB conformance
// ------------------------------------------------------------

mod ijb {
    use super::{Value, array, table};
    use std::collections::BTreeSet;
    use std::path::{Path, PathBuf};

    const IJB_PRIMITIVES: &[&str] = &["thing", "scope", "path", "observed", "constraint", "time"];
    const IJB_CLASSES: &[&str] = &["structural", "instance"];
    const IJB_CONSTRAINT_TYPES: &[&str] = &["structural", "policy", "observed"];

    fn primitive_class(
        block: &toml::map::Map<String, Value>,
        loc: &str,
        expected_primitive: &str,
        expected_class: Option<&str>,
        expected_constraint_type: Option<&str>,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        match block.get("ijb_primitive").and_then(Value::as_str) {
            None => errors.push(format!("{loc}: missing required `ijb_primitive`")),
            Some(v) if !IJB_PRIMITIVES.contains(&v) => errors.push(format!(
                "{loc}: `ijb_primitive = \"{v}\"` is not one of {:?}",
                IJB_PRIMITIVES
            )),
            Some(v) if v != expected_primitive => errors.push(format!(
                "{loc}: `ijb_primitive = \"{v}\"` does not match the SPEC §10.2 mapping (expected `\"{expected_primitive}\"`)"
            )),
            _ => {}
        }

        if let Some(expected) = expected_class {
            match block.get("ijb_class").and_then(Value::as_str) {
                None => errors.push(format!("{loc}: missing required `ijb_class`")),
                Some(v) if !IJB_CLASSES.contains(&v) => errors.push(format!(
                    "{loc}: `ijb_class = \"{v}\"` is not one of {:?}",
                    IJB_CLASSES
                )),
                Some(v) if v != expected => errors.push(format!(
                    "{loc}: `ijb_class = \"{v}\"` does not match the SPEC §10.2 mapping (expected `\"{expected}\"`)"
                )),
                _ => {}
            }
        } else if block.contains_key("ijb_class") {
            errors.push(format!(
                "{loc}: `ijb_class` is not permitted on this block per SPEC §10.2"
            ));
        }

        if let Some(expected) = expected_constraint_type {
            match block.get("ijb_constraint_type").and_then(Value::as_str) {
                None => errors.push(format!("{loc}: missing required `ijb_constraint_type`")),
                Some(v) if !IJB_CONSTRAINT_TYPES.contains(&v) => errors.push(format!(
                    "{loc}: `ijb_constraint_type = \"{v}\"` is not one of {:?}",
                    IJB_CONSTRAINT_TYPES
                )),
                Some(v) if v != expected => errors.push(format!(
                    "{loc}: `ijb_constraint_type = \"{v}\"` does not match the SPEC §10.2 mapping (expected `\"{expected}\"`)"
                )),
                _ => {}
            }
        } else if block.contains_key("ijb_constraint_type") {
            errors.push(format!(
                "{loc}: `ijb_constraint_type` is not permitted on this block per SPEC §10.2"
            ));
        }

        errors
    }

    fn meta_field_expected(
        field: &str,
    ) -> Option<(&'static str, Option<&'static str>, Option<&'static str>)> {
        match field {
            "framework_profile" => Some(("scope", Some("structural"), None)),
            "template_kind" => Some(("scope", Some("structural"), None)),
            "schema_version" => Some(("constraint", None, Some("structural"))),
            "ontology_version" => Some(("constraint", None, Some("structural"))),
            "confidentiality" => Some(("constraint", None, Some("policy"))),
            "license" => Some(("constraint", None, Some("policy"))),
            "embargo_until" => Some(("time", None, None)),
            _ => None,
        }
    }

    pub fn validate_ontology(source: &Path, doc: &Value) -> Vec<String> {
        let mut errors = Vec::new();
        for (idx, block) in array(doc, "entities").iter().enumerate() {
            if let Some(t) = block.as_table() {
                let label = t
                    .get("id_prefix")
                    .or_else(|| t.get("id_pattern"))
                    .and_then(Value::as_str)
                    .unwrap_or("?");
                errors.extend(primitive_class(
                    t,
                    &format!("{}:entities[{idx}] ({label})", source.display()),
                    "thing",
                    Some("structural"),
                    None,
                ));
            }
        }
        for (idx, block) in array(doc, "relations").iter().enumerate() {
            if let Some(t) = block.as_table() {
                let label = t.get("predicate").and_then(Value::as_str).unwrap_or("?");
                errors.extend(primitive_class(
                    t,
                    &format!("{}:relations[{idx}] (predicate={label})", source.display()),
                    "path",
                    Some("structural"),
                    None,
                ));
            }
        }
        for (idx, block) in array(doc, "attribute_vocabularies").iter().enumerate() {
            if let Some(t) = block.as_table() {
                let label = t.get("attribute").and_then(Value::as_str).unwrap_or("?");
                let loc = format!(
                    "{}:attribute_vocabularies[{idx}] (attribute={label})",
                    source.display()
                );
                match t.get("ijb_primitive").and_then(Value::as_str) {
                    None => errors.push(format!("{loc}: missing required `ijb_primitive`")),
                    Some(v) if !IJB_PRIMITIVES.contains(&v) => errors.push(format!(
                        "{loc}: `ijb_primitive = \"{v}\"` is not one of {:?}",
                        IJB_PRIMITIVES
                    )),
                    Some(v) if v != "constraint" => errors.push(format!(
                        "{loc}: `ijb_primitive = \"{v}\"` does not match the SPEC §10.2 mapping (expected `\"constraint\"`)"
                    )),
                    _ => {}
                }
                if t.contains_key("ijb_class") {
                    errors.push(format!(
                        "{loc}: `ijb_class` is not permitted on attribute_vocabularies blocks"
                    ));
                }
                match t.get("ijb_constraint_type").and_then(Value::as_str) {
                    None => errors.push(format!("{loc}: missing required `ijb_constraint_type`")),
                    Some(v) if !IJB_CONSTRAINT_TYPES.contains(&v) => errors.push(format!(
                        "{loc}: `ijb_constraint_type = \"{v}\"` is not one of {:?}",
                        IJB_CONSTRAINT_TYPES
                    )),
                    _ => {}
                }
            }
        }
        match table(doc, "extension_rules") {
            Some(ext) => errors.extend(primitive_class(
                ext,
                &format!("{}:[extension_rules]", source.display()),
                "constraint",
                None,
                Some("structural"),
            )),
            None => errors.push(format!(
                "{}: missing required `[extension_rules]` table (SPEC §10.2 row)",
                source.display()
            )),
        }

        let meta = table(doc, "meta");
        let field_prims = meta
            .and_then(|m| m.get("ijb_field_primitives"))
            .and_then(Value::as_table);
        let Some(field_prims) = field_prims else {
            errors.push(format!(
                "{}: missing required `[meta.ijb_field_primitives]` table",
                source.display()
            ));
            return errors;
        };
        let Some(meta) = meta else {
            return errors;
        };
        for fname in [
            "framework_profile",
            "template_kind",
            "schema_version",
            "ontology_version",
            "confidentiality",
            "license",
            "embargo_until",
        ] {
            let fblock = field_prims.get(fname).and_then(Value::as_table);
            if fblock.is_none() && meta.contains_key(fname) {
                errors.push(format!(
                    "{}:[meta.ijb_field_primitives].{fname}: missing required inline annotation table",
                    source.display()
                ));
                continue;
            }
            if let (Some(block), Some((p, c, ct))) = (fblock, meta_field_expected(fname)) {
                errors.extend(primitive_class(
                    block,
                    &format!("{}:[meta.ijb_field_primitives].{fname}", source.display()),
                    p,
                    c,
                    ct,
                ));
            }
        }
        for fname in field_prims.keys() {
            if meta_field_expected(fname).is_none() {
                errors.push(format!(
                    "{}:[meta.ijb_field_primitives].{fname}: unknown meta-field annotation key",
                    source.display()
                ));
            }
        }
        errors
    }

    pub fn validate_kind_descriptor(source: &Path, doc: &Value) -> Vec<String> {
        let mut errors = Vec::new();
        let Some(kind) = table(doc, "kind") else {
            errors.push(format!(
                "{}: kind-descriptor missing required `[kind]` table",
                source.display()
            ));
            return errors;
        };
        errors.extend(primitive_class(
            kind,
            &format!("{}:[kind]", source.display()),
            "thing",
            Some("structural"),
            None,
        ));
        for key in ["required_fields", "required_sections", "hard_invariants"] {
            for (idx, block) in kind
                .get(key)
                .and_then(Value::as_array)
                .map(Vec::as_slice)
                .unwrap_or(&[])
                .iter()
                .enumerate()
            {
                if let Some(t) = block.as_table() {
                    errors.extend(primitive_class(
                        t,
                        &format!("{}:[[kind.{key}]][{idx}]", source.display()),
                        "constraint",
                        None,
                        Some("structural"),
                    ));
                }
            }
        }
        for (idx, block) in kind
            .get("example")
            .and_then(Value::as_array)
            .map(Vec::as_slice)
            .unwrap_or(&[])
            .iter()
            .enumerate()
        {
            if let Some(t) = block.as_table() {
                errors.extend(primitive_class(
                    t,
                    &format!("{}:[[kind.example]][{idx}]", source.display()),
                    "observed",
                    None,
                    None,
                ));
            }
        }
        if let Some(rto) = kind.get("relation_to_ontology").and_then(Value::as_table) {
            errors.extend(primitive_class(
                rto,
                &format!("{}:[kind.relation_to_ontology]", source.display()),
                "constraint",
                None,
                Some("structural"),
            ));
        }
        errors
    }

    pub fn validate_profile_descriptor(source: &Path, doc: &Value) -> Vec<String> {
        let Some(profile) = table(doc, "profile") else {
            return vec![format!(
                "{}: profile-descriptor missing required `[profile]` table",
                source.display()
            )];
        };
        primitive_class(
            profile,
            &format!("{}:[profile]", source.display()),
            "thing",
            Some("structural"),
            None,
        )
    }

    fn resolve_profile_name(name: &str) -> &str {
        if name == "AGDF" {
            "agent-assurance"
        } else {
            name
        }
    }

    fn matches_id_pattern(pattern: &str, value: &str) -> bool {
        let Some((prefix, rest)) = pattern.split_once("\\d+") else {
            return value == pattern;
        };
        if !value.starts_with(prefix) {
            return false;
        }
        let suffix = &value[prefix.len()..];
        if suffix.is_empty() {
            return false;
        }
        let digit_count = suffix.chars().take_while(|c| c.is_ascii_digit()).count();
        if digit_count == 0 {
            return false;
        }
        let after_digits = &suffix[digit_count..];
        match rest {
            "" => after_digits.is_empty(),
            "[a-z]?" => {
                after_digits.is_empty()
                    || (after_digits.len() == 1
                        && after_digits.chars().all(|c| c.is_ascii_lowercase()))
            }
            _ => false,
        }
    }

    fn build_resolver(
        ontologies: &[(PathBuf, Value)],
    ) -> (BTreeSet<String>, Vec<String>, BTreeSet<String>) {
        let mut prefixes = BTreeSet::new();
        let mut patterns = Vec::new();
        let mut predicates = BTreeSet::new();
        for (_path, doc) in ontologies {
            for ent in array(doc, "entities") {
                if let Some(t) = ent.as_table() {
                    if let Some(prefix) = t.get("id_prefix").and_then(Value::as_str) {
                        prefixes.insert(prefix.to_string());
                    }
                    if let Some(pattern) = t.get("id_pattern").and_then(Value::as_str) {
                        patterns.push(pattern.to_string());
                    }
                }
            }
            for rel in array(doc, "relations") {
                if let Some(predicate) = rel
                    .as_table()
                    .and_then(|t| t.get("predicate"))
                    .and_then(Value::as_str)
                {
                    predicates.insert(predicate.to_string());
                }
            }
        }
        (prefixes, patterns, predicates)
    }

    fn looks_upper_prefix(prefix: &str) -> bool {
        let mut chars = prefix.chars();
        let Some(first) = chars.next() else {
            return false;
        };
        first.is_ascii_uppercase()
            && chars.all(|c| c.is_ascii_uppercase() || c.is_ascii_digit() || c == '_')
    }

    fn check_entity_ref(
        token: &str,
        prefixes: &BTreeSet<String>,
        patterns: &[String],
    ) -> Option<String> {
        if let Some((prefix, _)) = token.split_once(':') {
            if !looks_upper_prefix(prefix) {
                return None;
            }
            if prefixes.contains(prefix) {
                return None;
            }
            return Some(format!(
                "entity prefix `{prefix}` in `{token}` does not resolve to a declared `[[entities]].id_prefix` in the loaded ontologies"
            ));
        }
        if patterns
            .iter()
            .any(|pattern| matches_id_pattern(pattern, token))
        {
            return None;
        }
        None
    }

    fn walk_instance(
        node: &Value,
        parent_key: &str,
        path: &str,
        prefixes: &BTreeSet<String>,
        patterns: &[String],
        predicates: &BTreeSet<String>,
        errors: &mut Vec<String>,
    ) {
        match node {
            Value::String(s) => {
                if (parent_key == "id" || predicates.contains(parent_key))
                    && let Some(err) = check_entity_ref(s, prefixes, patterns)
                {
                    errors.push(format!("{path}: {err}"));
                }
            }
            Value::Array(arr) => {
                for (idx, item) in arr.iter().enumerate() {
                    walk_instance(
                        item,
                        parent_key,
                        &format!("{path}[{idx}]"),
                        prefixes,
                        patterns,
                        predicates,
                        errors,
                    );
                }
            }
            Value::Table(t) => {
                for (k, v) in t {
                    let sub = if path.is_empty() {
                        k.to_string()
                    } else {
                        format!("{path}.{k}")
                    };
                    walk_instance(v, k, &sub, prefixes, patterns, predicates, errors);
                }
            }
            _ => {}
        }
    }

    pub fn validate_instance(source: &Path, doc: &Value, repo_root: &Path) -> Vec<String> {
        let mut errors = Vec::new();
        let mut ontologies = Vec::new();
        let core_path = repo_root.join("core/ontology.toml");
        match std::fs::read_to_string(&core_path)
            .ok()
            .and_then(|raw| toml::from_str::<Value>(&raw).ok())
        {
            Some(core) => {
                errors.extend(validate_ontology(&core_path, &core));
                ontologies.push((core_path, core));
            }
            None => errors.push(format!(
                "core ontology not found or unparsable at {}",
                core_path.display()
            )),
        }
        if let Some(fp) = table(doc, "meta")
            .and_then(|m| m.get("framework_profile"))
            .and_then(Value::as_str)
        {
            let profile = resolve_profile_name(fp);
            let profile_path = repo_root
                .join("profiles")
                .join(profile)
                .join("ontology.toml");
            match std::fs::read_to_string(&profile_path)
                .ok()
                .and_then(|raw| toml::from_str::<Value>(&raw).ok())
            {
                Some(profile_doc) => {
                    errors.extend(validate_ontology(&profile_path, &profile_doc));
                    ontologies.push((profile_path, profile_doc));
                }
                None => errors.push(format!(
                    "framework_profile = \"{fp}\" but profile ontology not found or unparsable at {}",
                    profile_path.display()
                )),
            }
        }
        if !errors.is_empty() {
            return errors;
        }
        let (prefixes, patterns, predicates) = build_resolver(&ontologies);
        walk_instance(doc, "", "", &prefixes, &patterns, &predicates, &mut errors);
        if let Some(units) = table(doc, "units") {
            for unit_id in units.keys() {
                if !patterns
                    .iter()
                    .any(|pattern| matches_id_pattern(pattern, unit_id))
                {
                    errors.push(format!(
                        "units.{unit_id}: identifier does not match any declared entity `id_pattern` in the loaded ontologies"
                    ));
                }
            }
        }
        if source.as_os_str().is_empty() {
            errors.push("internal error: empty path".to_string());
        }
        errors
    }

    pub fn validate(source: &Path, doc: &Value, repo_root: &Path) -> Vec<String> {
        let tk = table(doc, "meta")
            .and_then(|m| m.get("template_kind"))
            .and_then(Value::as_str)
            .unwrap_or("");
        match tk {
            "ontology" => validate_ontology(source, doc),
            "kind-descriptor" => validate_kind_descriptor(source, doc),
            "profile-descriptor" => validate_profile_descriptor(source, doc),
            _ => validate_instance(source, doc, repo_root),
        }
    }
}

// ------------------------------------------------------------
// Full provenance binding validation (SPEC §11)
// ------------------------------------------------------------

fn validate_provenance_binding(path: &Path, doc: &Value, repo_root: &Path) -> Vec<String> {
    let mut errors = Vec::new();
    let Some(prov) = table(doc, "provenance") else {
        return errors;
    };
    let source_path = prov.get("source_path").and_then(Value::as_str);
    let source_sha = prov.get("source_sha256").and_then(Value::as_str);
    let source_bytes = prov.get("source_bytes").and_then(Value::as_integer);
    let Some(source_path) = source_path else {
        errors.push(format!(
            "{}: [provenance].source_path is required",
            path.display()
        ));
        return errors;
    };
    let Some(source_sha) = source_sha else {
        errors.push(format!(
            "{}: [provenance].source_sha256 is required",
            path.display()
        ));
        return errors;
    };
    let Some(source_bytes) = source_bytes else {
        errors.push(format!(
            "{}: [provenance].source_bytes is required and must be an integer",
            path.display()
        ));
        return errors;
    };
    // SPEC §11: source_path MUST be relative and resolve to a file under
    // repo root. Reject absolute paths and any path that escapes via `..`
    // or a symlink — otherwise an attestation could bind its provenance
    // digest to a file outside the repo (e.g. "../../etc/passwd") and the
    // binding would be meaningless. The Python reference
    // (validators/validate_provenance.py) enforces this; a *primary*
    // validator MUST NOT be weaker than the cross-check.
    if Path::new(source_path).is_absolute() {
        errors.push(format!(
            "{}: [provenance].source_path must be relative to repo root, got absolute path {source_path}",
            path.display()
        ));
        return errors;
    }
    let canon_root = match std::fs::canonicalize(repo_root) {
        Ok(p) => p,
        Err(e) => {
            errors.push(format!(
                "{}: [provenance] cannot canonicalize repo root: {e}",
                path.display()
            ));
            return errors;
        }
    };
    // canonicalize() resolves `..` and follows symlinks, so a symlinked
    // escape is caught by the starts_with check below; a non-existent path
    // returns Err and is reported as "does not resolve".
    let full = match std::fs::canonicalize(canon_root.join(source_path)) {
        Ok(p) => p,
        Err(e) => {
            errors.push(format!(
                "{}: [provenance].source_path does not resolve to a file under repo root ({source_path}): {e}",
                path.display()
            ));
            return errors;
        }
    };
    if !full.starts_with(&canon_root) {
        errors.push(format!(
            "{}: [provenance].source_path {source_path} resolves outside repo root ({} not under {}); SPEC §11 requires source_path to point to a file under repo root",
            path.display(),
            full.display(),
            canon_root.display()
        ));
        return errors;
    }
    if !full.is_file() {
        errors.push(format!(
            "{}: [provenance].source_path does not resolve to a regular file under repo root ({source_path})",
            path.display()
        ));
        return errors;
    }
    let data = match std::fs::read(&full) {
        Ok(data) => data,
        Err(e) => {
            errors.push(format!(
                "{}: [provenance].source_path could not be read ({source_path}): {e}",
                path.display()
            ));
            return errors;
        }
    };

    let hash_over = prov
        .get("encryption")
        .and_then(Value::as_table)
        .and_then(|e| e.get("hash_is_over"))
        .and_then(Value::as_str);
    if hash_over == Some("plaintext") {
        return errors;
    }

    if source_bytes < 0 || data.len() as i64 != source_bytes {
        errors.push(format!(
            "{}: [provenance].source_bytes = {source_bytes} but actual byte length is {}",
            path.display(),
            data.len()
        ));
    }
    let actual = format!("sha256:{}", digest_hex("sha256", &data));
    if actual != source_sha {
        errors.push(format!(
            "{}: [provenance].source_sha256 = {source_sha} but actual digest is {actual}",
            path.display()
        ));
    }
    errors
}

// ------------------------------------------------------------
// Core implementation-dag validation
// ------------------------------------------------------------

mod implementation_dag {
    use super::{Value, table};
    use std::collections::{BTreeMap, BTreeSet};
    use std::path::Path;

    const VALID_STATUS: &[&str] = &["pending", "in_progress", "done", "blocked", "deferred"];
    const REQUIRED_UNIT_FIELDS: &[&str] = &[
        "name",
        "summary",
        "layer",
        "tier",
        "status",
        "depends_on",
        "blocks",
        "estimated_loc",
    ];

    type UnitMap<'a> = BTreeMap<String, &'a toml::map::Map<String, Value>>;
    type EdgeSets = (
        BTreeMap<String, BTreeSet<String>>,
        BTreeMap<String, BTreeSet<String>>,
    );
    type EdgeValidation = (Vec<String>, EdgeSets);

    fn str_vec(value: Option<&Value>) -> Option<Vec<String>> {
        let arr = value?.as_array()?;
        let mut out = Vec::new();
        for item in arr {
            out.push(item.as_str()?.to_string());
        }
        Some(out)
    }

    fn int_value(value: Option<&Value>) -> Option<i64> {
        value.and_then(Value::as_integer)
    }

    fn has_placeholder(value: &str) -> bool {
        value.contains('<') || value.contains('>')
    }

    fn validate_units(doc: &Value) -> (Vec<String>, UnitMap<'_>) {
        let mut errors = Vec::new();
        let mut units = BTreeMap::new();
        let Some(units_table) = table(doc, "units") else {
            errors.push("no `units` table found".to_string());
            return (errors, units);
        };
        if units_table.is_empty() {
            errors.push("no `units` table found".to_string());
            return (errors, units);
        }
        for (uid, raw) in units_table {
            let Some(unit) = raw.as_table() else {
                errors.push(format!("{uid}: unit entry must be a table"));
                continue;
            };
            units.insert(uid.clone(), unit);
            for field in REQUIRED_UNIT_FIELDS {
                if !unit.contains_key(*field) {
                    errors.push(format!("{uid}: missing required field `{field}`"));
                }
            }
            if let Some(status) = unit.get("status").and_then(Value::as_str) {
                if !VALID_STATUS.contains(&status) {
                    errors.push(format!("{uid}: invalid status `{status}`"));
                }
            }
            if let Some(tier) = int_value(unit.get("tier")) {
                if !matches!(tier, 1..=3) {
                    errors.push(format!("{uid}: invalid tier `{tier}` (must be 1, 2, or 3)"));
                }
            }
            if let Some(layer) = int_value(unit.get("layer")) {
                if layer < 0 {
                    errors.push(format!("{uid}: layer must be a non-negative integer"));
                }
            }
            if let Some(loc) = int_value(unit.get("estimated_loc")) {
                if loc < 0 {
                    errors.push(format!(
                        "{uid}: estimated_loc must be a non-negative integer"
                    ));
                }
            }
        }
        (errors, units)
    }

    fn duplicate_strings(items: &[String]) -> Vec<String> {
        let mut seen = BTreeSet::new();
        let mut dupes = BTreeSet::new();
        for item in items {
            if !seen.insert(item.clone()) {
                dupes.insert(item.clone());
            }
        }
        dupes.into_iter().collect()
    }

    fn validate_edges(units: &UnitMap<'_>) -> EdgeValidation {
        let mut errors = Vec::new();
        let uids: BTreeSet<String> = units.keys().cloned().collect();
        let mut deps: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
        let mut blocks: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
        for (uid, unit) in units {
            let dep_list = str_vec(unit.get("depends_on")).unwrap_or_default();
            let block_list = str_vec(unit.get("blocks")).unwrap_or_default();
            for r in &dep_list {
                if r == uid {
                    errors.push(format!("{uid}: depends_on includes self"));
                } else if !uids.contains(r) {
                    errors.push(format!("{uid}: depends_on references unknown unit `{r}`"));
                }
            }
            for r in duplicate_strings(&dep_list) {
                errors.push(format!("{uid}: depends_on has duplicate entry `{r}`"));
            }
            for r in &block_list {
                if r == uid {
                    errors.push(format!("{uid}: blocks includes self"));
                } else if !uids.contains(r) {
                    errors.push(format!("{uid}: blocks references unknown unit `{r}`"));
                }
            }
            for r in duplicate_strings(&block_list) {
                errors.push(format!("{uid}: blocks has duplicate entry `{r}`"));
            }
            deps.insert(uid.clone(), dep_list.into_iter().collect());
            blocks.insert(uid.clone(), block_list.into_iter().collect());
        }
        for (a, bs) in &blocks {
            for b in bs {
                if uids.contains(b) && !deps.get(b).is_some_and(|set| set.contains(a)) {
                    errors.push(format!(
                        "inverse mismatch: {a}.blocks contains `{b}` but {b}.depends_on is missing `{a}`"
                    ));
                }
            }
        }
        for (b, ds) in &deps {
            for a in ds {
                if uids.contains(a) && !blocks.get(a).is_some_and(|set| set.contains(b)) {
                    errors.push(format!(
                        "inverse mismatch: {b}.depends_on contains `{a}` but {a}.blocks is missing `{b}`"
                    ));
                }
            }
        }
        (errors, (deps, blocks))
    }

    fn detect_cycles(dep_sets: &BTreeMap<String, BTreeSet<String>>) -> Vec<String> {
        fn visit(
            node: &str,
            dep_sets: &BTreeMap<String, BTreeSet<String>>,
            stack: &mut Vec<String>,
            seen: &mut BTreeSet<String>,
            errors: &mut Vec<String>,
        ) {
            if let Some(pos) = stack.iter().position(|n| n == node) {
                let mut cycle = stack[pos..].to_vec();
                cycle.push(node.to_string());
                errors.push(format!("cycle in depends_on: {}", cycle.join(" -> ")));
                return;
            }
            if !seen.insert(node.to_string()) {
                return;
            }
            stack.push(node.to_string());
            if let Some(deps) = dep_sets.get(node) {
                for dep in deps {
                    visit(dep, dep_sets, stack, seen, errors);
                }
            }
            stack.pop();
        }
        let mut errors = Vec::new();
        let mut seen = BTreeSet::new();
        for node in dep_sets.keys() {
            visit(node, dep_sets, &mut Vec::new(), &mut seen, &mut errors);
        }
        errors
    }

    fn validate_artifacts(units: &BTreeMap<String, &toml::map::Map<String, Value>>) -> Vec<String> {
        let mut errors = Vec::new();
        let mut producers: BTreeMap<String, Vec<String>> = BTreeMap::new();
        for (uid, unit) in units {
            for art in str_vec(unit.get("produces")).unwrap_or_default() {
                producers.entry(art).or_default().push(uid.clone());
            }
        }
        for (art, ps) in &producers {
            if !(art.starts_with("ART:") || art.starts_with("OUT:")) {
                errors.push(format!(
                    "{}: produces `{art}` has unrecognized prefix (expected ART: or OUT:)",
                    ps[0]
                ));
            }
            if ps.len() > 1 {
                errors.push(format!("artifact `{art}` has multiple producers: {ps:?}"));
            }
        }
        for (uid, unit) in units {
            for art in str_vec(unit.get("consumes")).unwrap_or_default() {
                if !(art.starts_with("ART:") || art.starts_with("OUT:")) {
                    errors.push(format!(
                        "{uid}: consumes `{art}` has unrecognized prefix (expected ART: or OUT:)"
                    ));
                } else if !producers.contains_key(&art) {
                    errors.push(format!(
                        "{uid}: consumes `{art}` which is not produced by any unit in the DAG"
                    ));
                }
            }
        }
        errors
    }

    fn validate_layer_ordering(
        units: &BTreeMap<String, &toml::map::Map<String, Value>>,
        dep_sets: &BTreeMap<String, BTreeSet<String>>,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        for (u, deps) in dep_sets {
            let Some(ul) = int_value(units.get(u).and_then(|unit| unit.get("layer"))) else {
                continue;
            };
            for d in deps {
                let Some(dl) = int_value(units.get(d).and_then(|unit| unit.get("layer"))) else {
                    continue;
                };
                if ul <= dl {
                    errors.push(format!(
                        "layer ordering: {u} (layer={ul}) depends_on {d} (layer={dl}) — a depender must be in a strictly higher layer"
                    ));
                }
            }
        }
        errors
    }

    fn validate_meta(
        doc: &Value,
        units: &BTreeMap<String, &toml::map::Map<String, Value>>,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        let Some(meta) = table(doc, "meta") else {
            return errors;
        };
        if let Some(total) = int_value(meta.get("total_units")) {
            if total != units.len() as i64 {
                errors.push(format!(
                    "meta.total_units={total} but units table has {} entries",
                    units.len()
                ));
            }
        }
        let mut by_tier: BTreeMap<i64, BTreeSet<String>> = BTreeMap::new();
        for (uid, unit) in units {
            if let Some(tier @ 1..=3) = int_value(unit.get("tier")) {
                by_tier.entry(tier).or_default().insert(uid.clone());
            }
        }
        for tier in 1..=3 {
            let key = format!("tier{tier}_units");
            let Some(declared_vec) = str_vec(meta.get(&key)) else {
                continue;
            };
            let declared: BTreeSet<String> = declared_vec.into_iter().collect();
            let actual = by_tier.get(&tier).cloned().unwrap_or_default();
            for extra in declared.difference(&actual) {
                errors.push(format!(
                    "meta.{key} lists `{extra}` but that unit does not have tier={tier}"
                ));
            }
            for missing in actual.difference(&declared) {
                errors.push(format!(
                    "meta.{key} is missing `{missing}` (unit has tier={tier})"
                ));
            }
        }
        errors
    }

    fn longest_path_loc(
        units: &BTreeMap<String, &toml::map::Map<String, Value>>,
        blocks: &BTreeMap<String, BTreeSet<String>>,
    ) -> Option<i64> {
        fn dfs(
            node: &str,
            units: &BTreeMap<String, &toml::map::Map<String, Value>>,
            blocks: &BTreeMap<String, BTreeSet<String>>,
            visiting: &mut BTreeSet<String>,
            memo: &mut BTreeMap<String, i64>,
        ) -> Option<i64> {
            if let Some(v) = memo.get(node) {
                return Some(*v);
            }
            if !visiting.insert(node.to_string()) {
                return None;
            }
            let own =
                int_value(units.get(node).and_then(|unit| unit.get("estimated_loc"))).unwrap_or(0);
            let mut best_tail = 0;
            for next in blocks.get(node).cloned().unwrap_or_default() {
                if units.contains_key(&next) {
                    best_tail = best_tail.max(dfs(&next, units, blocks, visiting, memo)?);
                }
            }
            visiting.remove(node);
            let total = own + best_tail;
            memo.insert(node.to_string(), total);
            Some(total)
        }
        let mut memo = BTreeMap::new();
        let mut best = 0;
        for node in units.keys() {
            best = best.max(dfs(node, units, blocks, &mut BTreeSet::new(), &mut memo)?);
        }
        Some(best)
    }

    fn validate_computed(
        doc: &Value,
        units: &BTreeMap<String, &toml::map::Map<String, Value>>,
        deps: &BTreeMap<String, BTreeSet<String>>,
        blocks: &BTreeMap<String, BTreeSet<String>>,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        let Some(computed) = table(doc, "computed") else {
            return errors;
        };
        let actual_entry: BTreeSet<String> = units
            .keys()
            .filter(|u| deps.get(*u).is_none_or(BTreeSet::is_empty))
            .cloned()
            .collect();
        if let Some(declared_vec) = str_vec(computed.get("entry_points")) {
            let declared: BTreeSet<String> = declared_vec.into_iter().collect();
            for extra in declared.difference(&actual_entry) {
                errors.push(format!(
                    "computed.entry_points lists `{extra}` but its depends_on is non-empty"
                ));
            }
            for missing in actual_entry.difference(&declared) {
                errors.push(format!(
                    "computed.entry_points is missing `{missing}` (has empty depends_on)"
                ));
            }
        }
        let actual_leaf: BTreeSet<String> = units
            .keys()
            .filter(|u| blocks.get(*u).is_none_or(BTreeSet::is_empty))
            .cloned()
            .collect();
        if let Some(declared_vec) = str_vec(computed.get("leaf_nodes")) {
            let declared: BTreeSet<String> = declared_vec.into_iter().collect();
            for extra in declared.difference(&actual_leaf) {
                errors.push(format!(
                    "computed.leaf_nodes lists `{extra}` but its blocks is non-empty"
                ));
            }
            for missing in actual_leaf.difference(&declared) {
                errors.push(format!(
                    "computed.leaf_nodes is missing `{missing}` (has empty blocks)"
                ));
            }
        }
        let mut actual_layers: BTreeMap<i64, i64> = BTreeMap::new();
        let mut actual_all = 0;
        let mut actual_tier: BTreeMap<i64, i64> = BTreeMap::new();
        for unit in units.values() {
            if let Some(layer) = int_value(unit.get("layer")) {
                *actual_layers.entry(layer).or_default() += 1;
            }
            let loc = int_value(unit.get("estimated_loc")).unwrap_or(0);
            actual_all += loc;
            if let Some(tier @ 1..=3) = int_value(unit.get("tier")) {
                *actual_tier.entry(tier).or_default() += loc;
            }
        }
        if let Some(mp) = computed.get("max_parallel").and_then(Value::as_table) {
            for (layer, count) in &actual_layers {
                let key = format!("layer{layer}");
                match int_value(mp.get(&key)) {
                    None => errors.push(format!(
                        "computed.max_parallel is missing `{key}` (actual count={count})"
                    )),
                    Some(v) if v != *count => errors.push(format!(
                        "computed.max_parallel.{key}={v} but {count} unit(s) actually in layer {layer}"
                    )),
                    _ => {}
                }
            }
            for (key, value) in mp {
                if let Some(rest) = key.strip_prefix("layer") {
                    if let Ok(layer) = rest.parse::<i64>() {
                        if !actual_layers.contains_key(&layer) {
                            errors.push(format!(
                                "computed.max_parallel.{key}={} but no units are in layer {layer}",
                                value.as_integer().unwrap_or_default()
                            ));
                        }
                    } else {
                        errors.push(format!("computed.max_parallel has malformed key `{key}`"));
                    }
                }
            }
        }
        if let Some(loc) = computed.get("loc_totals").and_then(Value::as_table) {
            if let Some(all) = int_value(loc.get("all")) {
                if all != actual_all {
                    errors.push(format!(
                        "computed.loc_totals.all={all} but sum of estimated_loc={actual_all}"
                    ));
                }
            }
            for tier in 1..=3 {
                let key = format!("tier{tier}");
                if let Some(v) = int_value(loc.get(&key)) {
                    let actual = actual_tier.get(&tier).copied().unwrap_or(0);
                    if v != actual {
                        errors.push(format!(
                            "computed.loc_totals.{key}={v} but actual sum for tier-{tier} units={actual}"
                        ));
                    }
                }
            }
        }
        let cp = str_vec(computed.get("critical_path")).unwrap_or_default();
        let cp_loc = int_value(computed.get("critical_path_loc"));
        if cp.is_empty() {
            if let Some(v) = cp_loc {
                errors.push(format!(
                    "computed.critical_path_loc={v} but critical_path is empty or missing"
                ));
            }
            return errors;
        }
        let mut bad_ref = false;
        for (idx, unit) in cp.iter().enumerate() {
            if !units.contains_key(unit) {
                errors.push(format!(
                    "computed.critical_path[{idx}]=`{unit}` references unknown unit"
                ));
                bad_ref = true;
            }
        }
        if !bad_ref {
            for pair in cp.windows(2) {
                if !blocks
                    .get(&pair[0])
                    .is_some_and(|set| set.contains(&pair[1]))
                {
                    errors.push(format!(
                        "computed.critical_path: {} -> {} is not a direct dependency edge",
                        pair[0], pair[1]
                    ));
                }
            }
            if !deps.get(&cp[0]).is_none_or(BTreeSet::is_empty) {
                errors.push(format!(
                    "computed.critical_path starts at `{}` which is not an entry point",
                    cp[0]
                ));
            }
            if !blocks
                .get(cp.last().unwrap())
                .is_none_or(BTreeSet::is_empty)
            {
                errors.push(format!(
                    "computed.critical_path ends at `{}` which is not a leaf",
                    cp.last().unwrap()
                ));
            }
            let cp_actual: i64 = cp
                .iter()
                .map(|u| {
                    int_value(units.get(u).and_then(|unit| unit.get("estimated_loc"))).unwrap_or(0)
                })
                .sum();
            if let Some(v) = cp_loc {
                if v != cp_actual {
                    errors.push(format!(
                        "computed.critical_path_loc={v} but sum along path={cp_actual}"
                    ));
                }
            }
            if let Some(longest) = longest_path_loc(units, blocks) {
                if cp_actual < longest {
                    errors.push(format!(
                        "computed.critical_path LOC={cp_actual} but a longer path exists with LOC={longest}"
                    ));
                }
            }
        }
        errors
    }

    fn validate_paths(units: &UnitMap<'_>) -> Vec<String> {
        // Mirrors the Python reference validator's default placeholder
        // policy: unresolved markers in unit file claims are rejected.
        let mut errors = Vec::new();
        for (uid, unit) in units {
            for field in ["files_create", "files_modify"] {
                if let Some(files) = str_vec(unit.get(field)) {
                    for file in files {
                        if has_placeholder(&file) {
                            errors
                                .push(format!("{uid}.{field}: placeholder not allowed: `{file}`"));
                        }
                    }
                }
            }
        }
        errors
    }

    #[allow(clippy::type_complexity)]
    pub fn validate(_path: &Path, doc: &Value) -> Vec<String> {
        let (mut errors, units) = validate_units(doc);
        if units.is_empty() {
            return errors;
        }
        let (edge_errors, (deps, blocks)) = validate_edges(&units);
        errors.extend(edge_errors);
        errors.extend(detect_cycles(&deps));
        errors.extend(validate_artifacts(&units));
        errors.extend(validate_layer_ordering(&units, &deps));
        errors.extend(validate_meta(doc, &units));
        errors.extend(validate_computed(doc, &units, &deps, &blocks));
        errors.extend(validate_paths(&units));
        errors
    }
}

// ------------------------------------------------------------
// Core traceability validation
// ------------------------------------------------------------

mod traceability {
    use super::{Value, array};
    use std::collections::{BTreeMap, BTreeSet};
    use std::path::Path;

    const SECTIONS: &[&str] = &[
        "intents",
        "features",
        "requirements",
        "regulations",
        "decisions",
        "implementations",
        "code",
        "tests",
        "outputs",
    ];

    fn link_fields(section: &str) -> &'static [&'static str] {
        match section {
            "intents" => &["derived_from", "realized_by"],
            "features" => &["realizes", "constrained_by", "implemented_by", "produces"],
            "requirements" | "regulations" => &["constrains", "verified_by"],
            "decisions" => &["addresses", "shapes", "supersedes"],
            "implementations" => &[
                "implements",
                "guided_by",
                "code",
                "tests",
                "downstream_outputs",
            ],
            "code" => &["realizes"],
            "tests" => &["verifies"],
            "outputs" => &["realizes"],
            _ => &[],
        }
    }

    fn downstream_fields(section: &str) -> &'static [&'static str] {
        match section {
            "intents" => &["realized_by"],
            "features" => &["implemented_by", "produces"],
            "requirements" | "regulations" => &["verified_by", "constrains"],
            "decisions" => &["shapes"],
            "implementations" => &["code", "tests", "downstream_outputs"],
            "code" => &["realizes"],
            "tests" => &["verifies"],
            "outputs" => &["realizes"],
            _ => &[],
        }
    }

    fn str_vec(value: Option<&Value>) -> Vec<String> {
        value
            .and_then(Value::as_array)
            .map(|arr| {
                arr.iter()
                    .filter_map(Value::as_str)
                    .map(ToString::to_string)
                    .collect()
            })
            .unwrap_or_default()
    }

    fn has_placeholder(value: &str) -> bool {
        value.contains('<') || value.contains('>') || value.contains("YYYY-MM-DD")
    }

    type EntityMap<'a> = BTreeMap<String, (&'static str, &'a toml::map::Map<String, Value>)>;

    fn gather_entities(doc: &Value) -> (EntityMap<'_>, Vec<String>) {
        let mut entities = BTreeMap::new();
        let mut errors = Vec::new();
        for section in SECTIONS {
            for entry in array(doc, section) {
                let Some(t) = entry.as_table() else {
                    continue;
                };
                let Some(id) = t.get("id").and_then(Value::as_str) else {
                    errors.push(format!("{section}: missing required `id` field"));
                    continue;
                };
                if entities.insert(id.to_string(), (*section, t)).is_some() {
                    errors.push(format!("duplicate id: {id}"));
                }
            }
        }
        (entities, errors)
    }

    fn validate_links(doc: &Value, entities: &EntityMap<'_>) -> Vec<String> {
        let mut errors = Vec::new();
        for section in SECTIONS {
            for entry in array(doc, section) {
                let Some(t) = entry.as_table() else {
                    continue;
                };
                let id = t
                    .get("id")
                    .and_then(Value::as_str)
                    .unwrap_or("<missing-id>");
                for field in link_fields(section) {
                    for target in str_vec(t.get(*field)) {
                        if !entities.contains_key(&target) {
                            errors.push(format!("{id}: `{field}` target missing: {target}"));
                        }
                    }
                }
            }
        }
        for relation in array(doc, "relations") {
            let Some(t) = relation.as_table() else {
                continue;
            };
            let source = t.get("from").and_then(Value::as_str).unwrap_or("");
            let target = t.get("to").and_then(Value::as_str).unwrap_or("");
            let relation_type = t
                .get("type")
                .and_then(Value::as_str)
                .unwrap_or("<missing-type>");
            if !entities.contains_key(source) {
                errors.push(format!(
                    "relation `{relation_type}` missing `from` target: {source}"
                ));
            }
            if !entities.contains_key(target) {
                errors.push(format!(
                    "relation `{relation_type}` missing `to` target: {target}"
                ));
            }
        }
        errors
    }

    fn build_forward_graph(doc: &Value) -> BTreeMap<String, BTreeSet<String>> {
        let mut graph: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
        for section in SECTIONS {
            for entry in array(doc, section) {
                let Some(t) = entry.as_table() else {
                    continue;
                };
                let Some(id) = t.get("id").and_then(Value::as_str) else {
                    continue;
                };
                for field in downstream_fields(section) {
                    for target in str_vec(t.get(*field)) {
                        graph.entry(id.to_string()).or_default().insert(target);
                    }
                }
            }
        }
        graph
    }

    fn reachable(
        graph: &BTreeMap<String, BTreeSet<String>>,
        start: &str,
        prefixes: &[&str],
    ) -> bool {
        let mut stack = vec![start.to_string()];
        let mut seen = BTreeSet::new();
        while let Some(current) = stack.pop() {
            if !seen.insert(current.clone()) {
                continue;
            }
            if current != start && prefixes.iter().any(|prefix| current.starts_with(prefix)) {
                return true;
            }
            if let Some(nexts) = graph.get(&current) {
                stack.extend(nexts.iter().cloned());
            }
        }
        false
    }

    fn detect_cycles(doc: &Value) -> Vec<String> {
        let mut errors = Vec::new();
        for (section, field) in [("intents", "derived_from"), ("decisions", "supersedes")] {
            let mut graph: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
            for entry in array(doc, section) {
                let Some(t) = entry.as_table() else {
                    continue;
                };
                let Some(id) = t.get("id").and_then(Value::as_str) else {
                    continue;
                };
                for target in str_vec(t.get(field)) {
                    graph.entry(id.to_string()).or_default().insert(target);
                }
            }
            fn visit(
                node: &str,
                graph: &BTreeMap<String, BTreeSet<String>>,
                visiting: &mut BTreeSet<String>,
                visited: &mut BTreeSet<String>,
            ) -> bool {
                if visited.contains(node) {
                    return false;
                }
                if !visiting.insert(node.to_string()) {
                    return true;
                }
                for next in graph.get(node).cloned().unwrap_or_default() {
                    if visit(&next, graph, visiting, visited) {
                        return true;
                    }
                }
                visiting.remove(node);
                visited.insert(node.to_string());
                false
            }
            let mut visiting = BTreeSet::new();
            let mut visited = BTreeSet::new();
            for node in graph.keys() {
                if visit(node, &graph, &mut visiting, &mut visited) {
                    errors.push(format!(
                        "{section}: `{field}` contains a cycle involving {node}"
                    ));
                    break;
                }
            }
        }
        errors
    }

    fn validate_downstream_realization(doc: &Value) -> Vec<String> {
        let mut errors = Vec::new();
        let graph = build_forward_graph(doc);
        for section in ["requirements", "regulations"] {
            for entry in array(doc, section) {
                let Some(id) = entry
                    .as_table()
                    .and_then(|t| t.get("id"))
                    .and_then(Value::as_str)
                else {
                    continue;
                };
                if !reachable(&graph, id, &["CODE:", "TEST:", "OUT:", "IMP:"]) {
                    errors.push(format!(
                        "{id}: no downstream realization path to implementation, code, tests, or outputs"
                    ));
                }
            }
        }
        errors
    }

    fn validate_paths(doc: &Value) -> Vec<String> {
        let mut errors = Vec::new();
        for section in ["code", "tests"] {
            for entry in array(doc, section) {
                let Some(t) = entry.as_table() else {
                    continue;
                };
                let id = t
                    .get("id")
                    .and_then(Value::as_str)
                    .unwrap_or("<missing-id>");
                let path = t.get("path").and_then(Value::as_str).unwrap_or("");
                if path.is_empty() {
                    errors.push(format!("{id}: missing `path`"));
                } else if has_placeholder(path) {
                    errors.push(format!("{id}: placeholder path not allowed: {path}"));
                }
            }
        }
        errors
    }

    fn validate_placeholders(doc: &Value) -> Vec<String> {
        let mut errors = Vec::new();
        for section in SECTIONS {
            for entry in array(doc, section) {
                if let Some(id) = entry
                    .as_table()
                    .and_then(|t| t.get("id"))
                    .and_then(Value::as_str)
                {
                    if has_placeholder(id) {
                        errors.push(format!("{section}: placeholder id not allowed: {id}"));
                    }
                }
            }
        }
        errors
    }

    fn validate_computed(doc: &Value, entities: &EntityMap<'_>) -> Vec<String> {
        let mut errors = Vec::new();
        let Some(computed) = super::table(doc, "computed") else {
            return errors;
        };
        for field in [
            "root_intents",
            "terminal_outputs",
            "unverified_requirements",
            "unmapped_code",
            "coverage_gaps",
        ] {
            for target in str_vec(computed.get(field)) {
                if !target.is_empty() && field != "coverage_gaps" && !entities.contains_key(&target)
                {
                    errors.push(format!("computed `{field}` target missing: {target}"));
                }
            }
        }
        errors
    }

    pub fn validate(_path: &Path, doc: &Value) -> Vec<String> {
        let (entities, mut errors) = gather_entities(doc);
        errors.extend(validate_placeholders(doc));
        errors.extend(validate_links(doc, &entities));
        errors.extend(detect_cycles(doc));
        errors.extend(validate_downstream_realization(doc));
        errors.extend(validate_paths(doc));
        errors.extend(validate_computed(doc, &entities));
        errors
    }
}

// ------------------------------------------------------------
// Review-readiness validation
// ------------------------------------------------------------

mod review_readiness {
    use super::{Value, table};
    use std::collections::BTreeMap;
    use std::path::Path;

    fn has_placeholder(value: &str) -> bool {
        value.contains('<') || value.contains('>') || value.contains("YYYY-MM-DD")
    }

    fn normalize_kind(value: Option<&str>) -> Option<&'static str> {
        match value?
            .trim()
            .to_ascii_lowercase()
            .replace('_', "-")
            .as_str()
        {
            "readiness-gate" | "readiness" | "gate-readiness" => Some("readiness-gate"),
            "contract-declaration" | "contract" | "contracts" => Some("contract-declaration"),
            "evidence-matrix" | "evidence" | "matrix" => Some("evidence-matrix"),
            _ => None,
        }
    }

    fn section_aliases(kind: &str) -> &'static [(&'static str, &'static [&'static str])] {
        match kind {
            "readiness-gate" => &[
                (
                    "artifact_classes",
                    &[
                        "artifact_classes",
                        "artifacts",
                        "readiness.artifact_classes",
                    ],
                ),
                ("gates", &["gates", "readiness_gates", "readiness.gates"]),
            ],
            "contract-declaration" => &[(
                "contracts",
                &["contracts", "declarations", "contract_declarations"],
            )],
            "evidence-matrix" => &[
                ("claims", &["claims", "assertions"]),
                ("evidence", &["evidence", "artifacts", "evidence_artifacts"]),
                ("matrix", &["matrix", "rows", "evidence_matrix"]),
            ],
            _ => &[],
        }
    }

    fn required_fields(kind: &str, section: &str) -> &'static [&'static [&'static str]] {
        match (kind, section) {
            ("readiness-gate", "artifact_classes") => &[&["id"]],
            ("readiness-gate", "gates") => &[
                &["id"],
                &["artifact_class"],
                &["checks", "required_documents", "criteria", "summary"],
            ],
            ("contract-declaration", "contracts") => &[
                &["id"],
                &["statement", "contract", "summary"],
                &["applies_to", "depends_on", "supersedes", "verified_by"],
            ],
            ("evidence-matrix", "claims") => &[&["id"], &["claim", "statement", "assertion"]],
            ("evidence-matrix", "evidence") => &[
                &["id"],
                &["path", "artifact_path", "evidence_path", "file_path"],
            ],
            ("evidence-matrix", "matrix") => &[
                &["id"],
                &["claim", "claim_id"],
                &["evidence", "evidence_id"],
                &["scope_covered", "scope"],
                &["known_exclusions", "exclusions", "limitations"],
            ],
            _ => &[],
        }
    }

    fn link_fields(kind: &str, section: &str) -> &'static [(&'static str, Option<&'static str>)] {
        match (kind, section) {
            ("readiness-gate", "gates") => &[("artifact_class", Some("artifact_classes"))],
            ("contract-declaration", "contracts") => &[
                ("depends_on", Some("contracts")),
                ("supersedes", Some("contracts")),
                ("related_to", Some("contracts")),
                ("verified_by", None),
                ("applies_to", None),
            ],
            ("evidence-matrix", "matrix") => &[
                ("claim", Some("claims")),
                ("claim_id", Some("claims")),
                ("evidence", Some("evidence")),
                ("evidence_id", Some("evidence")),
            ],
            _ => &[],
        }
    }

    fn section_value<'a>(doc: &'a Value, dotted: &str) -> Option<&'a Value> {
        let mut current = doc;
        for part in dotted.split('.') {
            current = current.get(part)?;
        }
        Some(current)
    }

    fn entries_from_value(value: &Value) -> Vec<&toml::map::Map<String, Value>> {
        if let Some(arr) = value.as_array() {
            arr.iter().filter_map(Value::as_table).collect()
        } else if let Some(t) = value.as_table() {
            vec![t]
        } else {
            vec![]
        }
    }

    fn str_targets(value: Option<&Value>) -> Vec<String> {
        match value {
            Some(Value::String(s)) => vec![s.clone()],
            Some(Value::Array(arr)) => arr
                .iter()
                .filter_map(Value::as_str)
                .map(ToString::to_string)
                .collect(),
            _ => vec![],
        }
    }

    fn detect_kind(doc: &Value) -> Option<&'static str> {
        if let Some(meta) = table(doc, "meta") {
            for key in ["template_kind", "kind", "control_kind", "template"] {
                if let Some(kind) = normalize_kind(meta.get(key).and_then(Value::as_str)) {
                    return Some(kind);
                }
            }
        }
        if doc.get("contracts").is_some()
            || doc.get("declarations").is_some()
            || doc.get("contract_declarations").is_some()
        {
            return Some("contract-declaration");
        }
        if (doc.get("gates").is_some() || doc.get("readiness_gates").is_some())
            && (doc.get("artifact_classes").is_some() || doc.get("artifacts").is_some())
        {
            return Some("readiness-gate");
        }
        if (doc.get("claims").is_some() || doc.get("matrix").is_some())
            && (doc.get("evidence").is_some() || doc.get("artifacts").is_some())
        {
            return Some("evidence-matrix");
        }
        None
    }

    fn collect_placeholders(value: &Value, prefix: &str, errors: &mut Vec<String>) {
        match value {
            Value::String(s) => {
                if has_placeholder(s) {
                    errors.push(format!("placeholder value not allowed at {prefix}"));
                }
            }
            Value::Array(arr) => {
                for (idx, item) in arr.iter().enumerate() {
                    collect_placeholders(item, &format!("{prefix}[{idx}]"), errors);
                }
            }
            Value::Table(t) => {
                for (k, v) in t {
                    let sub = if prefix.is_empty() {
                        k.to_string()
                    } else {
                        format!("{prefix}.{k}")
                    };
                    collect_placeholders(v, &sub, errors);
                }
            }
            _ => {}
        }
    }

    fn value_present(entry: &toml::map::Map<String, Value>, field: &str) -> bool {
        match entry.get(field) {
            Some(Value::String(s)) => !s.is_empty(),
            Some(Value::Array(a)) => !a.is_empty(),
            Some(Value::Table(t)) => !t.is_empty(),
            Some(_) => true,
            None => false,
        }
    }

    pub fn validate(_path: &Path, doc: &Value) -> Vec<String> {
        let mut errors = Vec::new();
        let Some(kind) = detect_kind(doc) else {
            return vec!["unable to detect template kind from TOML content".to_string()];
        };
        if let Some(meta) = table(doc, "meta") {
            if let Some(rv) = meta.get("release_version").and_then(Value::as_str) {
                if rv != "0.1.0" {
                    errors.push(format!(
                        "meta.release_version ({rv}) does not match expected 0.1.0"
                    ));
                }
            }
        } else {
            errors.push("missing required `meta` section".to_string());
        }

        let mut resolved: BTreeMap<&str, Vec<&toml::map::Map<String, Value>>> = BTreeMap::new();
        for (canonical, aliases) in section_aliases(kind) {
            let mut found: Option<&Value> = None;
            let mut found_alias = "";
            for alias in *aliases {
                if let Some(value) = section_value(doc, alias) {
                    found = Some(value);
                    found_alias = alias;
                    break;
                }
            }
            let Some(raw) = found else {
                errors.push(format!("missing required `{canonical}` section"));
                continue;
            };
            if !(raw.is_table() || raw.is_array()) {
                errors.push(format!(
                    "`{found_alias}` must be a table or array of tables"
                ));
                continue;
            }
            if let Some(arr) = raw.as_array() {
                if arr.is_empty() {
                    errors.push(format!("`{found_alias}` must contain at least one entry"));
                }
                for (idx, item) in arr.iter().enumerate() {
                    if !item.is_table() {
                        errors.push(format!(
                            "`{found_alias}` entry at index {idx} must be a table"
                        ));
                    }
                }
            }
            resolved.insert(canonical, entries_from_value(raw));
        }

        let mut id_index: BTreeMap<String, &str> = BTreeMap::new();
        for (section, entries) in &resolved {
            for (idx, entry) in entries.iter().enumerate() {
                let Some(id) = entry.get("id").and_then(Value::as_str) else {
                    errors.push(format!("{section}: missing required `id` field"));
                    continue;
                };
                if id_index.insert(id.to_string(), section).is_some() {
                    errors.push(format!("duplicate id across sections: {id}"));
                }
                for group in required_fields(kind, section) {
                    if !group.iter().any(|field| value_present(entry, field)) {
                        if group.len() == 1 {
                            errors.push(format!("{id}: missing required `{}` field", group[0]));
                        } else {
                            errors.push(format!(
                                "{id}: missing required `{}` field",
                                group.join("` or `")
                            ));
                        }
                    }
                }
                let _ = idx;
            }
        }

        for (section, fields) in section_aliases(kind) {
            let _ = fields;
            for entry in resolved.get(section).cloned().unwrap_or_default() {
                let id = entry
                    .get("id")
                    .and_then(Value::as_str)
                    .unwrap_or("<missing-id>");
                for (field, target_section) in link_fields(kind, section) {
                    for target in str_targets(entry.get(*field)) {
                        let Some(expected_section) = target_section else {
                            continue;
                        };
                        match id_index.get(&target) {
                            None => errors.push(format!("{id}: `{field}` target missing: {target}")),
                            Some(actual) if actual != expected_section => errors.push(format!(
                                "{id}: `{field}` target must reference `{expected_section}` ids: {target}"
                            )),
                            _ => {}
                        }
                    }
                }
            }
        }

        collect_placeholders(doc, "", &mut errors);
        errors
    }
}

// ------------------------------------------------------------
// Cost-record profile validation
// ------------------------------------------------------------

mod cost_record {
    use super::{Value, load, table};
    use std::collections::BTreeSet;
    use std::path::Path;

    const REQUIRED_RECORD_FIELDS: &[&str] = &[
        "action_id",
        "incurred_at",
        "citing_kind",
        "citing_ref",
        "decider_class",
        "producer_id",
        "hash_algorithm",
        "canonical_form",
    ];

    struct CostVocabs {
        decider: BTreeSet<String>,
        citing: BTreeSet<String>,
        dimension: BTreeSet<String>,
    }

    fn string_set(doc: &Value, attribute: &str) -> BTreeSet<String> {
        let mut out = BTreeSet::new();
        for block in doc
            .get("attribute_vocabularies")
            .and_then(Value::as_array)
            .map(Vec::as_slice)
            .unwrap_or(&[])
        {
            let Some(t) = block.as_table() else { continue };
            if t.get("attribute").and_then(Value::as_str) != Some(attribute) {
                continue;
            }
            if let Some(values) = t.get("values").and_then(Value::as_array) {
                out.extend(
                    values
                        .iter()
                        .filter_map(Value::as_str)
                        .map(ToString::to_string),
                );
            }
        }
        out
    }

    fn load_vocab(repo_root: &Path) -> Result<CostVocabs, String> {
        let ont_path = repo_root.join("profiles/cost/ontology.toml");
        let doc = load(&ont_path)?;
        let decider = string_set(&doc, "decider_class");
        let citing = string_set(&doc, "cost_citing_kind");
        let dimension = string_set(&doc, "cost_dimension_category");
        let mut missing = Vec::new();
        if decider.is_empty() {
            missing.push("decider_class");
        }
        if citing.is_empty() {
            missing.push("cost_citing_kind");
        }
        if dimension.is_empty() {
            missing.push("cost_dimension_category");
        }
        if !missing.is_empty() {
            return Err(format!(
                "cost-profile ontology is missing required vocabularies: {missing:?}"
            ));
        }
        Ok(CostVocabs {
            decider,
            citing,
            dimension,
        })
    }

    fn is_rfc3339_datetime(value: &str) -> bool {
        let bytes = value.as_bytes();
        if bytes.len() < 20 {
            return false;
        }
        let digit = |idx: usize| bytes.get(idx).is_some_and(u8::is_ascii_digit);
        for idx in [0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18] {
            if !digit(idx) {
                return false;
            }
        }
        if bytes[4] != b'-'
            || bytes[7] != b'-'
            || bytes[10] != b'T'
            || bytes[13] != b':'
            || bytes[16] != b':'
        {
            return false;
        }
        let mut idx = 19;
        if bytes.get(idx) == Some(&b'.') {
            idx += 1;
            let start = idx;
            while bytes.get(idx).is_some_and(u8::is_ascii_digit) {
                idx += 1;
            }
            if idx == start {
                return false;
            }
        }
        match bytes.get(idx) {
            Some(b'Z') => idx + 1 == bytes.len(),
            Some(b'+') | Some(b'-') => {
                idx + 6 == bytes.len()
                    && digit(idx + 1)
                    && digit(idx + 2)
                    && bytes[idx + 3] == b':'
                    && digit(idx + 4)
                    && digit(idx + 5)
            }
            _ => false,
        }
    }

    pub fn validate(path: &Path, doc: &Value, repo_root: &Path) -> Vec<String> {
        let mut errors = Vec::new();
        let Ok(vocab) = load_vocab(repo_root) else {
            return vec!["cost-profile ontology could not be loaded".to_string()];
        };
        let Some(meta) = table(doc, "meta") else {
            return vec![format!(
                "{}: not a cost-record instance (meta.template_kind != 'cost-record')",
                path.display()
            )];
        };
        if meta.get("template_kind").and_then(Value::as_str) != Some("cost-record") {
            return vec![format!(
                "{}: not a cost-record instance (meta.template_kind != 'cost-record')",
                path.display()
            )];
        }
        if meta.get("framework_profile").and_then(Value::as_str) != Some("cost") {
            errors.push(format!(
                "{}: meta.framework_profile must be 'cost', got {:?}",
                path.display(),
                meta.get("framework_profile")
            ));
        }
        let Some(record) = table(doc, "record") else {
            errors.push(format!(
                "{}: missing required `[record]` table",
                path.display()
            ));
            return errors;
        };
        for field in REQUIRED_RECORD_FIELDS {
            match record.get(*field).and_then(Value::as_str) {
                Some(v) if !v.is_empty() => {}
                _ => errors.push(format!(
                    "{}: record.{field} must be a non-empty string",
                    path.display()
                )),
            }
        }
        if let Some(incurred_at) = record.get("incurred_at").and_then(Value::as_str) {
            if !is_rfc3339_datetime(incurred_at) {
                errors.push(format!(
                    "{}: record.incurred_at must be RFC 3339 date-time, got {incurred_at:?}",
                    path.display()
                ));
            }
        }
        if let Some(citing_kind) = record.get("citing_kind").and_then(Value::as_str) {
            if !vocab.citing.contains(citing_kind) {
                errors.push(format!(
                    "{}: record.citing_kind {citing_kind:?} not in closed vocabulary",
                    path.display()
                ));
            }
        }
        if let Some(decider_class) = record.get("decider_class").and_then(Value::as_str) {
            if !vocab.decider.contains(decider_class) {
                errors.push(format!(
                    "{}: record.decider_class {decider_class:?} not in closed vocabulary",
                    path.display()
                ));
            }
        }
        if let Some(hash_algorithm) = record.get("hash_algorithm").and_then(Value::as_str) {
            if matches!(hash_algorithm.to_ascii_lowercase().as_str(), "md5" | "sha1") {
                errors.push(format!(
                    "{}: record.hash_algorithm {hash_algorithm:?} is forbidden by SPEC §12.1",
                    path.display()
                ));
            }
        }
        let dims = record.get("dimensions").and_then(Value::as_array);
        match dims.map(Vec::as_slice) {
            None | Some([]) => errors.push(format!(
                "{}: at least one `[[record.dimensions]]` entry is required",
                path.display()
            )),
            Some(dimensions) => {
                for (idx, dim) in dimensions.iter().enumerate() {
                    let Some(t) = dim.as_table() else {
                        errors.push(format!(
                            "{}: record.dimensions[{idx}] must be a table",
                            path.display()
                        ));
                        continue;
                    };
                    match t.get("category").and_then(Value::as_str) {
                        Some(category) if vocab.dimension.contains(category) => {}
                        other => errors.push(format!(
                            "{}: record.dimensions[{idx}].category {:?} not in closed vocabulary",
                            path.display(),
                            other
                        )),
                    }
                    match t.get("quantity").and_then(Value::as_integer) {
                        Some(q) if q >= 0 => {}
                        other => errors.push(format!(
                            "{}: record.dimensions[{idx}].quantity must be a non-negative integer; got {:?}",
                            path.display(),
                            other
                        )),
                    }
                    match t.get("unit_label").and_then(Value::as_str) {
                        Some(unit) if !unit.is_empty() => {}
                        _ => errors.push(format!(
                            "{}: record.dimensions[{idx}].unit_label must be a non-empty string",
                            path.display()
                        )),
                    }
                }
            }
        }
        errors
    }
}

// ------------------------------------------------------------
// Rollback-plan validation
// ------------------------------------------------------------

mod rollback_plan {
    use super::{Value, load, table};
    use std::collections::BTreeSet;
    use std::path::Path;

    fn trigger_kind_values(repo_root: &Path) -> Result<BTreeSet<String>, String> {
        let doc = load(&repo_root.join("profiles/agent-assurance/ontology.toml"))?;
        let mut out = BTreeSet::new();
        for block in doc
            .get("attribute_vocabularies")
            .and_then(Value::as_array)
            .map(Vec::as_slice)
            .unwrap_or(&[])
        {
            let Some(t) = block.as_table() else { continue };
            if t.get("attribute").and_then(Value::as_str) == Some("trigger_kind") {
                if let Some(values) = t.get("values").and_then(Value::as_array) {
                    out.extend(
                        values
                            .iter()
                            .filter_map(Value::as_str)
                            .map(ToString::to_string),
                    );
                }
            }
        }
        if out.is_empty() {
            Err("ontology declares no trigger_kind values".to_string())
        } else {
            Ok(out)
        }
    }

    pub fn validate(doc: &Value, repo_root: &Path) -> Vec<String> {
        let mut errors = Vec::new();
        let Ok(allowed) = trigger_kind_values(repo_root) else {
            return vec!["agent-assurance ontology could not be loaded".to_string()];
        };
        let Some(meta) = table(doc, "meta") else {
            errors.push("[meta].template_kind is None; expected 'rollback-plan'.".to_string());
            return errors;
        };
        if meta.get("template_kind").and_then(Value::as_str) != Some("rollback-plan") {
            errors.push(format!(
                "[meta].template_kind is {:?}; expected 'rollback-plan'.",
                meta.get("template_kind")
            ));
        }
        let triggers = doc.get("triggers").and_then(Value::as_array);
        match triggers.map(Vec::as_slice) {
            None | Some([]) => {
                errors.push("at least one [[triggers]] entry is required.".to_string());
                return errors;
            }
            Some(items) => {
                for (idx, trig) in items.iter().enumerate() {
                    let Some(t) = trig.as_table() else {
                        errors.push(format!("[[triggers]] #{idx}: must be a table."));
                        continue;
                    };
                    let trig_id = t.get("id").and_then(Value::as_str).unwrap_or("<unset>");
                    let kind_value = t
                        .get("trigger_kind")
                        .or_else(|| t.get("kind"))
                        .and_then(Value::as_str)
                        .unwrap_or("");
                    if kind_value.trim().is_empty() {
                        errors.push(format!(
                            "[[triggers]] #{idx} (id={trig_id:?}): missing trigger_kind/kind."
                        ));
                    } else if !allowed.contains(kind_value) {
                        errors.push(format!(
                            "[[triggers]] #{idx} (id={trig_id:?}): trigger_kind={kind_value:?} not in profile ontology vocabulary."
                        ));
                    }
                    for field in ["id", "metric", "threshold", "action"] {
                        if !t.contains_key(field) {
                            errors.push(format!(
                                "[[triggers]] #{idx} (id={trig_id:?}): missing required field '{field}'."
                            ));
                        }
                    }
                }
            }
        }
        errors
    }
}

// ------------------------------------------------------------
// SPEC §13 abstraction_class / capability_envelope validation
// ------------------------------------------------------------

mod abstraction_class {
    use super::{Value, load, table};
    use std::collections::BTreeSet;
    use std::path::Path;

    fn load_domains(repo_root: &Path) -> Result<BTreeSet<String>, String> {
        let doc = load(&repo_root.join("core/ontology.toml"))?;
        for block in doc
            .get("attribute_vocabularies")
            .and_then(Value::as_array)
            .map(Vec::as_slice)
            .unwrap_or(&[])
        {
            let Some(t) = block.as_table() else { continue };
            if t.get("attribute").and_then(Value::as_str) == Some("capability_envelope.domain") {
                let mut out = BTreeSet::new();
                if let Some(values) = t.get("values").and_then(Value::as_array) {
                    out.extend(
                        values
                            .iter()
                            .filter_map(Value::as_str)
                            .map(ToString::to_string),
                    );
                }
                if !out.is_empty() {
                    return Ok(out);
                }
            }
        }
        Err("core ontology is missing capability_envelope.domain vocabulary".to_string())
    }

    fn valid_id(value: &str) -> bool {
        let Some((slug, version)) = value.rsplit_once(".v") else {
            return false;
        };
        !slug.is_empty()
            && !version.is_empty()
            && version.chars().all(|c| c.is_ascii_digit())
            && slug.chars().all(|c| {
                c.is_ascii_lowercase() || c.is_ascii_digit() || matches!(c, '.' | '_' | '-')
            })
            && slug
                .chars()
                .next()
                .is_some_and(|c| c.is_ascii_lowercase() || c.is_ascii_digit())
    }

    fn check_ijb(t: &toml::map::Map<String, Value>, loc: &str, errors: &mut Vec<String>) {
        if t.get("ijb_primitive").and_then(Value::as_str) != Some("constraint") {
            errors.push(format!("{loc}.ijb_primitive: must be 'constraint'"));
        }
        if t.get("ijb_constraint_type").and_then(Value::as_str) != Some("structural") {
            errors.push(format!("{loc}.ijb_constraint_type: must be 'structural'"));
        }
    }

    fn check_nonneg_int(
        t: &toml::map::Map<String, Value>,
        key: &str,
        loc: &str,
        errors: &mut Vec<String>,
    ) {
        match t.get(key).and_then(Value::as_integer) {
            Some(v) if v >= 0 => {}
            _ => errors.push(format!("{loc}.{key}: must be a non-negative integer")),
        }
    }

    fn check_bool(
        t: &toml::map::Map<String, Value>,
        key: &str,
        loc: &str,
        errors: &mut Vec<String>,
    ) {
        if !t.get(key).is_some_and(Value::is_bool) {
            errors.push(format!("{loc}.{key}: must be a boolean"));
        }
    }

    fn check_string_list(
        t: &toml::map::Map<String, Value>,
        key: &str,
        loc: &str,
        errors: &mut Vec<String>,
    ) {
        match t.get(key).and_then(Value::as_array) {
            Some(arr) if arr.iter().all(Value::is_str) => {}
            _ => errors.push(format!("{loc}.{key}: must be a list of strings")),
        }
    }

    fn denied(t: &toml::map::Map<String, Value>) -> bool {
        t.get("denied").and_then(Value::as_bool) == Some(true)
    }

    fn check_domain(
        name: &str,
        t: &toml::map::Map<String, Value>,
        loc: &str,
        errors: &mut Vec<String>,
    ) {
        if denied(t) {
            return;
        }
        match name {
            "filesystem" => {
                check_string_list(t, "preopens", loc, errors);
                check_bool(t, "read_allowed", loc, errors);
                check_bool(t, "write_allowed", loc, errors);
                check_bool(t, "exec_allowed", loc, errors);
            }
            "sockets" => {
                for key in ["tcp_allowlist", "udp_allowlist"] {
                    if t.contains_key(key) && t.get(key).and_then(Value::as_bool) != Some(false) {
                        check_string_list(t, key, loc, errors);
                    }
                }
                if t.contains_key("ip_resolve_allowed") {
                    check_bool(t, "ip_resolve_allowed", loc, errors);
                }
            }
            "http" => {
                check_string_list(t, "outgoing_host_allowlist", loc, errors);
                check_nonneg_int(t, "max_concurrent_requests", loc, errors);
            }
            "clocks" => {
                check_bool(t, "wall_clock_allowed", loc, errors);
                check_bool(t, "monotonic_clock_allowed", loc, errors);
                if t.contains_key("precision_cap_ms") {
                    check_nonneg_int(t, "precision_cap_ms", loc, errors);
                }
            }
            "random" => {
                if !matches!(
                    t.get("entropy_source").and_then(Value::as_str),
                    Some("os" | "deterministic_seed" | "none")
                ) {
                    errors.push(format!(
                        "{loc}.entropy_source: must be one of ['os', 'deterministic_seed', 'none']"
                    ));
                }
            }
            "environment" => check_string_list(t, "var_allowlist", loc, errors),
            "process_spawn" => check_string_list(t, "allowed_programs", loc, errors),
            "ipc" => {
                check_bool(t, "shared_memory_allowed", loc, errors);
                check_bool(t, "fd_passing_allowed", loc, errors);
            }
            "crypto_keys" => {
                for key in ["read_keys", "use_keys"] {
                    if t.contains_key(key) {
                        check_string_list(t, key, loc, errors);
                    }
                }
                if t.contains_key("generate_allowed") {
                    check_bool(t, "generate_allowed", loc, errors);
                }
            }
            _ => {}
        }
    }

    pub fn validate(path: &Path, doc: &Value, repo_root: &Path) -> Vec<String> {
        let mut errors = Vec::new();
        let Ok(domains) = load_domains(repo_root) else {
            return vec!["core ontology could not be loaded".to_string()];
        };
        let Some(kind) = table(doc, "kind") else {
            return errors;
        };
        if let Some(ac) = kind.get("abstraction_class").and_then(Value::as_table) {
            let loc = format!("{}: [kind.abstraction_class]", path.display());
            match ac.get("id").and_then(Value::as_str) {
                Some(id) if !id.is_empty() && valid_id(id) => {}
                other => errors.push(format!(
                    "{loc}.id: must match `<slug>.v<integer>`, got {other:?}"
                )),
            }
            match ac.get("description").and_then(Value::as_str) {
                Some(desc) if !desc.is_empty() => {}
                other => errors.push(format!(
                    "{loc}.description: must be a non-empty string, got {other:?}"
                )),
            }
            check_ijb(ac, &loc, &mut errors);
        }
        if let Some(ce) = kind.get("capability_envelope").and_then(Value::as_table) {
            let loc = format!("{}: [kind.capability_envelope]", path.display());
            match ce.get("spec_version").and_then(Value::as_str) {
                Some(v) if !v.is_empty() => {}
                other => errors.push(format!(
                    "{loc}.spec_version: must be a non-empty string, got {other:?}"
                )),
            }
            check_ijb(ce, &loc, &mut errors);
            match ce.get("cpu_bounds").and_then(Value::as_table) {
                Some(cpu) => {
                    check_nonneg_int(cpu, "max_cpu_ms", &format!("{loc}.cpu_bounds"), &mut errors);
                    if cpu.contains_key("max_cpu_percent") {
                        check_nonneg_int(
                            cpu,
                            "max_cpu_percent",
                            &format!("{loc}.cpu_bounds"),
                            &mut errors,
                        );
                    } else {
                        errors.push(format!(
                            "{loc}.cpu_bounds.max_cpu_percent: must be a non-negative integer"
                        ));
                    }
                }
                None => errors.push(format!("{loc}.cpu_bounds: missing required table")),
            }
            match ce.get("memory_bounds").and_then(Value::as_table) {
                Some(mem) => check_nonneg_int(
                    mem,
                    "max_bytes",
                    &format!("{loc}.memory_bounds"),
                    &mut errors,
                ),
                None => errors.push(format!("{loc}.memory_bounds: missing required table")),
            }
            for (key, value) in ce {
                if matches!(
                    key.as_str(),
                    "cpu_bounds"
                        | "memory_bounds"
                        | "spec_version"
                        | "ijb_primitive"
                        | "ijb_constraint_type"
                ) {
                    continue;
                }
                let Some(t) = value.as_table() else {
                    errors.push(format!("{loc}.{key}: top-level value must be a sub-table"));
                    continue;
                };
                if !domains.contains(key) {
                    errors.push(format!(
                        "{loc}.{key}: not a capability domain. Closed set: {domains:?}."
                    ));
                    continue;
                }
                check_domain(key, t, &format!("{loc}.{key}"), &mut errors);
            }
        }
        errors
    }
}

// ------------------------------------------------------------
// Profile descriptor (§6.1)
// ------------------------------------------------------------

mod profile {
    use super::*;
    use std::collections::BTreeMap;

    const REQUIRED_FIELDS: &[&str] = &[
        "name",
        "namespace",
        "owner",
        "license",
        "extends",
        "ontology",
        "contained_kinds",
    ];

    // INV07 (spec.md §12.8.1): profile-pinned closure records.
    const CLOSURE_RECORD_KEYS: &[&str] = &["contained_kind", "field", "presence"];
    const CLOSURE_RECORD_PRESENCE: &[&str] = &["required", "when-present"];
    const CLOSURE_RECORD_FORBIDDEN_FIELDS: &[&str] = &["closure_root", "provenance.source_sha256"];
    const POSTURE_FIELDS: &[&str] = &["confidentiality", "license", "embargo_until"];

    /// Frozen path grammar `^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$`,
    /// hand-rolled (no regex dependency): one or more dot-separated
    /// non-empty segments of `[A-Za-z0-9_-]`.
    fn closure_record_field_ok(field: &str) -> bool {
        !field.is_empty()
            && field.split('.').all(|seg| {
                !seg.is_empty()
                    && seg
                        .chars()
                        .all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
            })
    }

    /// Union `contained_kinds` and `closure_records` across the
    /// `extends` graph rooted at `name` (spec.md §6.1 rules 3 and 4).
    /// The root resolves through `descriptors` when discovered there,
    /// falling back to the profile table of the document under
    /// validation (mirrors the Python reference, which merges CLI
    /// files into the discovery set before validating).
    fn effective_profile_sets(
        name: &str,
        local_profile: &toml::map::Map<String, Value>,
        descriptors: &BTreeMap<String, (PathBuf, Value)>,
    ) -> (BTreeSet<String>, Vec<toml::map::Map<String, Value>>) {
        let mut kinds: BTreeSet<String> = BTreeSet::new();
        let mut records: Vec<toml::map::Map<String, Value>> = Vec::new();
        let mut seen: BTreeSet<String> = BTreeSet::new();
        union_visit(
            name,
            name,
            local_profile,
            descriptors,
            &mut seen,
            &mut kinds,
            &mut records,
        );
        (kinds, records)
    }

    fn union_visit(
        node: &str,
        root: &str,
        local_profile: &toml::map::Map<String, Value>,
        descriptors: &BTreeMap<String, (PathBuf, Value)>,
        seen: &mut BTreeSet<String>,
        kinds: &mut BTreeSet<String>,
        records: &mut Vec<toml::map::Map<String, Value>>,
    ) {
        if seen.contains(node) {
            return;
        }
        let profile: &toml::map::Map<String, Value> = match descriptors.get(node) {
            Some((_, doc)) => match doc.get("profile").and_then(|p| p.as_table()) {
                Some(t) => t,
                None => return,
            },
            None if node == root => local_profile,
            None => return, // unresolved extends entry; INV03 handles it
        };
        seen.insert(node.to_string());
        if let Some(arr) = profile.get("contained_kinds").and_then(|x| x.as_array()) {
            for slug in arr {
                if let Some(s) = slug.as_str() {
                    kinds.insert(s.to_string());
                }
            }
        }
        if let Some(arr) = profile.get("closure_records").and_then(|x| x.as_array()) {
            for rec in arr {
                if let Some(t) = rec.as_table() {
                    records.push(t.clone());
                }
            }
        }
        if let Some(arr) = profile.get("extends").and_then(|x| x.as_array()) {
            for child in arr {
                if let Some(s) = child.as_str() {
                    union_visit(s, root, local_profile, descriptors, seen, kinds, records);
                }
            }
        }
    }

    /// INV07 (spec.md §12.8.1): profile-pinned closure records.
    fn check_closure_records(
        descriptor_path: &Path,
        name: &str,
        profile: &toml::map::Map<String, Value>,
        descriptors: &BTreeMap<String, (PathBuf, Value)>,
    ) -> Vec<String> {
        let mut errors: Vec<String> = Vec::new();
        let closure_records: &[Value] = match profile.get("closure_records") {
            None => &[],
            Some(v) => match v.as_array() {
                Some(a) => a.as_slice(),
                None => {
                    return vec![format!(
                        "{}: [profile].closure_records must be an array of tables (INV07)",
                        descriptor_path.display()
                    )];
                }
            },
        };

        for (index, entry) in closure_records.iter().enumerate() {
            let place = format!(
                "{}: [[profile.closure_records]] entry {}",
                descriptor_path.display(),
                index
            );
            let Some(table) = entry.as_table() else {
                errors.push(format!("{} must be a table (INV07)", place));
                continue;
            };
            let mut unknown: Vec<&str> = table
                .keys()
                .map(|k| k.as_str())
                .filter(|k| !CLOSURE_RECORD_KEYS.contains(k))
                .collect();
            unknown.sort_unstable();
            if !unknown.is_empty() {
                errors.push(format!(
                    "{} carries unknown keys {:?} (INV07: exactly contained_kind / field / presence)",
                    place, unknown
                ));
            }
            let mut bad_shape = false;
            for key in CLOSURE_RECORD_KEYS {
                let ok = table
                    .get(*key)
                    .and_then(|v| v.as_str())
                    .is_some_and(|s| !s.is_empty());
                if !ok {
                    errors.push(format!(
                        "{}.{} must be a non-empty string (INV07)",
                        place, key
                    ));
                    bad_shape = true;
                }
            }
            if bad_shape {
                continue;
            }

            let field = table.get("field").and_then(|v| v.as_str()).unwrap_or("");
            let presence = table.get("presence").and_then(|v| v.as_str()).unwrap_or("");
            if !closure_record_field_ok(field) {
                errors.push(format!(
                    "{}.field `{}` does not match the frozen path grammar ^[A-Za-z0-9_-]+(\\.[A-Za-z0-9_-]+)*$ (INV07)",
                    place, field
                ));
            } else if CLOSURE_RECORD_FORBIDDEN_FIELDS.contains(&field)
                || field.split('.').next() == Some("meta")
                || POSTURE_FIELDS.contains(&field)
            {
                errors.push(format!(
                    "{}.field `{}` is a forbidden pin target (INV07: not closure_root, not provenance.source_sha256, no meta.* path, no §12.9 posture field)",
                    place, field
                ));
            }
            if !CLOSURE_RECORD_PRESENCE.contains(&presence) {
                errors.push(format!(
                    "{}.presence `{}` must be one of {:?} (INV07)",
                    place, presence, CLOSURE_RECORD_PRESENCE
                ));
            }
        }

        let (effective_kinds, effective_records) =
            effective_profile_sets(name, profile, descriptors);

        for (index, entry) in closure_records.iter().enumerate() {
            let Some(table) = entry.as_table() else {
                continue;
            };
            if let Some(ck) = table.get("contained_kind").and_then(|v| v.as_str()) {
                if !ck.is_empty() && !effective_kinds.contains(ck) {
                    errors.push(format!(
                        "{}: [[profile.closure_records]] entry {}.contained_kind `{}` is not in the post-extends-union contained_kinds (INV07)",
                        descriptor_path.display(),
                        index,
                        ck
                    ));
                }
            }
        }

        let mut pairs: Vec<(String, String)> = Vec::new();
        for rec in &effective_records {
            if let (Some(ck), Some(fld)) = (
                rec.get("contained_kind").and_then(|v| v.as_str()),
                rec.get("field").and_then(|v| v.as_str()),
            ) {
                pairs.push((ck.to_string(), fld.to_string()));
            }
        }
        let mut duplicates: BTreeSet<(String, String)> = BTreeSet::new();
        for pair in &pairs {
            if pairs.iter().filter(|p| *p == pair).count() > 1 {
                duplicates.insert(pair.clone());
            }
        }
        for (ck, fld) in duplicates {
            errors.push(format!(
                "{}: duplicate closure-record pin (`{}`, `{}`) after the extends union (INV07)",
                descriptor_path.display(),
                ck,
                fld
            ));
        }

        errors
    }

    /// Discover profile descriptors; also report duplicate profile
    /// names. A duplicate would let one descriptor shadow another in
    /// the name-keyed map and silently erase its closure pins, so the
    /// caller MUST refuse to validate anything when duplicates exist
    /// (SPEC 12.8.1 pin resolution: no pin-free fall-through).
    pub fn discover(repo_root: &Path) -> (BTreeMap<String, (PathBuf, Value)>, Vec<String>) {
        let mut duplicates: Vec<String> = Vec::new();
        let mut out: BTreeMap<String, (PathBuf, Value)> = BTreeMap::new();
        let dir = repo_root.join("profiles");
        let Ok(entries) = std::fs::read_dir(&dir) else {
            return (out, duplicates);
        };
        for entry in entries.flatten() {
            let candidate = entry.path().join("PROFILE.toml");
            if !candidate.is_file() {
                continue;
            }
            let Ok(doc) = load(&candidate) else { continue };
            let tk = doc
                .get("meta")
                .and_then(|m| m.get("template_kind"))
                .and_then(|x| x.as_str())
                .unwrap_or("");
            if tk != "profile-descriptor" {
                continue;
            }
            if let Some(name) = doc
                .get("profile")
                .and_then(|p| p.get("name"))
                .and_then(|x| x.as_str())
            {
                if let Some((existing, _)) = out.get(name) {
                    duplicates.push(format!(
                        "duplicate profile-descriptor name `{}` ({} and {})",
                        name,
                        existing.display(),
                        candidate.display()
                    ));
                    continue;
                }
                out.insert(name.to_string(), (candidate, doc));
            }
        }
        (out, duplicates)
    }

    fn is_unprefixed(name: &str) -> bool {
        let mut chars = name.chars();
        let Some(first) = chars.next() else {
            return false;
        };
        if !(first.is_ascii_lowercase()) {
            return false;
        }
        chars.all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-')
    }

    fn is_reverse_dns(name: &str) -> bool {
        if !name.contains('.') {
            return false;
        }
        let parts: Vec<&str> = name.split('.').collect();
        parts.iter().all(|p| !p.is_empty() && is_unprefixed(p))
    }

    pub fn check_namespace_partition(name: &str, namespace: &str) -> Vec<String> {
        let mut errors = Vec::new();
        let u = is_unprefixed(name);
        let r = is_reverse_dns(name);
        if !(u || r) {
            errors.push(format!(
                "[profile].name `{}` does not match the SPEC §2.5 namespacing partition",
                name
            ));
            return errors;
        }
        if u {
            if namespace != "spec.reserved" {
                errors.push(format!(
                    "[profile].namespace `{}` is inconsistent with unprefixed name `{}` (SPEC §2.5 requires `namespace = \"spec.reserved\"`)",
                    namespace, name
                ));
            }
        } else if namespace == "spec.reserved" {
            errors.push(format!(
                "[profile].namespace = \"spec.reserved\" is not permitted for reverse-DNS name `{}`",
                name
            ));
        } else {
            let prefix = format!("{}.", namespace);
            if !name.starts_with(&prefix) {
                errors.push(format!(
                    "[profile].namespace `{}` is not a strict reverse-DNS prefix of name `{}` (SPEC §2.5)",
                    namespace, name
                ));
            }
        }
        errors
    }

    pub fn check_extends_acyclic(
        name: &str,
        descriptors: &BTreeMap<String, (PathBuf, Value)>,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        let mut path: Vec<String> = Vec::new();
        let mut visited: BTreeSet<String> = BTreeSet::new();
        visit(name, descriptors, &mut path, &mut visited, &mut errors);
        errors
    }

    fn visit(
        node: &str,
        descriptors: &BTreeMap<String, (PathBuf, Value)>,
        path: &mut Vec<String>,
        visited: &mut BTreeSet<String>,
        errors: &mut Vec<String>,
    ) {
        if let Some(pos) = path.iter().position(|n| n == node) {
            let mut cycle: Vec<String> = path[pos..].to_vec();
            cycle.push(node.to_string());
            errors.push(format!(
                "`extends` graph contains a cycle: {}",
                cycle.join(" -> ")
            ));
            return;
        }
        if visited.contains(node) {
            return;
        }
        visited.insert(node.to_string());
        let Some((_, doc)) = descriptors.get(node) else {
            return; // INV03 handled separately
        };
        let Some(arr) = doc
            .get("profile")
            .and_then(|p| p.get("extends"))
            .and_then(|x| x.as_array())
        else {
            return;
        };
        path.push(node.to_string());
        for child in arr {
            if let Some(s) = child.as_str() {
                visit(s, descriptors, path, visited, errors);
            }
        }
        path.pop();
    }

    fn kind_descriptor_candidates(
        repo_root: &Path,
        slug: &str,
        profile_name: &str,
    ) -> Vec<PathBuf> {
        let fname = format!("{}-kind.toml", slug);
        let mut out: Vec<PathBuf> = vec![
            repo_root.join("profiles").join(profile_name).join(&fname),
            repo_root.join("core").join(&fname),
        ];
        if let Ok(entries) = std::fs::read_dir(repo_root.join("profiles")) {
            for entry in entries.flatten() {
                // Path::is_dir follows symlinks (DirEntry::file_type does
                // not), matching the Python candidate enumeration.
                if entry.path().is_dir() {
                    out.push(entry.path().join(&fname));
                }
            }
        }
        // dedupe preserving order
        let mut seen: BTreeSet<PathBuf> = BTreeSet::new();
        let mut deduped = Vec::with_capacity(out.len());
        for p in out {
            let key = p.clone();
            if seen.insert(key) {
                deduped.push(p);
            }
        }
        deduped
    }

    pub fn validate_one(
        descriptor_path: &Path,
        doc: &Value,
        repo_root: &Path,
        descriptors: &BTreeMap<String, (PathBuf, Value)>,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        let meta = match doc.get("meta").and_then(|x| x.as_table()) {
            Some(t) => t,
            None => {
                errors.push(format!(
                    "{}: missing required `[meta]` table",
                    descriptor_path.display()
                ));
                return errors;
            }
        };
        match meta.get("template_kind").and_then(|x| x.as_str()) {
            Some("profile-descriptor") => {}
            other => {
                errors.push(format!(
                    "{}: meta.template_kind must equal `\"profile-descriptor\"` (got {:?})",
                    descriptor_path.display(),
                    other
                ));
                return errors;
            }
        }

        let profile = match doc.get("profile").and_then(|x| x.as_table()) {
            Some(t) => t,
            None => {
                errors.push(format!(
                    "{}: missing required `[profile]` table",
                    descriptor_path.display()
                ));
                return errors;
            }
        };

        for field in REQUIRED_FIELDS {
            if !profile.contains_key(*field) {
                errors.push(format!(
                    "{}: [profile].{} is required",
                    descriptor_path.display(),
                    field
                ));
            }
        }
        if !errors.is_empty() {
            return errors;
        }

        let name = profile
            .get("name")
            .and_then(|v| v.as_str())
            .unwrap_or_default();
        let namespace = profile
            .get("namespace")
            .and_then(|v| v.as_str())
            .unwrap_or_default();

        if name.is_empty() {
            errors.push(format!(
                "{}: [profile].name must be a non-empty string",
                descriptor_path.display()
            ));
        }
        if namespace.is_empty() {
            errors.push(format!(
                "{}: [profile].namespace must be a non-empty string",
                descriptor_path.display()
            ));
        }

        // INV01
        errors.extend(check_namespace_partition(name, namespace));

        // INV02
        errors.extend(check_extends_acyclic(name, descriptors));

        // INV03
        if let Some(arr) = profile.get("extends").and_then(|x| x.as_array()) {
            for entry in arr {
                let Some(s) = entry.as_str() else {
                    errors.push(format!(
                        "{}: [profile].extends entries must be strings",
                        descriptor_path.display()
                    ));
                    continue;
                };
                if !descriptors.contains_key(s) {
                    errors.push(format!(
                        "{}: [profile].extends entry `{}` does not resolve to a loaded profile-descriptor",
                        descriptor_path.display(),
                        s
                    ));
                }
            }
        }

        // INV04
        if let Some(ontology_rel) = profile.get("ontology").and_then(|x| x.as_str()) {
            let ontology_path = repo_root.join(ontology_rel);
            if !ontology_path.is_file() {
                errors.push(format!(
                    "{}: [profile].ontology path does not resolve to a file ({})",
                    descriptor_path.display(),
                    ontology_path.display()
                ));
            } else {
                match load(&ontology_path) {
                    Ok(ont) => {
                        let tk = ont
                            .get("meta")
                            .and_then(|m| m.get("template_kind"))
                            .and_then(|x| x.as_str())
                            .unwrap_or("");
                        if tk != "ontology" {
                            errors.push(format!(
                                "{}: [profile].ontology ({}) does not declare `template_kind = \"ontology\"`",
                                descriptor_path.display(),
                                ontology_rel
                            ));
                        }
                    }
                    Err(e) => errors.push(format!(
                        "{}: ontology parse failure: {}",
                        descriptor_path.display(),
                        e
                    )),
                }
            }
        }

        // INV05
        if let Some(arr) = profile.get("contained_kinds").and_then(|x| x.as_array()) {
            for entry in arr {
                let Some(slug) = entry.as_str().filter(|s| !s.is_empty()) else {
                    errors.push(format!(
                        "{}: [profile].contained_kinds entries must be non-empty strings",
                        descriptor_path.display()
                    ));
                    continue;
                };
                let candidates = kind_descriptor_candidates(repo_root, slug, name);
                let mut matched = false;
                for c in &candidates {
                    if !c.is_file() {
                        continue;
                    }
                    if let Ok(kd) = load(c) {
                        let m = kd.get("meta").and_then(|x| x.as_table());
                        let tk = m
                            .and_then(|t| t.get("template_kind"))
                            .and_then(|x| x.as_str())
                            .unwrap_or("");
                        let dk = m
                            .and_then(|t| t.get("describes_kind"))
                            .and_then(|x| x.as_str())
                            .unwrap_or("");
                        if tk == "kind-descriptor" && dk == slug {
                            matched = true;
                            break;
                        }
                    }
                }
                if !matched {
                    errors.push(format!(
                        "{}: [profile].contained_kinds entry `{}` does not resolve to a *-kind.toml with matching describes_kind",
                        descriptor_path.display(),
                        slug
                    ));
                }
            }
        }

        // INV07: profile-pinned closure records (spec.md §12.8.1)
        errors.extend(check_closure_records(
            descriptor_path,
            name,
            profile,
            descriptors,
        ));

        errors
    }
}

// ------------------------------------------------------------
// Disclosure profile (3 kinds)
// ------------------------------------------------------------

mod disclosure {
    use super::*;

    fn load_vocabs(repo_root: &Path) -> BTreeMap<String, (Vec<String>, bool)> {
        let mut out = BTreeMap::new();
        let path = repo_root.join("profiles/disclosure/ontology.toml");
        let Ok(doc) = super::load(&path) else {
            return out;
        };
        let Some(arr) = doc.get("attribute_vocabularies").and_then(|x| x.as_array()) else {
            return out;
        };
        for entry in arr {
            let Some(t) = entry.as_table() else { continue };
            let Some(attr) = t.get("attribute").and_then(|x| x.as_str()) else {
                continue;
            };
            let values: Vec<String> = t
                .get("values")
                .and_then(|x| x.as_array())
                .map(|a| {
                    a.iter()
                        .filter_map(|v| v.as_str().map(str::to_string))
                        .collect()
                })
                .unwrap_or_default();
            let extensible = t
                .get("extensible")
                .and_then(|x| x.as_bool())
                .unwrap_or(false);
            out.insert(attr.to_string(), (values, extensible));
        }
        out
    }

    fn check_vocab(
        attribute: &str,
        value: Option<&str>,
        vocabs: &BTreeMap<String, (Vec<String>, bool)>,
        location: &str,
    ) -> Vec<String> {
        let Some((values, extensible)) = vocabs.get(attribute) else {
            return vec![format!(
                "{}: ontology missing attribute_vocabulary `{}` (cannot enforce closure)",
                location, attribute
            )];
        };
        let Some(v) = value else {
            return vec![format!("{}: `{}` must be a string", location, attribute)];
        };
        if values.iter().any(|x| x == v) {
            return Vec::new();
        }
        if *extensible {
            return Vec::new();
        }
        vec![format!(
            "{}: `{} = \"{}\"` is not in the closed vocabulary {:?}",
            location, attribute, v, values
        )]
    }

    pub fn validate(path: &Path, doc: &Value, repo_root: &Path) -> Vec<String> {
        let vocabs = load_vocabs(repo_root);
        let meta = match doc.get("meta").and_then(|x| x.as_table()) {
            Some(t) => t,
            None => return vec![format!("{}: missing [meta]", path.display())],
        };
        let tk = meta
            .get("template_kind")
            .and_then(|x| x.as_str())
            .unwrap_or("");
        match tk {
            "disclosure-attestation" => validate_attestation(path, doc, meta, &vocabs),
            "redaction-manifest" => validate_redaction(path, doc, &vocabs),
            "selective-disclosure-proof" => validate_proof(path, doc, &vocabs),
            other => vec![format!(
                "{}: template_kind `{}` is not a disclosure-profile kind",
                path.display(),
                other
            )],
        }
    }

    fn validate_attestation(
        path: &Path,
        doc: &Value,
        meta: &toml::value::Table,
        vocabs: &BTreeMap<String, (Vec<String>, bool)>,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        let embargo = meta.get("embargo_until").and_then(|x| x.as_str());
        let Some(arr) = doc.get("attestations").and_then(|x| x.as_array()) else {
            return vec![format!(
                "{}: at least one `[[attestations]]` entry required",
                path.display()
            )];
        };
        for (i, entry) in arr.iter().enumerate() {
            let Some(t) = entry.as_table() else {
                errors.push(format!(
                    "{}:attestations[{}]: must be a table",
                    path.display(),
                    i
                ));
                continue;
            };
            let loc = format!("{}:attestations[{}]", path.display(), i);
            let id = t.get("id").and_then(|x| x.as_str()).unwrap_or("");
            if !id.starts_with("DISC:") {
                errors.push(format!("{}: `id` must start with `DISC:`", loc));
            }
            let posture = t.get("disclosure_posture").and_then(|x| x.as_str());
            errors.extend(check_vocab(
                "disclosure_posture",
                posture,
                vocabs,
                &format!("{}.disclosure_posture", loc),
            ));
            if posture == Some("partial") {
                let covered_ok = t
                    .get("covered_by")
                    .and_then(|x| x.as_array())
                    .map(|a| {
                        a.iter()
                            .any(|v| v.as_str().is_some_and(|s| s.starts_with("RED:")))
                    })
                    .unwrap_or(false);
                if !covered_ok {
                    errors.push(format!(
                        "{}: `disclosure_posture = \"partial\"` requires at least one `covered_by` entry referencing a `RED:` id",
                        loc
                    ));
                }
            }
            if posture == Some("embargoed") && embargo.is_none() {
                errors.push(format!(
                    "{}: `disclosure_posture = \"embargoed\"` requires `[meta].embargo_until` (SPEC §2.7)",
                    loc
                ));
            }
        }
        errors
    }

    fn validate_redaction(
        path: &Path,
        doc: &Value,
        vocabs: &BTreeMap<String, (Vec<String>, bool)>,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        let Some(arr) = doc.get("redactions").and_then(|x| x.as_array()) else {
            return vec![format!(
                "{}: at least one `[[redactions]]` entry required",
                path.display()
            )];
        };
        for (i, entry) in arr.iter().enumerate() {
            let Some(t) = entry.as_table() else {
                errors.push(format!(
                    "{}:redactions[{}]: must be a table",
                    path.display(),
                    i
                ));
                continue;
            };
            let loc = format!("{}:redactions[{}]", path.display(), i);
            let id = t.get("id").and_then(|x| x.as_str()).unwrap_or("");
            if !id.starts_with("RED:") {
                errors.push(format!("{}: `id` must start with `RED:`", loc));
            }
            let method = t.get("redaction_method").and_then(|x| x.as_str());
            errors.extend(check_vocab(
                "redaction_method",
                method,
                vocabs,
                &format!("{}.redaction_method", loc),
            ));
            let reason = t.get("redaction_reason").and_then(|x| x.as_str());
            errors.extend(check_vocab(
                "redaction_reason",
                reason,
                vocabs,
                &format!("{}.redaction_reason", loc),
            ));
            if reason == Some("other") {
                let notes = t.get("notes").and_then(|x| x.as_str()).unwrap_or("");
                if notes.trim().is_empty() {
                    errors.push(format!(
                        "{}: `redaction_reason = \"other\"` requires a non-empty `notes` field",
                        loc
                    ));
                }
            }
        }
        errors
    }

    fn validate_proof(
        path: &Path,
        doc: &Value,
        vocabs: &BTreeMap<String, (Vec<String>, bool)>,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        let Some(arr) = doc.get("proofs").and_then(|x| x.as_array()) else {
            return vec![format!(
                "{}: at least one `[[proofs]]` entry required",
                path.display()
            )];
        };
        for (i, entry) in arr.iter().enumerate() {
            let Some(t) = entry.as_table() else {
                errors.push(format!("{}:proofs[{}]: must be a table", path.display(), i));
                continue;
            };
            let loc = format!("{}:proofs[{}]", path.display(), i);
            let id = t.get("id").and_then(|x| x.as_str()).unwrap_or("");
            if !id.starts_with("SDP:") {
                errors.push(format!("{}: `id` must start with `SDP:`", loc));
            }
            let bound = t.get("bound_source").and_then(|x| x.as_str()).unwrap_or("");
            if !is_sha256_hex(bound) {
                errors.push(format!(
                    "{}: `bound_source` must match `^sha256:[0-9a-f]{{64}}$` (got {:?})",
                    loc, bound
                ));
            }
            let scheme = t.get("proof_scheme").and_then(|x| x.as_str());
            errors.extend(check_vocab(
                "proof_scheme",
                scheme,
                vocabs,
                &format!("{}.proof_scheme", loc),
            ));
            if let Some(covers) = t.get("covers").and_then(|x| x.as_array()) {
                for (ci, c) in covers.iter().enumerate() {
                    let Some(s) = c.as_str() else {
                        errors.push(format!("{}.covers[{}]: must be a string", loc, ci));
                        continue;
                    };
                    if !s.starts_with("RED:") {
                        errors.push(format!(
                            "{}.covers[{}]: every entry must start with `RED:` (got {:?})",
                            loc, ci, s
                        ));
                    }
                }
            }
        }
        errors
    }

    fn is_sha256_hex(s: &str) -> bool {
        let Some(rest) = s.strip_prefix("sha256:") else {
            return false;
        };
        rest.len() == 64
            && rest
                .chars()
                .all(|c| c.is_ascii_hexdigit() && !c.is_ascii_uppercase())
    }
}

// ------------------------------------------------------------
// Gate-decision profile (agent-assurance gate-decision-kind)
// Enforces INV01..INV06 from
// profiles/agent-assurance/gate-decision-kind.toml. The load-bearing
// invariant is INV06: when decision.subject_class = "self-modification",
// the deciding model's provider_id AND model_family_id MUST both differ
// from the proposing model's (conjunctive AND).
//
// Mirrors validators/validate_gate_decision.py (Python reference).
// CI runs both; divergence is a build break.
// ------------------------------------------------------------

mod gate_decision {
    use super::*;

    fn load_vocab(repo_root: &Path, attribute: &str) -> Option<Vec<String>> {
        let path = repo_root.join("profiles/agent-assurance/ontology.toml");
        let doc = super::load(&path).ok()?;
        let arr = doc.get("attribute_vocabularies")?.as_array()?;
        for entry in arr {
            let t = entry.as_table()?;
            if t.get("attribute")?.as_str()? == attribute {
                let values: Vec<String> = t
                    .get("values")?
                    .as_array()?
                    .iter()
                    .filter_map(|v| v.as_str().map(str::to_string))
                    .collect();
                return Some(values);
            }
        }
        None
    }

    fn is_hex64(s: &str) -> bool {
        s.len() == 64 && s.chars().all(|c| c.is_ascii_hexdigit())
    }

    fn matches_assertion_id(s: &str) -> bool {
        // ^A-[A-Za-z0-9][A-Za-z0-9_-]*$
        let bytes = s.as_bytes();
        if bytes.len() < 3 || &bytes[0..2] != b"A-" {
            return false;
        }
        if !(bytes[2].is_ascii_alphanumeric()) {
            return false;
        }
        bytes[3..]
            .iter()
            .all(|&b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
    }

    fn matches_observed_line(s: &str) -> bool {
        // Loose check: '<assertion-id> = observed(<non-empty arg-list>)'.
        // Full ABNF validation is RUNTIME-SPEC.
        let trimmed = s.trim();
        let Some(eq_pos) = trimmed.find('=') else {
            return false;
        };
        let id_part = trimmed[..eq_pos].trim();
        let rhs = trimmed[eq_pos + 1..].trim();
        matches_assertion_id(id_part)
            && rhs.starts_with("observed(")
            && rhs.ends_with(')')
            && rhs.len() > "observed()".len()
    }

    pub fn validate(path: &Path, doc: &Value, repo_root: &Path) -> Vec<String> {
        let mut defects = Vec::new();
        let location = path.display();

        let meta = match doc.get("meta").and_then(|x| x.as_table()) {
            Some(t) => t,
            None => return vec![format!("{}: missing [meta]", location)],
        };
        let tk = meta
            .get("template_kind")
            .and_then(|x| x.as_str())
            .unwrap_or("");
        if tk != "gate-decision" {
            return vec![format!(
                "{}: template_kind = {:?} (expected 'gate-decision')",
                location, tk
            )];
        }
        let fp = meta
            .get("framework_profile")
            .and_then(|x| x.as_str())
            .unwrap_or("");
        if fp != "agent-assurance" {
            defects.push(format!(
                "{}: meta.framework_profile = {:?} (expected 'agent-assurance')",
                location, fp
            ));
        }

        let decision = match doc.get("decision").and_then(|x| x.as_table()) {
            Some(t) => t,
            None => return vec![format!("{}: missing or non-table [decision]", location)],
        };

        let verdict = decision.get("verdict").and_then(|x| x.as_str());
        let failed_refs = decision
            .get("failed_constraint_refs")
            .and_then(|x| x.as_array())
            .cloned()
            .unwrap_or_default();

        // INV01: verdict == "pass" iff failed_constraint_refs is empty.
        let is_pass = verdict == Some("pass");
        let is_empty = failed_refs.is_empty();
        if is_pass != is_empty {
            defects.push(format!(
                "{}: INV01 violated: decision.verdict = {:?} but failed_constraint_refs has {} entries",
                location,
                verdict.unwrap_or("(missing)"),
                failed_refs.len()
            ));
        }

        // INV02: every failed_constraint_refs[].constraint_id matches assertion-id syntax.
        for (i, ref_v) in failed_refs.iter().enumerate() {
            let Some(t) = ref_v.as_table() else {
                defects.push(format!(
                    "{}: INV02 violated: failed_constraint_refs[{}] is not a table",
                    location, i
                ));
                continue;
            };
            let cid = t
                .get("constraint_id")
                .and_then(|x| x.as_str())
                .unwrap_or("");
            if !matches_assertion_id(cid) {
                defects.push(format!(
                    "{}: INV02 violated: failed_constraint_refs[{}].constraint_id = {:?} does not match ^A-[A-Za-z0-9][A-Za-z0-9_-]*$",
                    location, i, cid
                ));
            }
        }

        // INV03: every override_refs[].observation_line parses observed(...).
        let overrides = decision
            .get("override_refs")
            .and_then(|x| x.as_array())
            .cloned()
            .unwrap_or_default();
        for (i, ovr) in overrides.iter().enumerate() {
            let Some(t) = ovr.as_table() else {
                defects.push(format!(
                    "{}: INV03 violated: override_refs[{}] is not a table",
                    location, i
                ));
                continue;
            };
            let line = t
                .get("observation_line")
                .and_then(|x| x.as_str())
                .unwrap_or("");
            if !matches_observed_line(line) {
                defects.push(format!(
                    "{}: INV03 violated: override_refs[{}].observation_line does not match canonical observed(...) shape: {:?}",
                    location, i, line
                ));
            }
        }

        // INV04: evidence_root == 64 hex chars.
        let er = decision
            .get("evidence_root")
            .and_then(|x| x.as_str())
            .unwrap_or("");
        if !is_hex64(er) {
            defects.push(format!(
                "{}: INV04 violated: decision.evidence_root = {:?} does not match ^[0-9a-f]{{64}}$",
                location, er
            ));
        }

        // INV06: subject_class vocabulary + self-modification AND predicate.
        let subject_class = decision.get("subject_class").and_then(|x| x.as_str());
        if let Some(sc) = subject_class {
            let vocab = load_vocab(repo_root, "subject_class");
            if let Some(v) = &vocab {
                if !v.iter().any(|x| x == sc) {
                    defects.push(format!(
                        "{}: INV06 violated: decision.subject_class = {:?} not in subject_class vocabulary {:?}",
                        location, sc, v
                    ));
                }
            } else {
                defects.push(format!(
                    "{}: INV06 vocab load failed (subject_class vocabulary missing from agent-assurance ontology)",
                    location
                ));
            }
        }

        if subject_class == Some("self-modification") {
            let required = [
                "proposing_provider_id",
                "proposing_model_family_id",
                "deciding_provider_id",
                "deciding_model_family_id",
            ];
            let missing: Vec<&str> = required
                .iter()
                .filter(|k| {
                    decision
                        .get(**k)
                        .and_then(|x| x.as_str())
                        .map(|s| s.is_empty())
                        .unwrap_or(true)
                })
                .copied()
                .collect();
            if !missing.is_empty() {
                defects.push(format!(
                    "{}: INV06 violated: subject_class = 'self-modification' requires all four of {:?}; missing or empty: {:?}",
                    location, required, missing
                ));
            }

            let provider_vocab = load_vocab(repo_root, "provider_id");
            let family_vocab = load_vocab(repo_root, "model_family_id");

            let prop_p = decision
                .get("proposing_provider_id")
                .and_then(|x| x.as_str());
            let prop_f = decision
                .get("proposing_model_family_id")
                .and_then(|x| x.as_str());
            let dec_p = decision
                .get("deciding_provider_id")
                .and_then(|x| x.as_str());
            let dec_f = decision
                .get("deciding_model_family_id")
                .and_then(|x| x.as_str());

            for (label, value, vocab) in [
                ("proposing_provider_id", prop_p, &provider_vocab),
                ("deciding_provider_id", dec_p, &provider_vocab),
                ("proposing_model_family_id", prop_f, &family_vocab),
                ("deciding_model_family_id", dec_f, &family_vocab),
            ] {
                if let (Some(v), Some(values)) = (value.filter(|s| !s.is_empty()), vocab) {
                    if !values.iter().any(|x| x == v) {
                        defects.push(format!(
                            "{}: INV06 violated: decision.{} = {:?} not in vocabulary {:?}",
                            location, label, v, values
                        ));
                    }
                }
            }

            // Conjunctive AND: both inequalities must hold.
            if let (Some(pp), Some(pf), Some(dp), Some(df)) = (
                prop_p.filter(|s| !s.is_empty()),
                prop_f.filter(|s| !s.is_empty()),
                dec_p.filter(|s| !s.is_empty()),
                dec_f.filter(|s| !s.is_empty()),
            ) {
                let same_provider = dp == pp;
                let same_family = df == pf;
                if same_provider || same_family {
                    let mut problem = Vec::new();
                    if same_provider {
                        problem.push(format!(
                            "deciding_provider_id ({:?}) == proposing_provider_id ({:?})",
                            dp, pp
                        ));
                    }
                    if same_family {
                        problem.push(format!(
                            "deciding_model_family_id ({:?}) == proposing_model_family_id ({:?})",
                            df, pf
                        ));
                    }
                    defects.push(format!(
                        "{}: INV06 violated (conjunctive AND): {}. INV06 requires BOTH deciding_provider_id != proposing_provider_id AND deciding_model_family_id != proposing_model_family_id. Same-provider/different-family and different-provider/same-family BOTH fail INV06.",
                        location,
                        problem.join(" AND ")
                    ));
                }
            }
        }

        defects
    }
}

// ------------------------------------------------------------
// Meta-field checks (§2.2 + §2.6 + §2.7) — applied to every doc with [meta]
// ------------------------------------------------------------

const CONFIDENTIALITY: &[&str] = &[
    "public",
    "restricted",
    "confidential",
    "trade-secret",
    "embargoed",
];

fn validate_meta_fields(path: &Path, doc: &Value) -> Vec<String> {
    let mut errors = Vec::new();
    let Some(meta) = doc.get("meta").and_then(|x| x.as_table()) else {
        return errors;
    };

    match meta.get("schema_version").and_then(|x| x.as_str()) {
        Some(v) if is_semver(v) => {}
        _ => errors.push(format!(
            "{}: [meta].schema_version must be a semver string `MAJOR.MINOR.PATCH`",
            path.display()
        )),
    }

    if let Some(raw) = meta.get("ontology_version") {
        match raw.as_integer() {
            Some(v) if v > 0 => {}
            _ => errors.push(format!(
                "{}: [meta].ontology_version must be a positive integer snapshot",
                path.display()
            )),
        }
    }

    if let Some(docs_url) = meta.get("docs").and_then(|x| x.as_str()) {
        // §2.6 — https only, no query string
        if !docs_url.starts_with("https://") {
            errors.push(format!(
                "{}: [meta].docs must start with `https://` (SPEC §2.6)",
                path.display()
            ));
        }
        if let Some(after_path) = docs_url.split_once('#').map(|p| p.0).or(Some(docs_url)) {
            if after_path.contains('?') {
                errors.push(format!(
                    "{}: [meta].docs must not contain a query string (SPEC §2.6)",
                    path.display()
                ));
            }
        }
    }

    if let Some(c_raw) = meta.get("confidentiality") {
        let Some(c) = c_raw.as_str() else {
            errors.push(format!(
                "{}: [meta].confidentiality, when present, must be a string (SPEC §2.7)",
                path.display()
            ));
            // Fall through so the closed-set + cross-field rules don't
            // shadow the type error.
            return errors;
        };
        if !CONFIDENTIALITY.contains(&c) {
            errors.push(format!(
                "{}: [meta].confidentiality = `{}` is not in the closed set {:?} (SPEC §2.7)",
                path.display(),
                c,
                CONFIDENTIALITY
            ));
        }
        if c == "embargoed" {
            let until = meta.get("embargo_until").and_then(|x| x.as_str());
            match until {
                None => errors.push(format!(
                    "{}: [meta].confidentiality = \"embargoed\" REQUIRES [meta].embargo_until (SPEC §2.7)",
                    path.display()
                )),
                Some(v) if !is_rfc3339_date_or_datetime(v) => errors.push(format!(
                    "{}: [meta].embargo_until = `{}` does not match RFC 3339 date or date-time syntax (SPEC §2.7)",
                    path.display(), v
                )),
                _ => {}
            }
        } else if let Some(v) = meta.get("embargo_until").and_then(|x| x.as_str()) {
            // embargo_until is informational when confidentiality is
            // not "embargoed", but its syntax MUST still match RFC 3339
            // so the field doesn't become a free-form trap.
            if !is_rfc3339_date_or_datetime(v) {
                errors.push(format!(
                    "{}: [meta].embargo_until = `{}` does not match RFC 3339 date or date-time syntax (SPEC §2.7)",
                    path.display(), v
                ));
            }
        }
    }

    if let Some(lic_raw) = meta.get("license") {
        match lic_raw.as_str() {
            None => errors.push(format!(
                "{}: [meta].license, when present, must be a string (SPEC §2.7)",
                path.display()
            )),
            Some(s) if s.trim().is_empty() => errors.push(format!(
                "{}: [meta].license, when present, must be a non-empty string",
                path.display()
            )),
            _ => {}
        }
    }

    errors
}

// SPEC §2.7 — accept either:
//   YYYY-MM-DD                                (full-date)
//   YYYY-MM-DDTHH:MM:SS[.fff][Z|±HH:MM]       (full date-time)
// The check is syntactic only; the validator does NOT compare against
// wall-clock time per SPEC §2.7.
fn is_rfc3339_date_or_datetime(s: &str) -> bool {
    let bytes = s.as_bytes();
    // YYYY-MM-DD prefix is mandatory.
    if bytes.len() < 10 {
        return false;
    }
    let date_ok = bytes[0..4].iter().all(|b| b.is_ascii_digit())
        && bytes[4] == b'-'
        && bytes[5..7].iter().all(|b| b.is_ascii_digit())
        && bytes[7] == b'-'
        && bytes[8..10].iter().all(|b| b.is_ascii_digit());
    if !date_ok {
        return false;
    }
    if bytes.len() == 10 {
        return true;
    }
    // Datetime separator: T or t.
    if !(bytes[10] == b'T' || bytes[10] == b't') {
        return false;
    }
    // HH:MM:SS
    if bytes.len() < 19 {
        return false;
    }
    let time_ok = bytes[11..13].iter().all(|b| b.is_ascii_digit())
        && bytes[13] == b':'
        && bytes[14..16].iter().all(|b| b.is_ascii_digit())
        && bytes[16] == b':'
        && bytes[17..19].iter().all(|b| b.is_ascii_digit());
    if !time_ok {
        return false;
    }
    let mut idx = 19;
    // Optional fractional seconds.
    if idx < bytes.len() && bytes[idx] == b'.' {
        idx += 1;
        let start = idx;
        while idx < bytes.len() && bytes[idx].is_ascii_digit() {
            idx += 1;
        }
        if idx == start {
            return false;
        }
    }
    if idx >= bytes.len() {
        return false;
    }
    // Offset: Z|z, +HH:MM, -HH:MM.
    let off = &bytes[idx..];
    match off {
        [b'Z'] | [b'z'] => true,
        [sign, h1, h2, b':', m1, m2]
            if (*sign == b'+' || *sign == b'-')
                && h1.is_ascii_digit()
                && h2.is_ascii_digit()
                && m1.is_ascii_digit()
                && m2.is_ascii_digit() =>
        {
            true
        }
        _ => false,
    }
}

// ------------------------------------------------------------
// Provenance encryption sub-table (§11.1)
// ------------------------------------------------------------

const HASH_IS_OVER: &[&str] = &["plaintext", "ciphertext"];

fn validate_provenance_encryption(path: &Path, doc: &Value) -> Vec<String> {
    let mut errors = Vec::new();
    let Some(prov) = doc.get("provenance").and_then(|x| x.as_table()) else {
        return errors;
    };
    let Some(enc) = prov.get("encryption").and_then(|x| x.as_table()) else {
        return errors;
    };
    match enc.get("sealed").and_then(|x| x.as_bool()) {
        Some(true) => {}
        Some(false) => errors.push(format!(
            "{}: [provenance.encryption] is present but `sealed = false` — SPEC §11.1 requires the sub-table to be absent in that case",
            path.display()
        )),
        None => errors.push(format!(
            "{}: [provenance.encryption].sealed is required (boolean) when the sub-table is present",
            path.display()
        )),
    }
    match enc.get("hash_is_over").and_then(|x| x.as_str()) {
        Some(v) if HASH_IS_OVER.contains(&v) => {}
        Some(other) => errors.push(format!(
            "{}: [provenance.encryption].hash_is_over = `{}` is not in {:?}",
            path.display(),
            other,
            HASH_IS_OVER
        )),
        None => errors.push(format!(
            "{}: [provenance.encryption].hash_is_over is required (SPEC §11.1)",
            path.display()
        )),
    }
    // SPEC §11.1 — `scheme_hint` is OPTIONAL but, when present, MUST
    // be a string (free-form label).
    if let Some(v) = enc.get("scheme_hint") {
        if v.as_str().is_none() {
            errors.push(format!(
                "{}: [provenance.encryption].scheme_hint, when present, must be a string (SPEC §11.1)",
                path.display()
            ));
        }
    }
    errors
}

// ------------------------------------------------------------
// §12.8 closure_root source-hash subset
// ------------------------------------------------------------

const EMPTY_SHA256: &str =
    "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
const EMPTY_SHA384: &str = "sha384:38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da274edebfe76f65fbd51ad2f14898b95b";
const EMPTY_SHA512: &str = "sha512:cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e";

fn is_lower_hex(s: &str) -> bool {
    s.bytes()
        .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

fn split_closure_root(value: &str) -> Result<(&str, &str), String> {
    let Some((algo, hex)) = value.split_once(':') else {
        return Err("`closure_root` must match `<algo>:<lowercase-hex-digest>`".to_string());
    };
    let expected_len = match algo {
        "sha256" => 64,
        "sha384" => 96,
        "sha512" => 128,
        "md5" | "sha1" => {
            return Err(format!(
                "`closure_root` uses forbidden weak digest algorithm `{algo}`. SPEC §12.1 forbids MD5 and SHA-1"
            ));
        }
        _ => {
            return Err(format!(
                "`closure_root` uses unknown digest algorithm `{algo}`"
            ));
        }
    };
    if hex.len() != expected_len || !is_lower_hex(hex) {
        return Err(format!(
            "`closure_root` digest must be {expected_len} lowercase hex chars for `{algo}`"
        ));
    }
    Ok((algo, hex))
}

fn source_hash_records(path: &Path, doc: &Value) -> Result<Vec<String>, Vec<String>> {
    let mut errors = Vec::new();
    let mut records = Vec::new();
    let Some(prov) = doc.get("provenance").and_then(|x| x.as_table()) else {
        return Ok(records);
    };
    let Some(raw) = prov.get("source_sha256") else {
        return Ok(records);
    };
    match raw.as_str() {
        Some(s)
            if s.len() == "sha256:".len() + 64
                && s.starts_with("sha256:")
                && is_lower_hex(&s["sha256:".len()..]) =>
        {
            records.push(format!("provenance.source_sha256 {s}\n"));
        }
        _ => errors.push(format!(
            "{}: `[provenance].source_sha256`, when present, must match `sha256:<64 lowercase hex chars>`",
            path.display()
        )),
    }
    if errors.is_empty() {
        records.sort();
        Ok(records)
    } else {
        Err(errors)
    }
}

fn digest_hex(algo: &str, bytes: &[u8]) -> String {
    // sha2 0.11 returns a `hybrid_array::Array` that no longer implements
    // `LowerHex`, so `format!("{:x}", ...)` no longer compiles. Hex-encode
    // the digest bytes directly (the output derefs to `[u8]`).
    let digest: Vec<u8> = match algo {
        "sha256" => Sha256::digest(bytes).to_vec(),
        "sha384" => Sha384::digest(bytes).to_vec(),
        "sha512" => Sha512::digest(bytes).to_vec(),
        _ => unreachable!("algorithm checked before digest"),
    };
    digest.iter().map(|b| format!("{b:02x}")).collect()
}

fn expected_closure_root(algo: &str, records: &[String]) -> String {
    let mut stream = String::new();
    for record in records {
        stream.push_str(record);
    }
    format!("{algo}:{}", digest_hex(algo, stream.as_bytes()))
}

// ------------------------------------------------------------
// SPEC §12.8.1: profile-pinned closure records
// ------------------------------------------------------------
//
// The pin map is keyed by `template_kind` (kind names are
// namespace-partitioned per SPEC §6.1, so a kind maps to at most one
// profile). Built from the discovered profile descriptors, with
// `closure_records` unioned across `extends` like `contained_kinds`.
// Declaration-shape enforcement (INV07) lives in the
// profile-descriptor path; this consumes well-formed declarations.

/// `{template_kind -> sorted [(field, presence, profile_name)]}`.
type ClosurePinMap = BTreeMap<String, Vec<(String, String, String)>>;

fn closure_pin_map(descriptors: &BTreeMap<String, (PathBuf, Value)>) -> ClosurePinMap {
    let mut pin_map: ClosurePinMap = BTreeMap::new();
    for root in descriptors.keys() {
        let mut seen: BTreeSet<&str> = BTreeSet::new();
        let mut stack: Vec<&str> = vec![root.as_str()];
        while let Some(node) = stack.pop() {
            if seen.contains(node) {
                continue;
            }
            let Some((_, doc)) = descriptors.get(node) else {
                continue;
            };
            seen.insert(node);
            let Some(profile) = doc.get("profile").and_then(|p| p.as_table()) else {
                continue;
            };
            if let Some(arr) = profile.get("closure_records").and_then(|x| x.as_array()) {
                for rec in arr {
                    let Some(table) = rec.as_table() else {
                        continue;
                    };
                    let (Some(kind), Some(field), Some(presence)) = (
                        table.get("contained_kind").and_then(|v| v.as_str()),
                        table.get("field").and_then(|v| v.as_str()),
                        table.get("presence").and_then(|v| v.as_str()),
                    ) else {
                        continue;
                    };
                    if presence != "required" && presence != "when-present" {
                        continue;
                    }
                    let entries = pin_map.entry(kind.to_string()).or_default();
                    // Dedup by (field, presence) only: a record inherited
                    // through `extends` reaches this map once per extending
                    // root, but its record string excludes the profile
                    // name, so keying dedup on the profile would
                    // double-emit the record and corrupt the digest stream.
                    if !entries.iter().any(|(f, p, _)| f == field && p == presence) {
                        entries.push((field.to_string(), presence.to_string(), root.clone()));
                    }
                }
            }
            if let Some(arr) = profile.get("extends").and_then(|x| x.as_array()) {
                for child in arr {
                    if let Some(s) = child.as_str() {
                        stack.push(s);
                    }
                }
            }
        }
    }
    for entries in pin_map.values_mut() {
        entries.sort();
    }
    pin_map
}

fn walk_field<'a>(doc: &'a Value, dotted: &str) -> Option<&'a Value> {
    let mut current = doc;
    for segment in dotted.split('.') {
        current = current.as_table()?.get(segment)?;
    }
    Some(current)
}

fn is_pinned_sha256(s: &str) -> bool {
    s.len() == "sha256:".len() + 64
        && s.starts_with("sha256:")
        && is_lower_hex(&s["sha256:".len()..])
}

/// SPEC §12.8.1 record emission + pin resolution for one document.
///
/// Pins resolve by `template_kind` over the full loaded descriptor
/// set, in EVERY mode that validates `closure_root`; a document of a
/// pinned kind with a missing/unresolvable `framework_profile` is
/// rejected. There is no pin-free fall-through for a pinned kind.
fn pinned_closure_inputs(
    path: &Path,
    doc: &Value,
    pin_map: &ClosurePinMap,
    loaded_profiles: &BTreeSet<String>,
) -> (Vec<String>, Vec<String>) {
    let Some(meta) = doc.get("meta").and_then(|x| x.as_table()) else {
        return (Vec::new(), Vec::new());
    };
    let template_kind = meta
        .get("template_kind")
        .and_then(|x| x.as_str())
        // legacy synonym
        .or_else(|| meta.get("kind").and_then(|x| x.as_str()));
    let Some(template_kind) = template_kind else {
        return (Vec::new(), Vec::new());
    };
    let Some(pins) = pin_map.get(template_kind) else {
        return (Vec::new(), Vec::new());
    };

    let mut errors: Vec<String> = Vec::new();
    match meta.get("framework_profile").and_then(|x| x.as_str()) {
        None | Some("") => errors.push(format!(
            "{}: documents of pinned kind `{template_kind}` MUST declare `meta.framework_profile` (SPEC §12.8.1 pin resolution)",
            path.display()
        )),
        Some(fp) if !loaded_profiles.contains(fp) => errors.push(format!(
            "{}: `meta.framework_profile` `{fp}` does not resolve to a loaded profile-descriptor (SPEC §12.8.1 pin resolution; pinned kind `{template_kind}`)",
            path.display()
        )),
        _ => {}
    }

    let mut records: Vec<String> = Vec::new();
    for (field, presence, profile_name) in pins {
        let Some(value) = walk_field(doc, field) else {
            if presence == "required" {
                errors.push(format!(
                    "{}: pinned closure record `{field}` (required by profile `{profile_name}`, SPEC §12.8.1) is missing",
                    path.display()
                ));
            }
            continue;
        };
        match value.as_str() {
            Some(s) if is_pinned_sha256(s) => {
                records.push(format!("{field} {s}\n"));
            }
            _ => {
                let shown = match value.as_str() {
                    Some(s) => format!("{s:?}"),
                    None => format!("`{}` value", value.type_str()),
                };
                errors.push(format!(
                    "{}: pinned closure record `{field}` must match `sha256:<64 lowercase hex chars>` (SPEC §12.8.1), got {shown}",
                    path.display()
                ));
            }
        }
    }
    (records, errors)
}

fn validate_closure_root(
    path: &Path,
    doc: &Value,
    pin_map: &ClosurePinMap,
    loaded_profiles: &BTreeSet<String>,
) -> Vec<String> {
    let mut errors = Vec::new();
    let Some(value) = doc.get("closure_root") else {
        errors.push(format!(
            "{}: missing required root-level `closure_root` field (SPEC §12.1)",
            path.display()
        ));
        return errors;
    };
    let Some(value) = value.as_str() else {
        errors.push(format!(
            "{}: `closure_root` must be a non-empty string",
            path.display()
        ));
        return errors;
    };
    if value.is_empty() {
        errors.push(format!(
            "{}: `closure_root` must be a non-empty string",
            path.display()
        ));
        return errors;
    }
    let (algo, _) = match split_closure_root(value) {
        Ok(parts) => parts,
        Err(err) => {
            errors.push(format!("{}: {err}", path.display()));
            return errors;
        }
    };
    let (mut records, mut input_errors) = match source_hash_records(path, doc) {
        Ok(records) => (records, Vec::new()),
        Err(errs) => (Vec::new(), errs),
    };
    // SPEC §12.8.1: pinned records join the same sorted record stream
    // as `provenance.source_sha256`; any pin-input error short-circuits
    // before the digest comparison (mirrors the Python reference).
    let (pinned_records, pinned_errors) =
        pinned_closure_inputs(path, doc, pin_map, loaded_profiles);
    records.extend(pinned_records);
    input_errors.extend(pinned_errors);
    if !input_errors.is_empty() {
        errors.extend(input_errors);
        return errors;
    }
    records.sort();
    let expected = expected_closure_root(algo, &records);
    if value != expected {
        if records.is_empty() {
            let sentinel = match algo {
                "sha256" => EMPTY_SHA256,
                "sha384" => EMPTY_SHA384,
                "sha512" => EMPTY_SHA512,
                _ => &expected,
            };
            errors.push(format!(
                "{}: self-contained documents MUST use the canonical empty-closure sentinel `{sentinel}`; got `{value}`",
                path.display()
            ));
        } else {
            errors.push(format!(
                "{}: `closure_root` does not match SPEC §12.8 source-hash closure. Expected `{expected}` from {} canonical source-hash input(s), got `{value}`.",
                path.display(),
                records.len()
            ));
        }
    }
    errors
}

// ------------------------------------------------------------
// §2.5 framework_profile partition (instance file check)
// ------------------------------------------------------------

fn validate_framework_profile(
    path: &Path,
    doc: &Value,
    descriptors: &std::collections::BTreeMap<String, (PathBuf, Value)>,
) -> Vec<String> {
    let mut errors = Vec::new();
    let Some(meta) = doc.get("meta").and_then(|x| x.as_table()) else {
        return errors;
    };
    let Some(name) = meta.get("framework_profile").and_then(|x| x.as_str()) else {
        return errors;
    };
    // SPEC §2.5 grandfather-aliases: AGDF → agent-assurance.
    let resolved = if name == "AGDF" {
        "agent-assurance"
    } else {
        name
    };

    // 1. Shape check — must match one of the two patterns in §2.5.
    let is_unprefixed = !resolved.is_empty()
        && resolved
            .chars()
            .next()
            .is_some_and(|c| c.is_ascii_lowercase())
        && resolved
            .chars()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-');
    let is_reverse_dns = resolved.contains('.')
        && resolved.split('.').all(|p| {
            !p.is_empty()
                && p.chars().next().is_some_and(|c| c.is_ascii_lowercase())
                && p.chars()
                    .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-')
        });
    if !(is_unprefixed || is_reverse_dns) {
        errors.push(format!(
            "{}: [meta].framework_profile = `{}` does not match the SPEC §2.5 namespacing partition (must be unprefixed kebab-case or reverse-DNS)",
            path.display(),
            name
        ));
        return errors;
    }
    // 2. Resolution check — unprefixed names MUST be in the loaded
    //    profile-descriptor set; reverse-DNS names MAY be locally
    //    declared and SHOULD also resolve but absence is downgraded
    //    to a structural lint (the spec doesn't require third-party
    //    descriptors to be shipped here).
    if is_unprefixed && !descriptors.contains_key(resolved) {
        errors.push(format!(
            "{}: [meta].framework_profile = `{}` is an unprefixed (spec-reserved) name but no loaded profile-descriptor declares it (SPEC §2.5)",
            path.display(),
            name
        ));
    }
    errors
}

// ------------------------------------------------------------
// Driver
// ------------------------------------------------------------

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let parsed = match cli::parse(args) {
        Ok(a) => a,
        Err(code) => return code,
    };

    let repo_root: PathBuf = parsed
        .repo_root
        .canonicalize()
        .unwrap_or(parsed.repo_root.clone());

    let (descriptors, duplicate_profiles) = profile::discover(&repo_root);
    if !duplicate_profiles.is_empty() {
        eprintln!("DAGTOML VALIDATION FAILED (rust primary)");
        for d in &duplicate_profiles {
            eprintln!("- {d}: pin resolution refuses to proceed (SPEC 12.8.1)");
        }
        std::process::exit(1);
    }
    // SPEC §12.8.1: build the profile-pinned closure-record map and the
    // loaded-profile-name set once per run; both feed closure_root
    // validation in every mode that runs it.
    let pin_map = closure_pin_map(&descriptors);
    let loaded_profiles: BTreeSet<String> = descriptors.keys().cloned().collect();

    let mut all_errors: Vec<String> = Vec::new();
    let mut validated = 0usize;

    for path in &parsed.files {
        validated += 1;
        let doc = match load(path) {
            Ok(d) => d,
            Err(e) => {
                all_errors.push(e);
                continue;
            }
        };

        let mut errs: Vec<String> = Vec::new();
        let tk = doc
            .get("meta")
            .and_then(|m| m.get("template_kind"))
            .and_then(|x| x.as_str())
            .unwrap_or("");

        // Meta-field checks (§2.2 + §2.5 + §2.6 + §2.7) apply to every doc
        // unconditionally.
        if matches!(parsed.mode, cli::Mode::Auto | cli::Mode::Meta) {
            errs.extend(validate_meta_fields(path, &doc));
            errs.extend(validate_framework_profile(path, &doc, &descriptors));
        }

        // Provenance encryption sub-table check (§11.1).
        if matches!(parsed.mode, cli::Mode::Auto | cli::Mode::Provenance) {
            errs.extend(validate_provenance_encryption(path, &doc));
            errs.extend(validate_closure_root(
                path,
                &doc,
                &pin_map,
                &loaded_profiles,
            ));
        }
        if matches!(parsed.mode, cli::Mode::Auto | cli::Mode::ProvenanceBinding) {
            errs.extend(validate_provenance_binding(path, &doc, &repo_root));
        }

        // Routing by mode + kind.
        match parsed.mode {
            cli::Mode::Auto => match tk {
                "profile-descriptor" => {
                    errs.extend(profile::validate_one(path, &doc, &repo_root, &descriptors));
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
                "kind-descriptor" => {
                    errs.extend(kind_descriptor::validate(
                        path, &doc, &repo_root, true, false,
                    ));
                    errs.extend(abstraction_class::validate(path, &doc, &repo_root));
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
                "ontology" => {
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
                "implementation-dag" => {
                    errs.extend(implementation_dag::validate(path, &doc));
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
                "traceability" => {
                    errs.extend(traceability::validate(path, &doc));
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
                "readiness-gate" | "contract-declaration" | "evidence-matrix" => {
                    errs.extend(review_readiness::validate(path, &doc));
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
                "cost-record" => {
                    errs.extend(cost_record::validate(path, &doc, &repo_root));
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
                "rollback-plan" => {
                    errs.extend(rollback_plan::validate(&doc, &repo_root));
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
                "disclosure-attestation" | "redaction-manifest" | "selective-disclosure-proof" => {
                    errs.extend(disclosure::validate(path, &doc, &repo_root));
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
                "gate-decision" => {
                    errs.extend(gate_decision::validate(path, &doc, &repo_root));
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
                "" => {}
                _ => {
                    errs.extend(ijb::validate(path, &doc, &repo_root));
                }
            },
            cli::Mode::Profile => {
                errs.extend(profile::validate_one(path, &doc, &repo_root, &descriptors));
            }
            cli::Mode::Disclosure => {
                errs.extend(disclosure::validate(path, &doc, &repo_root));
            }
            cli::Mode::GateDecision => {
                errs.extend(gate_decision::validate(path, &doc, &repo_root));
            }
            cli::Mode::KindDescriptor => {
                errs.extend(kind_descriptor::validate(
                    path, &doc, &repo_root, true, false,
                ));
                errs.extend(abstraction_class::validate(path, &doc, &repo_root));
            }
            cli::Mode::Ijb => {
                errs.extend(ijb::validate(path, &doc, &repo_root));
            }
            cli::Mode::ImplementationDag => {
                errs.extend(implementation_dag::validate(path, &doc));
            }
            cli::Mode::Traceability => {
                errs.extend(traceability::validate(path, &doc));
            }
            cli::Mode::ReviewReadiness => {
                errs.extend(review_readiness::validate(path, &doc));
            }
            cli::Mode::CostRecord => {
                errs.extend(cost_record::validate(path, &doc, &repo_root));
            }
            cli::Mode::RollbackPlan => {
                errs.extend(rollback_plan::validate(&doc, &repo_root));
            }
            cli::Mode::AbstractionClass => {
                errs.extend(abstraction_class::validate(path, &doc, &repo_root));
            }
            cli::Mode::Provenance | cli::Mode::Meta | cli::Mode::ProvenanceBinding => {}
        }

        if !errs.is_empty() {
            all_errors.push(format!("--- {} ---", path.display()));
            all_errors.extend(errs);
        }
    }

    if !all_errors.is_empty() {
        eprintln!("DAGTOML VALIDATION FAILED (rust primary)");
        for line in &all_errors {
            eprintln!("- {}", line);
        }
        return ExitCode::from(1);
    }
    println!("DAGTOML VALIDATION PASSED (rust primary)");
    println!("- files validated: {}", validated);
    println!("- profiles in resolution set: {}", descriptors.len());
    ExitCode::SUCCESS
}
