// Safe Rust only: deny any `unsafe` block in this crate. The crate's
// dependencies (serde, toml, oxttl) use unsafe internally — that is
// out of scope for this lint; what we enforce is that nothing WE write
// in this binary reaches for unsafe.
#![forbid(unsafe_code)]

//! dagtoml-rdf — generate the DAG-TOML ontology as RDF/Turtle.
//!
//! Reads:
//!   - <repo-root>/core/ontology.toml
//!   - <repo-root>/profiles/agent-assurance/ontology.toml
//!   - <repo-root>/core/*-kind.toml
//!   - <repo-root>/profiles/agent-assurance/*-kind.toml
//!
//! Emits a single Turtle file containing:
//!   - the six IJB primitives
//!   - 15 template kinds (5 core + 9 profile + 1 meta `kind-descriptor`)
//!   - 23 entity kinds as rdfs:Class with rdfs:subClassOf ijb:Thing
//!   - 30 relation predicates as rdf:Property with rdfs:domain / range
//!   - 29 attribute vocabularies as rdf:Property with owl:oneOf ranges
//!     for closed vocabs, dagtoml:extensible true for open ones
//!
//! This is non-normative reference tooling. The Turtle output is checked
//! into the repo at reference/database/rdf/schema.ttl; consumers do not
//! need this binary to use the artifact.

use serde::Deserialize;
use std::{collections::BTreeMap, fmt::Write as _, fs, path::PathBuf, process::ExitCode};

// ---------- ontology shapes ----------

#[derive(Debug, Deserialize)]
struct Ontology {
    #[serde(default)]
    entities: Vec<Entity>,
    #[serde(default)]
    relations: Vec<Relation>,
    #[serde(default)]
    attribute_vocabularies: Vec<Vocab>,
}

#[derive(Debug, Deserialize)]
#[allow(dead_code)] // ijb_primitive/ijb_class kept for future SHACL emission.
struct Entity {
    #[serde(default)]
    id_prefix: Option<String>,
    #[serde(default)]
    id_pattern: Option<String>,
    #[serde(default)]
    section: Option<String>,
    #[serde(default)]
    schema: Option<String>,
    #[serde(default)]
    description: Option<String>,
    #[serde(default)]
    ijb_primitive: Option<String>,
    #[serde(default)]
    ijb_class: Option<String>,
}

#[derive(Debug, Deserialize)]
struct Relation {
    predicate: String,
    #[serde(default)]
    source: Vec<String>,
    #[serde(default)]
    targets: Vec<String>,
    #[serde(default)]
    cardinality: Option<String>,
    #[serde(default)]
    inverse: Option<String>,
    #[serde(default)]
    notes: Option<String>,
}

#[derive(Debug, Deserialize)]
struct Vocab {
    attribute: String,
    #[serde(default)]
    applies_to: Option<String>,
    #[serde(default)]
    values: Vec<String>,
    #[serde(default)]
    extensible: bool,
    #[serde(default)]
    notes: Option<String>,
}

#[derive(Debug, Deserialize)]
struct KindFile {
    #[serde(default)]
    meta: Option<KindMeta>,
    #[serde(default)]
    kind: Option<KindBlock>,
}

#[derive(Debug, Deserialize)]
struct KindMeta {
    /// `*-kind.toml` files all carry `template_kind = "kind-descriptor"`.
    /// The kind they DESCRIBE is recorded in `describes_kind` (and again
    /// in `kind.name`). We prefer `describes_kind` because it is the
    /// canonical pointer per spec.md §3.
    #[serde(default)]
    describes_kind: Option<String>,
}

#[derive(Debug, Deserialize)]
#[allow(dead_code)] // summary is parsed but not yet emitted.
struct KindBlock {
    #[serde(default)]
    name: Option<String>,
    #[serde(default)]
    template_kind: Option<String>,
    #[serde(default)]
    summary: Option<String>,
}

// ---------- emission ----------

