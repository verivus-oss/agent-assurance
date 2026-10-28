#![forbid(unsafe_code)]

use std::collections::{BTreeMap, BTreeSet};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};

use dagtoml_spell::dictionary::{Dictionary, SOURCE_SHA256};
use dagtoml_spell::digest::sha256;
use dagtoml_spell::git::{self, Kind};
use dagtoml_spell::identity::{self, BUILD_TREE_SHA256};
use dagtoml_spell::project::{Failure, Project, read_source};
use dagtoml_spell::scan::{self, Finding};
use dagtoml_spell::scope::{Scope, binary_kind, classify};
use serde::Serialize;

#[derive(Serialize)]
struct Subject {
    path: String,
    state: String,
    reason: String,
    source_sha256: Option<String>,
    target_object: Option<String>,
}

#[derive(Serialize)]
struct ErrorRecord {
    path: String,
    source_sha256: Option<String>,
    byte_span: Option<[usize; 2]>,
    message: String,
}

#[derive(Serialize)]
struct Report {
    schema_version: String,
    rule_version: String,
    status: String,
    comparison: String,
    base_commit: Option<String>,
    tree_state: String,
    instrument_tree_sha256: String,
    dictionary_sha256: String,
    policy_sources: BTreeMap<String, String>,
    subjects: Vec<Subject>,
    findings: Vec<Finding>,
    errors: Vec<ErrorRecord>,
}

impl Report {
    fn new() -> Self {
        Self { schema_version: "spelling-report-v1".to_owned(), rule_version: scan::RULE_VERSION.to_owned(),
               status: "failed".to_owned(), comparison: "selected tracked source and path tokens against the pinned literal correction table and typed data roles".to_owned(),
               base_commit: None, tree_state: "not-measured".to_owned(), instrument_tree_sha256: BUILD_TREE_SHA256.to_owned(),
               dictionary_sha256: SOURCE_SHA256.to_owned(), policy_sources: BTreeMap::new(), subjects: Vec::new(), findings: Vec::new(), errors: Vec::new() }
    }

    fn fail(&mut self, failure: Failure) {
        self.status = "failed".to_owned();
        self.errors.push(ErrorRecord {
            path: failure.path,
            source_sha256: failure.source_sha256,
            byte_span: failure.byte_span.map(|span| [span.start, span.end]),
            message: failure.message.to_owned(),
        });
    }
}

struct Options {
    root: PathBuf,
    stdin_name: Option<String>,
    identity: bool,
    help: bool,
}

fn options() -> Result<Options, Failure> {
    let mut result = Options {
        root: PathBuf::from("."),
        stdin_name: None,
        identity: false,
        help: false,
    };
    let mut arguments = std::env::args_os().skip(1);
    let mut seen = BTreeSet::new();
    while let Some(argument) = arguments.next() {
        let argument = argument
            .into_string()
            .map_err(|_| Failure::at("<options>", None, "spelling options must be UTF-8"))?;
        if !seen.insert(argument.clone()) {
            return Err(Failure::at(
                "<options>",
                None,
                "spelling option was repeated",
            ));
        }
        match argument.as_str() {
            "--help" | "-h" => result.help = true,
            "--identity" => result.identity = true,
            "--repo-root" | "--stdin" => {
                let value = arguments.next().ok_or_else(|| {
                    Failure::at("<options>", None, "spelling option requires a value")
                })?;
                let value = value.into_string().map_err(|_| {
                    Failure::at("<options>", None, "spelling option value must be UTF-8")
                })?;
                if value.is_empty() || value.starts_with('-') {
                    return Err(Failure::at(
                        "<options>",
                        None,
                        "spelling option requires a nonempty value",
                    ));
                }
                if argument == "--repo-root" {
                    result.root = PathBuf::from(value);
                } else {
                    result.stdin_name = Some(value);
                }
            }
            _ => {
                return Err(Failure::at(
                    "<options>",
                    None,
                    "spelling option is unsupported",
                ));
            }
        }
    }
    if result.identity && result.stdin_name.is_some() {
        return Err(Failure::at(
            "<options>",
            None,
            "spelling identity mode cannot also scan input",
        ));
    }
    Ok(result)
}

