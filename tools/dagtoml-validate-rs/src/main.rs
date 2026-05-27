//! Safe-Rust primary validator for the DAG-TOML artifacts introduced
//! by the draft layering work:
//!
//! - `template_kind = "profile-descriptor"` (spec.md §6.1)
//! - The disclosure profile kinds (`disclosure-attestation`,
//!   `redaction-manifest`, `selective-disclosure-proof`)
//! - The `[provenance.encryption]` sub-table (spec.md §11.1)
//! - The SPEC §2.7 cross-field rule
//!   (`confidentiality = "embargoed"` REQUIRES `embargo_until`)
//! - The §2.5 namespacing partition
//!   (unprefixed kebab-case ⇔ `namespace = "spec.reserved"`;
//!   everything else MUST be reverse-DNS).
//! - The §2.6 `[meta].docs` URL shape (https://, no `?`).
//! - The §2.2 / §8 version pin shapes:
//!   `schema_version` is semver; `ontology_version`, when present, is
//!   a positive integer snapshot.
//!
//! This binary is the **primary** validator for the new artifacts.
//! The reference Python validators under `validators/` are retained
//! as a cross-check; CI runs Rust + Go first and treats divergence
//! as a build break.
//!
//! Safety posture: `#![forbid(unsafe_code)]`. No FFI, no
//! third-party `unsafe`-using deps beyond the `toml` and `serde`
//! crates which are widely vetted.

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
    }

    pub fn print_usage() {
        eprintln!(
            "usage: dagtoml-validate-rs --repo-root <path> [--mode auto|profile|disclosure|provenance|meta|gate-decision] <file.toml> ..."
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
                    other => {
                        eprintln!(
                            "error: --mode value must be auto|profile|disclosure|provenance|meta|gate-decision (got {:?})",
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
    raw.parse::<Value>()
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

    pub fn discover(repo_root: &Path) -> BTreeMap<String, (PathBuf, Value)> {
        let mut out = BTreeMap::new();
        let dir = repo_root.join("profiles");
        let Ok(entries) = std::fs::read_dir(&dir) else {
            return out;
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
                out.insert(name.to_string(), (candidate, doc));
            }
        }
        out
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
                if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
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
    match algo {
        "sha256" => format!("{:x}", Sha256::digest(bytes)),
        "sha384" => format!("{:x}", Sha384::digest(bytes)),
        "sha512" => format!("{:x}", Sha512::digest(bytes)),
        _ => unreachable!("algorithm checked before digest"),
    }
}

fn expected_closure_root(algo: &str, records: &[String]) -> String {
    let mut stream = String::new();
    for record in records {
        stream.push_str(record);
    }
    format!("{algo}:{}", digest_hex(algo, stream.as_bytes()))
}

fn validate_closure_root(path: &Path, doc: &Value) -> Vec<String> {
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
    let records = match source_hash_records(path, doc) {
        Ok(records) => records,
        Err(errs) => return errs,
    };
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

    let descriptors = profile::discover(&repo_root);

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
            errs.extend(validate_closure_root(path, &doc));
        }

        // Routing by mode + kind.
        match parsed.mode {
            cli::Mode::Auto => match tk {
                "profile-descriptor" => {
                    errs.extend(profile::validate_one(path, &doc, &repo_root, &descriptors));
                }
                "disclosure-attestation" | "redaction-manifest" | "selective-disclosure-proof" => {
                    errs.extend(disclosure::validate(path, &doc, &repo_root));
                }
                "gate-decision" => {
                    errs.extend(gate_decision::validate(path, &doc, &repo_root));
                }
                _ => {}
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
            cli::Mode::Provenance | cli::Mode::Meta => {}
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