const NS_DAGTOML: &str = "https://verivus-oss.org/dagtoml/v1#";
const NS_DAGPROF: &str = "https://verivus-oss.org/dagtoml/profile/agent-assurance/v1#";
const NS_IJB: &str = "https://verivus-oss.org/dagtoml/ijb/v1#";

/// Convert snake_case / kebab-case to PascalCase for RDF class names.
fn pascal(name: &str) -> String {
    let mut out = String::with_capacity(name.len());
    let mut up = true;
    for ch in name.chars() {
        if ch == '_' || ch == '-' || ch == ':' || ch == '.' {
            up = true;
        } else if up {
            out.extend(ch.to_uppercase());
            up = false;
        } else {
            out.push(ch);
        }
    }
    out
}

/// Quote a string for inclusion in a Turtle literal.
fn ttl_lit(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('"');
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            _ => out.push(ch),
        }
    }
    out.push('"');
    out
}

/// Map an ontology source/target token (entity name, "units" alias, regex
/// id-pattern) to a CURIE referencing dagtoml: / dagprof: namespace.
/// Returns None for free-form ranges (e.g. "unconstrained_label") so the
/// emitter can omit rdfs:range and add a marker instead.
fn token_to_class(token: &str) -> Option<String> {
    match token {
        // ontology-only aliases for entity collections (the [[entities]]
        // entry uses `section = "units"`, but relations cite the shorter
        // form). Map both to the singular class name.
        "units" => Some(format!("dagtoml:{}", pascal("unit"))),
        "contracts" => Some(format!("dagtoml:{}", pascal("contract"))),
        "matrix" => Some(format!("dagtoml:{}", pascal("matrix"))),
        "claims" => Some(format!("dagtoml:{}", pascal("claim"))),
        "evidence" => Some(format!("dagtoml:{}", pascal("evidence"))),
        "gates" => Some(format!("dagtoml:{}", pascal("gate"))),
        "artifact_classes" => Some(format!("dagtoml:{}", pascal("artifact_class"))),
        // free-form
        "unconstrained_label" | "" => None,
        // upper-case ID prefixes (INT, FEAT, REQ, …) — convert to the
        // entity class name. We rely on a small lookup so prefixes that
        // don't map cleanly (regex-keyed entities) raise no panic.
        prefix => {
            // Map common prefixes back to entity_kind names. Keep this
            // table in sync with src/main.rs::ENTITY_PREFIX_TO_KIND.
            let kind = match prefix {
                "INT" => "intent",
                "FEAT" => "feature",
                "REQ" => "requirement",
                "REG" => "regulation",
                "DEC" => "decision",
                "IMP" => "implementation",
                "CODE" => "code",
                "TEST" => "test",
                "OUT" => "output",
                "ART" => "artifact",
                "GUAR" => "guarantee",
                "INV" => "invariant",
                "NG" => "non_goal",
                "THREAT" => "threat",
                "SMOKE" => "smoke_check",
                "TRIG" => "rollback_trigger",
                "DISC" => "disclosure_attestation",
                "RED" => "redaction",
                "SDP" => "selective_disclosure_proof",
                // already a kind name? pass through.
                _ => prefix,
            };
            Some(format!("dagtoml:{}", pascal(kind)))
        }
    }
}