fn add_checked(
    report: &mut Report,
    checked: scan::Checked,
    words: &mut usize,
) -> Result<String, Failure> {
    if checked.findings.len() > checked.checked_words {
        return Err(Failure::at(
            "<scan>",
            None,
            "spelling findings exceed their checked word population",
        ));
    }
    *words = words
        .checked_add(checked.checked_words)
        .ok_or_else(|| Failure::at("<scan>", None, "spelling word population overflow"))?;
    report.findings.extend(checked.findings);
    Ok(checked.source_sha256)
}

fn subject(
    path: &str,
    state: &str,
    reason: &str,
    source: Option<String>,
    object: Option<String>,
) -> Subject {
    Subject {
        path: path.to_owned(),
        state: state.to_owned(),
        reason: reason.to_owned(),
        source_sha256: source,
        target_object: object,
    }
}

fn finish(report: &mut Report, words: usize) -> Result<(), Failure> {
    if words == 0 {
        return Err(Failure::at(
            "<scan>",
            None,
            "spelling scan did not examine any language words",
        ));
    }
    let distinct: BTreeSet<_> = report
        .findings
        .iter()
        .map(|finding| (&finding.path, &finding.source_kind, finding.byte_span))
        .collect();
    if distinct.len() != report.findings.len() {
        return Err(Failure::at(
            "<scan>",
            None,
            "spelling scan repeated a source obligation",
        ));
    }
    report.findings.sort_by(|a, b| {
        (&a.path, &a.source_kind, a.byte_span).cmp(&(&b.path, &b.source_kind, b.byte_span))
    });
    report.status = if report.findings.is_empty() {
        "no-corrections"
    } else {
        "findings"
    }
    .to_owned();
    Ok(())
}

