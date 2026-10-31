use serde::Serialize;

use crate::data_spans::contains;
use crate::dictionary::Dictionary;
use crate::digest::sha256;
use crate::project::{Failure, Project};
use crate::tokens::{Case, identifiers, words};

pub const RULE_VERSION: &str = "spelling-literal-corrections-v1";

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
pub struct Finding {
    pub path: String,
    pub source_kind: String,
    pub source_sha256: String,
    pub byte_span: [usize; 2],
    pub token: String,
    pub corrections: Vec<String>,
    pub rule_version: String,
}

pub struct Checked {
    pub findings: Vec<Finding>,
    pub checked_words: usize,
    pub source_sha256: String,
}

fn inspect(
    project: &Project,
    dictionary: &Dictionary,
    path: &str,
    source: &str,
    kind: &str,
) -> Result<Checked, Failure> {
    let bytes = source.as_bytes();
    let digest = sha256(bytes);
    let spans = if kind == "content" {
        project.spans(path, bytes)?
    } else {
        project.catalog_spans(source)
    };
    let mut findings = Vec::new();
    let mut checked_words = 0usize;
    for identifier in
        identifiers(source).map_err(|message| Failure::at(path, Some(bytes), message))?
    {
        if project.identifier_is_accepted(identifier.text) {
            continue;
        }
        for word in words(identifier).map_err(|message| Failure::at(path, Some(bytes), message))? {
            if word.case == Case::None || contains(&spans, word.start, word.end) {
                continue;
            }
            checked_words = checked_words.checked_add(1).ok_or_else(|| {
                Failure::at(path, Some(bytes), "spelling word population overflow")
            })?;
            if let Some(corrections) = dictionary.correct(word) {
                if source.get(word.start..word.end) != Some(word.text) {
                    return Err(Failure::at(
                        path,
                        Some(bytes),
                        "spelling finding has an invalid source pointer",
                    ));
                }
                findings.push(Finding {
                    path: path.to_owned(),
                    source_kind: kind.to_owned(),
                    source_sha256: digest.clone(),
                    byte_span: [word.start, word.end],
                    token: word.text.to_owned(),
                    corrections,
                    rule_version: RULE_VERSION.to_owned(),
                });
            }
        }
    }
    Ok(Checked {
        findings,
        checked_words,
        source_sha256: digest,
    })
}

pub fn content(
    project: &Project,
    dictionary: &Dictionary,
    path: &str,
    source: &[u8],
) -> Result<Checked, Failure> {
    if let Some(position) = source.iter().position(|byte| *byte == 0) {
        let mut failure = Failure::at(
            path,
            Some(source),
            "spelling text has an unclassified binary control byte",
        );
        failure.byte_span = Some(position..position + 1);
        return Err(failure);
    }
    let source = std::str::from_utf8(source).map_err(|error| {
        let mut failure = Failure::at(path, Some(source), "spelling text source is not UTF-8");
        let start = error.valid_up_to();
        failure.byte_span = Some(start..start + error.error_len().unwrap_or(source.len() - start));
        failure
    })?;
    inspect(project, dictionary, path, source, "content")
}

pub fn filename(
    project: &Project,
    dictionary: &Dictionary,
    path: &str,
) -> Result<Checked, Failure> {
    crate::scope::classify(path)
        .map_err(|message| Failure::at(path, Some(path.as_bytes()), message))?;
    inspect(project, dictionary, path, path, "path")
}