fn entity_kind_name(e: &Entity) -> Option<String> {
    // The ontology stores either an id_prefix (REQ, FEAT, GUAR, …) or an
    // id_pattern (U\d+[a-z]?). We derive a canonical kind name by
    // consulting the same prefix-to-kind table, falling back to the
    // section name for regex-keyed entities.
    if let Some(prefix) = &e.id_prefix {
        let kind = match prefix.as_str() {
            "INT" => "intent",
            "FEAT" => "feature",
            "REQ" => "requirement",
            "REG" => "regulation",
            "DEC" => "decision",
            "IMP" => "implementation",
            "CODE" => "code",
            "TEST" => "test",
            "OUT" => "output",
            "ART" => "artifact",
            "GUAR" => "guarantee",
            "INV" => "invariant",
            "NG" => "non_goal",
            "THREAT" => "threat",
            "SMOKE" => "smoke_check",
            "TRIG" => "rollback_trigger",
            "DISC" => "disclosure_attestation",
            "RED" => "redaction",
            "SDP" => "selective_disclosure_proof",
            other => other,
        };
        Some(kind.to_string())
    } else if let Some(section) = &e.section {
        // regex-keyed entities (U\d+, A\d+, …) use the section to name
        // the kind: units → unit, artifact_classes → artifact_class, etc.
        let singular = match section.as_str() {
            "units" => "unit",
            "artifact_classes" => "artifact_class",
            "gates" => "gate",
            "contracts" => "contract",
            "claims" => "claim",
            "evidence" => "evidence",
            "matrix" => "matrix",
            other => other,
        };
        Some(singular.to_string())
    } else {
        None
    }
}

struct Emitter {
    out: String,
}

impl Emitter {
    fn new() -> Self {
        let mut e = Self {
            out: String::with_capacity(32 * 1024),
        };
        e.preamble();
        e
    }

    fn preamble(&mut self) {
        let _ = writeln!(
            self.out,
            "# DAG-TOML ontology as RDF/Turtle (non-normative reference)."
        );
        let _ = writeln!(
            self.out,
            "# Generated by tools/dagtoml-rdf from core/ontology.toml +"
        );
        let _ = writeln!(
            self.out,
            "# every profiles/<name>/ontology.toml. Do not hand-edit;"
        );
        let _ = writeln!(self.out, "# re-run `cargo run -p dagtoml-rdf` instead.");
        let _ = writeln!(self.out);
        let _ = writeln!(self.out, "@prefix dagtoml: <{NS_DAGTOML}> .");
        let _ = writeln!(self.out, "@prefix dagprof: <{NS_DAGPROF}> .");
        let _ = writeln!(self.out, "@prefix ijb:     <{NS_IJB}> .");
        let _ = writeln!(
            self.out,
            "@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> ."
        );
        let _ = writeln!(
            self.out,
            "@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> ."
        );
        let _ = writeln!(
            self.out,
            "@prefix owl:     <http://www.w3.org/2002/07/owl#> ."
        );
        let _ = writeln!(
            self.out,
            "@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> ."
        );
        let _ = writeln!(self.out);
    }

    fn section(&mut self, title: &str) {
        let _ = writeln!(self.out, "###");
        let _ = writeln!(self.out, "### {title}");
        let _ = writeln!(self.out, "###");
        let _ = writeln!(self.out);
    }

    fn ijb_primitives(&mut self) {
        self.section("IJB primitives (spec.md §10)");
        for (term, label) in [
            ("Thing", "thing"),
            ("Scope", "scope"),
            ("Path", "path"),
            ("Observed", "observed"),
            ("Constraint", "constraint"),
            ("Time", "time"),
        ] {
            let _ = writeln!(
                self.out,
                "ijb:{term} a rdfs:Class ;\n    rdfs:label {} .\n",
                ttl_lit(label)
            );
        }
    }

    fn kind_descriptors(&mut self, kinds: &[(String, String, String)]) {
        // kinds: Vec<(template_kind, layer, descriptor_path)>
        let title = format!(
            "Template kinds ({} = core + every profile + 1 meta)",
            kinds.len()
        );
        self.section(&title);
        let _ = writeln!(
            self.out,
            "dagtoml:KindDescriptor a rdfs:Class ;\n    rdfs:subClassOf ijb:Thing ;\n    rdfs:label {} ;\n    rdfs:comment {} .\n",
            ttl_lit("kind-descriptor"),
            ttl_lit("Self-contained template descriptor for a DAG-TOML kind."),
        );
        for (template_kind, layer, descriptor_path) in kinds {
            let class = pascal(template_kind);
            let _ = writeln!(
                self.out,
                "dagtoml:{class}Kind a dagtoml:KindDescriptor ;\n    dagtoml:templateKind   {} ;\n    dagtoml:layer          {} ;\n    dagtoml:descriptorPath {} .\n",
                ttl_lit(template_kind),
                ttl_lit(layer),
                ttl_lit(descriptor_path),
            );
        }
    }