fn execute(options: Options, report: &mut Report) -> Result<(), Failure> {
    if options.identity {
        report.status = "identity".to_owned();
        report.comparison =
            "compiled instrument identities only; no source scan was executed".to_owned();
        return Ok(());
    }
    let root = options
        .root
        .canonicalize()
        .map_err(|_| Failure::at("<repository>", None, "spelling repository root is absent"))?;
    let actual = git::run(&root, &["rev-parse", "--show-toplevel"])?;
    let actual = std::str::from_utf8(actual.strip_suffix(b"\n").ok_or_else(|| {
        Failure::at(
            "<repository>",
            Some(&actual),
            "spelling root identity has incomplete framing",
        )
    })?)
    .map_err(|_| {
        Failure::at(
            "<repository>",
            Some(&actual),
            "spelling repository root is not UTF-8",
        )
    })?;
    if Path::new(actual).canonicalize().map_err(|_| {
        Failure::at(
            "<repository>",
            None,
            "spelling repository root cannot be resolved",
        )
    })? != root
    {
        return Err(Failure::at(
            "<repository>",
            None,
            "spelling scan requires the repository root",
        ));
    }
    let head = git::head(&root)?;
    report.base_commit = Some(head.clone());
    let initial_status = git::run(&root, &["status", "--porcelain=v1", "-z"])?;
    identity::verify(&root.join("tools/dagtoml-spell"))
        .map_err(|message| Failure::at("tools/dagtoml-spell", None, message))?;
    let project = Project::load(&root)?;
    report.policy_sources = project.source_hashes().clone();
    let dictionary = Dictionary::pinned(project.accepted_words.clone())
        .map_err(|message| Failure::at("tools/dagtoml-spell/data/words.csv", None, message))?;
    let mut words = 0;
    if let Some(path) = options.stdin_name {
        report.comparison = "provided UTF-8 input tokens against the pinned literal correction table and the declared file identity data context; filenames and tracked-file population were not scanned".to_owned();
        if classify(&path).map_err(|message| Failure::at(&path, None, message))? != Scope::Text {
            return Err(Failure::at(
                &path,
                None,
                "spelling input requires a governed text identity",
            ));
        }
        let mut source = Vec::new();
        std::io::stdin()
            .read_to_end(&mut source)
            .map_err(|_| Failure::at(&path, None, "spelling input bytes are unavailable"))?;
        if source.is_empty() {
            return Err(Failure::at(
                &path,
                Some(&source),
                "spelling input subject is absent",
            ));
        }
        let digest = add_checked(
            report,
            scan::content(&project, &dictionary, &path, &source)?,
            &mut words,
        )?;
        report.subjects.push(subject(
            &path,
            "checked-input",
            "provided UTF-8 input bytes; filenames were not part of this probe",
            Some(digest),
            None,
        ));
    } else {
        let index = git::run(&root, &["ls-files", "--stage", "-z", "--full-name"])?;
        let entries = git::entries(&index)?;
        let required: BTreeSet<_> = entries.iter().map(|entry| entry.path.clone()).collect();
        let mut visited = BTreeSet::new();
        let mut fingerprints = BTreeMap::new();
        for entry in entries {
            visited.insert(entry.path.clone());
            let scope =
                classify(&entry.path).map_err(|message| Failure::at(&entry.path, None, message))?;
            if let Scope::Excluded(reason) = scope {
                report
                    .subjects
                    .push(subject(&entry.path, "excluded", reason, None, None));
                continue;
            }
            add_checked(
                report,
                scan::filename(&project, &dictionary, &entry.path)?,
                &mut words,
            )?;
            if entry.kind == Kind::Gitlink {
                report.subjects.push(subject(
                    &entry.path,
                    "name-checked",
                    "external gitlink repository content is outside this scan",
                    None,
                    Some(entry.object),
                ));
                continue;
            }
            let bytes = read_source(&root, &entry.path)?;
            let digest = sha256(&bytes);
            fingerprints.insert(entry.path.clone(), digest.clone());
            if scope == Scope::PinnedDictionary {
                if digest != SOURCE_SHA256 {
                    return Err(Failure::at(
                        &entry.path,
                        Some(&bytes),
                        "spelling dictionary source differs from its pinned data",
                    ));
                }
                report.subjects.push(subject(
                    &entry.path,
                    "data-verified",
                    "literal correction data, verified by its pinned digest",
                    Some(digest),
                    None,
                ));
            } else if let Some(kind) = binary_kind(&entry.path, &bytes) {
                report.subjects.push(subject(
                    &entry.path,
                    "name-checked",
                    kind,
                    Some(digest),
                    None,
                ));
            } else {
                add_checked(
                    report,
                    scan::content(&project, &dictionary, &entry.path, &bytes)?,
                    &mut words,
                )?;
                report.subjects.push(subject(
                    &entry.path,
                    "checked",
                    "current UTF-8 content and path tokens",
                    Some(digest),
                    None,
                ));
            }
        }
        if visited != required || report.subjects.len() != required.len() {
            return Err(Failure::at(
                "<scan>",
                None,
                "spelling scan did not visit its complete declared source population",
            ));
        }
        for (path, expected) in fingerprints {
            let bytes = read_source(&root, &path)?;
            if sha256(&bytes) != expected {
                return Err(Failure::at(
                    &path,
                    Some(&bytes),
                    "spelling source moved during validation",
                ));
            }
        }
        if git::run(&root, &["ls-files", "--stage", "-z", "--full-name"])? != index {
            return Err(Failure::at(
                "<Git index>",
                None,
                "spelling source population moved during validation",
            ));
        }
    }
    project.verify_sources(&root)?;
    if git::head(&root)? != head {
        return Err(Failure::at(
            "<repository>",
            None,
            "spelling base commit moved during validation",
        ));
    }
    identity::verify(&root.join("tools/dagtoml-spell"))
        .map_err(|message| Failure::at("tools/dagtoml-spell", None, message))?;
    let final_status = git::run(&root, &["status", "--porcelain=v1", "-z"])?;
    report.tree_state = if initial_status.is_empty() && final_status.is_empty() {
        "clean"
    } else {
        "working-files"
    }
    .to_owned();
    finish(report, words)
}

fn main() -> std::process::ExitCode {
    let mut report = Report::new();
    let parsed = options();
    if parsed.as_ref().is_ok_and(|options| options.help) {
        let usage = b"usage: dagtoml-spell [--repo-root PATH] [--stdin NAME] [--identity]\n";
        return if std::io::stdout().write_all(usage).is_ok() {
            std::process::ExitCode::SUCCESS
        } else {
            std::process::ExitCode::from(2)
        };
    }
    if let Err(failure) = parsed.and_then(|options| execute(options, &mut report)) {
        report.fail(failure);
    }
    let status = match report.status.as_str() {
        "no-corrections" | "identity" => 0,
        "findings" => 1,
        _ => 2,
    };
    match toml::to_string_pretty(&report) {
        Ok(text) => {
            if std::io::stdout().write_all(text.as_bytes()).is_err() {
                return std::process::ExitCode::from(2);
            }
        }
        Err(_) => {
            // A closed diagnostic stream does not change the failure exit status.
            let _ = std::io::stderr().write_all(b"spelling result could not be serialized\n");
            return std::process::ExitCode::from(2);
        }
    }
    std::process::ExitCode::from(status)
}