    fn entity_kinds(&mut self, entities: &[(String, String, Entity)]) {
        // entities: Vec<(kind_name, layer, Entity)>
        let title = format!("Entity kinds ({}, all ijb:Thing)", entities.len());
        self.section(&title);
        for (kind, layer, e) in entities {
            let class = pascal(kind);
            let _ = write!(
                self.out,
                "dagtoml:{class} a rdfs:Class ;\n    rdfs:subClassOf ijb:Thing ;\n    rdfs:label {} ;\n    dagtoml:layer {} ",
                ttl_lit(kind),
                ttl_lit(layer),
            );
            if let Some(p) = &e.id_prefix {
                let _ = write!(self.out, ";\n    dagtoml:idPrefix {} ", ttl_lit(p));
            }
            if let Some(p) = &e.id_pattern {
                let _ = write!(self.out, ";\n    dagtoml:idPattern {} ", ttl_lit(p));
            }
            if let Some(s) = &e.section {
                let _ = write!(self.out, ";\n    dagtoml:section {} ", ttl_lit(s));
            }
            if let Some(sch) = &e.schema {
                let _ = write!(self.out, ";\n    dagtoml:definedByKind {} ", ttl_lit(sch));
            }
            if let Some(c) = &e.description {
                let _ = write!(self.out, ";\n    rdfs:comment {} ", ttl_lit(c));
            }
            let _ = writeln!(self.out, ".\n");
        }
    }

    fn relations(&mut self, relations: &[(Relation, String)]) {
        // relations: Vec<(Relation, namespaced_predicate_name)>
        // Some predicate names appear more than once with different
        // domain/range; we namespace them (contract:depends_on, …).
        let title = format!(
            "Relation predicates ({} = one per [[relations]] block in core/ontology.toml)",
            relations.len()
        );
        self.section(&title);
        for (r, namespaced) in relations {
            // local URI fragment must be a valid Turtle local name; use
            // an underscore where the ontology uses a colon namespace.
            let local = namespaced.replace(':', "_");
            let _ = write!(
                self.out,
                "dagtoml:{local} a rdf:Property ;\n    rdfs:label {} ",
                ttl_lit(namespaced),
            );
            // domain (union if multiple)
            let domains: Vec<String> = r
                .source
                .iter()
                .filter_map(|s| token_to_class(s.as_str()))
                .collect();
            if !domains.is_empty() {
                if domains.len() == 1 {
                    let _ = write!(self.out, ";\n    rdfs:domain {} ", domains[0]);
                } else {
                    let _ = write!(
                        self.out,
                        ";\n    rdfs:domain [ a owl:Class ; owl:unionOf ( {} ) ] ",
                        domains.join(" ")
                    );
                }
            }
            // range
            let typed: Vec<String> = r
                .targets
                .iter()
                .filter_map(|t| token_to_class(t.as_str()))
                .collect();
            let freeform = r.targets.iter().any(|t| t == "unconstrained_label");
            if freeform {
                let _ = write!(self.out, ";\n    dagtoml:targetFreeForm true ");
            }
            if !typed.is_empty() {
                if typed.len() == 1 {
                    let _ = write!(self.out, ";\n    rdfs:range {} ", typed[0]);
                } else {
                    let _ = write!(
                        self.out,
                        ";\n    rdfs:range [ a owl:Class ; owl:unionOf ( {} ) ] ",
                        typed.join(" ")
                    );
                }
            }
            if let Some(inv) = &r.inverse {
                if !inv.is_empty() {
                    let _ = write!(
                        self.out,
                        ";\n    owl:inverseOf dagtoml:{} ",
                        inv.replace(':', "_")
                    );
                }
            }
            if let Some(c) = &r.cardinality {
                let _ = write!(self.out, ";\n    dagtoml:cardinality {} ", ttl_lit(c));
            }
            if let Some(n) = &r.notes {
                let _ = write!(self.out, ";\n    rdfs:comment {} ", ttl_lit(n));
            }
            let _ = writeln!(self.out, ".\n");
        }
    }

    fn vocabularies(&mut self, vocabs: &[(Vocab, String)], template_kind_names: &[String]) {
        // vocabs: Vec<(Vocab, layer)>
        let title = format!("Attribute vocabularies ({})", vocabs.len());
        self.section(&title);
        for (v, layer) in vocabs {
            let local = v.attribute.replace(['.', ':'], "_");
            let _ = write!(
                self.out,
                "dagtoml:{local} a rdf:Property ;\n    rdfs:label {} ;\n    dagtoml:layer {} ;\n    dagtoml:extensible {} ",
                ttl_lit(&v.attribute),
                ttl_lit(layer),
                if v.extensible { "true" } else { "false" },
            );
            if let Some(applies) = &v.applies_to {
                if template_kind_names.iter().any(|k| k == applies) {
                    // The vocabulary lives on a singleton table of the
                    // named template_kind (e.g. smoke.decision on
                    // smoke-validation). Use appliesToKind so consumers
                    // don't confuse it with an entity domain.
                    let class = pascal(applies);
                    let _ = write!(
                        self.out,
                        ";\n    dagtoml:appliesToKind dagtoml:{class}Kind "
                    );
                } else if let Some(domain) = token_to_class(applies.as_str()) {
                    let _ = write!(self.out, ";\n    rdfs:domain {domain} ");
                } else {
                    let _ = write!(self.out, ";\n    dagtoml:appliesTo {} ", ttl_lit(applies));
                }
            }
            if !v.values.is_empty() {
                let parts: Vec<String> = v.values.iter().map(|x| ttl_lit(x)).collect();
                let _ = write!(
                    self.out,
                    ";\n    rdfs:range [ a rdfs:Datatype ; owl:oneOf ( {} ) ] ",
                    parts.join(" "),
                );
            }
            if let Some(n) = &v.notes {
                let _ = write!(self.out, ";\n    rdfs:comment {} ", ttl_lit(n));
            }
            let _ = writeln!(self.out, ".\n");
        }
    }
}

// ---------- loader ----------

fn namespaced_predicate(r: &Relation, seen: &mut BTreeMap<String, usize>) -> String {
    // First occurrence keeps the bare name. Subsequent occurrences of the
    // same predicate get a `<scope>:` prefix derived from the source
    // entity-kind token. This mirrors reference/database/postgres/seed.sql.
    let key = r.predicate.clone();
    let count = seen.entry(key.clone()).or_insert(0);
    *count += 1;
    if *count == 1 {
        return r.predicate.clone();
    }
    // pick a scope from the first source token
    let scope = r
        .source
        .first()
        .map(|s| match s.as_str() {
            "contracts" => "contract".to_string(),
            other => other.to_string(),
        })
        .unwrap_or_else(|| "scoped".to_string());
    format!("{scope}:{}", r.predicate)
}

fn verify(path: &PathBuf) -> ExitCode {
    let bytes = match fs::read(path) {
        Ok(b) => b,
        Err(e) => {
            eprintln!("failed to read {path:?}: {e}");
            return ExitCode::FAILURE;
        }
    };
    let mut count = 0usize;
    for triple in oxttl::TurtleParser::new().for_slice(&bytes) {
        match triple {
            Ok(_) => count += 1,
            Err(e) => {
                eprintln!("parse error in {path:?}: {e}");
                return ExitCode::FAILURE;
            }
        }
    }
    eprintln!("verify {path:?}: OK — parsed {count} triples");
    ExitCode::SUCCESS
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().collect();
    let mut repo_root = PathBuf::from(".");
    let mut output: Option<PathBuf> = None;
    let mut subcommand: Option<String> = None;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "verify" => {
                subcommand = Some("verify".into());
            }
            "--repo-root" => {
                i += 1;
                repo_root = PathBuf::from(&args[i]);
            }
            "-o" | "--output" => {
                i += 1;
                output = Some(PathBuf::from(&args[i]));
            }
            "-h" | "--help" => {
                eprintln!(
                    "dagtoml-rdf — DAG-TOML ontology Turtle generator.\n\nUsage:\n    dagtoml-rdf [--repo-root <path>] [-o <path>]    # generate\n    dagtoml-rdf verify -o <path>                    # re-parse the .ttl"
                );
                return ExitCode::SUCCESS;
            }
            other => {
                eprintln!("unknown argument: {other}");
                return ExitCode::from(2);
            }
        }
        i += 1;
    }

    if subcommand.as_deref() == Some("verify") {
        let Some(path) = output else {
            eprintln!("verify requires -o <path>");
            return ExitCode::from(2);
        };
        return verify(&path);
    }

    let core_ont_path = repo_root.join("core/ontology.toml");
    let core_ont: Ontology = match fs::read_to_string(&core_ont_path).and_then(|s| {
        toml::from_str::<Ontology>(&s)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
    }) {
        Ok(o) => o,
        Err(e) => {
            eprintln!("failed to read {core_ont_path:?}: {e}");
            return ExitCode::FAILURE;
        }
    };

    // Walk every profiles/<name>/ontology.toml. The set of profiles is
    // not hardcoded — the generator picks up new profiles automatically.
    let mut profile_onts: Vec<(String, Ontology)> = Vec::new();
    if let Ok(profiles_dir) = fs::read_dir(repo_root.join("profiles")) {
        let mut entries: Vec<PathBuf> = profiles_dir
            .filter_map(|e| e.ok())
            .map(|e| e.path())
            .filter(|p| p.is_dir())
            .collect();
        entries.sort();
        for dir in entries {
            let ont_path = dir.join("ontology.toml");
            if !ont_path.exists() {
                continue;
            }
            let prof_name = dir
                .file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("")
                .to_string();
            let parsed: Ontology = match fs::read_to_string(&ont_path).and_then(|s| {
                toml::from_str::<Ontology>(&s)
                    .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
            }) {
                Ok(o) => o,
                Err(e) => {
                    eprintln!("failed to read {ont_path:?}: {e}");
                    return ExitCode::FAILURE;
                }
            };
            profile_onts.push((prof_name, parsed));
        }
    }

    // Collect kind descriptors: 1 meta + every *-kind.toml on disk.
    let mut kinds: Vec<(String, String, String)> =
        vec![("kind-descriptor".into(), "core".into(), "spec.md".into())];
    let mut kind_bases: Vec<(String, String)> = vec![("core".into(), "core".into())];
    for (prof_name, _) in &profile_onts {
        kind_bases.push((
            format!("profile:{prof_name}"),
            format!("profiles/{prof_name}"),
        ));
    }
    for (layer, base) in &kind_bases {
        let layer = layer.as_str();
        let base = base.as_str();
        let dir = repo_root.join(base);
        let Ok(read) = fs::read_dir(&dir) else {
            continue;
        };
        let mut paths: Vec<PathBuf> = read
            .filter_map(|e| e.ok())
            .map(|e| e.path())
            .filter(|p| p.extension().is_some_and(|x| x == "toml"))
            .filter(|p| {
                p.file_name()
                    .and_then(|n| n.to_str())
                    .is_some_and(|n| n.ends_with("-kind.toml"))
            })
            .collect();
        paths.sort();
        for p in paths {
            let Ok(s) = fs::read_to_string(&p) else {
                continue;
            };
            let parsed: KindFile = match toml::from_str(&s) {
                Ok(v) => v,
                Err(_) => continue,
            };
            // *-kind.toml files all carry meta.template_kind =
            // "kind-descriptor". The kind they DESCRIBE is named in
            // meta.describes_kind (preferred) or [kind].name.
            let tk = parsed
                .meta
                .as_ref()
                .and_then(|m| m.describes_kind.clone())
                .or_else(|| parsed.kind.as_ref().and_then(|k| k.name.clone()))
                .or_else(|| parsed.kind.as_ref().and_then(|k| k.template_kind.clone()));
            if let Some(tk) = tk {
                if tk == "kind-descriptor" {
                    // the descriptor of descriptors — skip; we already
                    // added the meta row above.
                    continue;
                }
                let rel = p
                    .strip_prefix(&repo_root)
                    .unwrap_or(&p)
                    .to_string_lossy()
                    .replace('\\', "/");
                kinds.push((tk, layer.to_string(), rel));
            }
        }
    }

    // Entities: collect, attach layer, derive kind name.
    let mut entities: Vec<(String, String, Entity)> = Vec::new();
    for e in core_ont.entities {
        if let Some(kind) = entity_kind_name(&e) {
            entities.push((kind, "core".into(), e));
        }
    }
    for (prof_name, prof_ont) in &profile_onts {
        for e in &prof_ont.entities {
            if let Some(kind) = entity_kind_name(e) {
                entities.push((
                    kind,
                    format!("profile:{prof_name}"),
                    Entity {
                        id_prefix: e.id_prefix.clone(),
                        id_pattern: e.id_pattern.clone(),
                        section: e.section.clone(),
                        schema: e.schema.clone(),
                        description: e.description.clone(),
                        ijb_primitive: e.ijb_primitive.clone(),
                        ijb_class: e.ijb_class.clone(),
                    },
                ));
            }
        }
    }

    // Relations: namespace duplicates.
    let mut seen = BTreeMap::new();
    let mut relations: Vec<(Relation, String)> = Vec::new();
    for r in core_ont.relations {
        let ns = namespaced_predicate(&r, &mut seen);
        relations.push((r, ns));
    }
    // profile.relations is intentionally not yet enumerated — the profile
    // declares no namespaced predicates today (per ontology.md). When it
    // does, append here.

    // Vocabularies (iterate every profile)
    let mut vocabs: Vec<(Vocab, String)> = Vec::new();
    for v in core_ont.attribute_vocabularies {
        vocabs.push((v, "core".into()));
    }
    for (prof_name, prof_ont) in &profile_onts {
        for v in &prof_ont.attribute_vocabularies {
            vocabs.push((
                Vocab {
                    attribute: v.attribute.clone(),
                    applies_to: v.applies_to.clone(),
                    values: v.values.clone(),
                    extensible: v.extensible,
                    notes: v.notes.clone(),
                },
                format!("profile:{prof_name}"),
            ));
        }
    }

    // Emit.
    let mut em = Emitter::new();
    em.ijb_primitives();
    em.kind_descriptors(&kinds);
    em.entity_kinds(&entities);
    em.relations(&relations);
    let template_kind_names: Vec<String> = kinds.iter().map(|(k, _, _)| k.clone()).collect();
    em.vocabularies(&vocabs, &template_kind_names);

    // Footer: print observed counts so the consumer can diff vs MANIFEST.
    let _ = writeln!(em.out, "###");
    let _ = writeln!(
        em.out,
        "### Counts at generation: {} template kinds, {} entity kinds, {} relation predicates, {} attribute vocabularies.",
        kinds.len(),
        entities.len(),
        relations.len(),
        vocabs.len(),
    );
    let _ = writeln!(em.out, "###");

    match output {
        Some(p) => {
            if let Err(e) = fs::write(&p, em.out.as_bytes()) {
                eprintln!("failed to write {p:?}: {e}");
                return ExitCode::FAILURE;
            }
            eprintln!(
                "wrote {p:?}: {tk} template kinds, {ek} entity kinds, {rk} relations, {vk} vocabularies",
                tk = kinds.len(),
                ek = entities.len(),
                rk = relations.len(),
                vk = vocabs.len(),
            );
        }
        None => {
            print!("{}", em.out);
        }
    }
    ExitCode::SUCCESS
}
