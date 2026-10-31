use std::collections::{BTreeMap, BTreeSet};
use std::ops::Range;
use std::path::Path;

use serde::Deserialize;
use toml::Spanned;

use crate::data_spans::{Container, python_byte_literals, python_table};
use crate::digest::sha256;
use crate::tokens::Case;

const CATALOG: &str = "validators/credential-rule-population.toml";
const POLICY: &str = "tools/dagtoml-spell/data/project.toml";
const STOPWORDS: &str = "validators/_credential_words.py";
const STRUCTURES: &str = "validators/_credential_structures.py";
const CONTROLS: &str = "validators/_credential_controls.py";
const FIXTURES: &str = "tools/dagtoml-spell/tests/fixtures/corrections.toml";

#[derive(Debug)]
pub struct Failure {
    pub path: String,
    pub source_sha256: Option<String>,
    pub byte_span: Option<Range<usize>>,
    pub message: &'static str,
}

impl Failure {
    pub fn at(path: &str, source: Option<&[u8]>, message: &'static str) -> Self {
        Self {
            path: path.to_owned(),
            source_sha256: source.map(sha256),
            byte_span: None,
            message,
        }
    }
}

pub fn read_source(root: &Path, relative: &str) -> Result<Vec<u8>, Failure> {
    crate::scope::classify(relative).map_err(|message| Failure::at(relative, None, message))?;
    let path = root.join(relative);
    let metadata = std::fs::symlink_metadata(&path)
        .map_err(|_| Failure::at(relative, None, "spelling source cannot be inspected"))?;
    if !metadata.file_type().is_file() || metadata.file_type().is_symlink() {
        return Err(Failure::at(
            relative,
            None,
            "spelling source must be a regular file",
        ));
    }
    let resolved = path
        .canonicalize()
        .map_err(|_| Failure::at(relative, None, "spelling source cannot be resolved"))?;
    let root = root
        .canonicalize()
        .map_err(|_| Failure::at(relative, None, "spelling repository root is unavailable"))?;
    if !resolved.starts_with(root) {
        return Err(Failure::at(
            relative,
            None,
            "spelling source is outside its repository root",
        ));
    }
    std::fs::read(resolved)
        .map_err(|_| Failure::at(relative, None, "spelling source bytes are unavailable"))
}

fn text<'a>(path: &str, source: &'a [u8]) -> Result<&'a str, Failure> {
    std::str::from_utf8(source).map_err(|error| {
        let mut failure = Failure::at(path, Some(source), "spelling source is not UTF-8");
        let start = error.valid_up_to();
        failure.byte_span = Some(start..start + error.error_len().unwrap_or(source.len() - start));
        failure
    })
}

fn document<T: serde::de::DeserializeOwned>(path: &str, source: &[u8]) -> Result<T, Failure> {
    toml::from_str(text(path, source)?).map_err(|error: toml::de::Error| {
        let mut failure = Failure::at(
            path,
            Some(source),
            "spelling data has an unsupported TOML structure",
        );
        failure.byte_span = error.span();
        failure
    })
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct PolicyData {
    schema_version: u32,
    source_commit: String,
    catalog_sha256: String,
    stopwords_operand_sha256: String,
    headers_operand_sha256: String,
    provider_byte_literal: Spanned<String>,
    words: BTreeMap<String, String>,
    identifiers: BTreeMap<String, String>,
}

fn valid_identifiers(values: &BTreeMap<String, String>) -> bool {
    !values.is_empty()
        && values.iter().all(|(key, value)| {
            key == value
                && key
                    .as_bytes()
                    .first()
                    .is_some_and(|byte| byte.is_ascii_alphabetic() || *byte == b'_')
                && key
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
        })
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CatalogData {
    source_revision: String,
    rule_ids: Vec<String>,
}

pub struct Project {
    pub accepted_words: Vec<String>,
    pub accepted_identifiers: Vec<String>,
    names: Vec<String>,
    fixed_spans: BTreeMap<String, (String, Vec<Range<usize>>)>,
    source_hashes: BTreeMap<String, String>,
}

impl Project {
    pub fn load(root: &Path) -> Result<Self, Failure> {
        let policy_bytes = read_source(root, POLICY)?;
        let policy: PolicyData = document(POLICY, &policy_bytes)?;
        if policy.schema_version != 1
            || policy.source_commit.len() != 40
            || !policy
                .source_commit
                .bytes()
                .all(|byte| byte.is_ascii_hexdigit())
            || policy.words.is_empty()
            || !valid_identifiers(&policy.identifiers)
            || policy.provider_byte_literal.get_ref().is_empty()
            || policy
                .words
                .iter()
                .any(|(key, value)| key.is_empty() || key != value)
        {
            return Err(Failure::at(
                POLICY,
                Some(&policy_bytes),
                "spelling project policy operands are invalid",
            ));
        }
        let catalog_bytes = read_source(root, CATALOG)?;
        if sha256(&catalog_bytes) != policy.catalog_sha256 {
            return Err(Failure::at(
                CATALOG,
                Some(&catalog_bytes),
                "spelling identity catalog differs from its pinned data",
            ));
        }
        let catalog: CatalogData = document(CATALOG, &catalog_bytes)?;
        let distinct: BTreeSet<_> = catalog.rule_ids.iter().collect();
        if catalog.source_revision != "../requirements/credential-source-revision.toml"
            || catalog.rule_ids.is_empty()
            || distinct.len() != catalog.rule_ids.len()
            || catalog.rule_ids.iter().any(|name| {
                name.is_empty()
                    || !name
                        .bytes()
                        .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
            })
        {
            return Err(Failure::at(
                CATALOG,
                Some(&catalog_bytes),
                "spelling identity catalog has invalid literal names",
            ));
        }
        let mut fixed_spans = BTreeMap::new();
        fixed_spans.insert(
            POLICY.to_owned(),
            (
                sha256(&policy_bytes),
                vec![policy.provider_byte_literal.span()],
            ),
        );
        for (path, binding, container, expected) in [
            (
                STOPWORDS,
                "GENERIC_STOPWORDS",
                Container::FrozenSet,
                policy.stopwords_operand_sha256,
            ),
            (
                STRUCTURES,
                "JWT_HEADER_PREFIXES",
                Container::Tuple,
                policy.headers_operand_sha256,
            ),
        ] {
            let bytes = read_source(root, path)?;
            let table = python_table(text(path, &bytes)?, binding, container)
                .map_err(|message| Failure::at(path, Some(&bytes), message))?;
            if table
                .digest()
                .map_err(|message| Failure::at(path, Some(&bytes), message))?
                != expected
            {
                return Err(Failure::at(
                    path,
                    Some(&bytes),
                    "spelling byte-table operands differ from their pinned data",
                ));
            }
            fixed_spans.insert(path.to_owned(), (sha256(&bytes), table.spans));
        }
        for path in [STRUCTURES, CONTROLS] {
            let bytes = read_source(root, path)?;
            let spans = python_byte_literals(
                text(path, &bytes)?,
                std::slice::from_ref(policy.provider_byte_literal.get_ref()),
            )
            .map_err(|message| Failure::at(path, Some(&bytes), message))?;
            let entry = fixed_spans
                .entry(path.to_owned())
                .or_insert((sha256(&bytes), Vec::new()));
            entry.1.extend(spans);
        }
        let bytes = read_source(root, FIXTURES)?;
        fixed_spans.insert(
            FIXTURES.to_owned(),
            (sha256(&bytes), correction_fixture_spans(&bytes)?),
        );
        let mut source_hashes: BTreeMap<_, _> = fixed_spans
            .iter()
            .map(|(path, (digest, _))| (path.clone(), digest.clone()))
            .collect();
        source_hashes.insert(POLICY.to_owned(), sha256(&policy_bytes));
        source_hashes.insert(CATALOG.to_owned(), sha256(&catalog_bytes));
        Ok(Self {
            accepted_words: policy.words.into_keys().collect(),
            accepted_identifiers: policy.identifiers.into_keys().collect(),
            names: catalog.rule_ids,
            fixed_spans,
            source_hashes,
        })
    }

    pub fn identifier_is_accepted(&self, identifier: &str) -> bool {
        self.accepted_identifiers
            .iter()
            .any(|item| item == identifier)
    }

    pub fn verify_sources(&self, root: &Path) -> Result<(), Failure> {
        for (path, expected) in &self.source_hashes {
            let bytes = read_source(root, path)?;
            if sha256(&bytes) != *expected {
                return Err(Failure::at(
                    path,
                    Some(&bytes),
                    "spelling project source moved during validation",
                ));
            }
        }
        Ok(())
    }

    pub fn source_hashes(&self) -> &BTreeMap<String, String> {
        &self.source_hashes
    }

    pub fn spans(&self, path: &str, bytes: &[u8]) -> Result<Vec<Range<usize>>, Failure> {
        let mut spans = if let Some((digest, spans)) = self.fixed_spans.get(path) {
            if *digest != sha256(bytes) {
                return Err(Failure::at(
                    path,
                    Some(bytes),
                    "spelling data source moved after validation",
                ));
            }
            spans.clone()
        } else {
            Vec::new()
        };
        let source = text(path, bytes)?;
        spans.extend(self.catalog_spans(source));
        if spans
            .iter()
            .any(|span| span.start >= span.end || span.end > bytes.len())
        {
            return Err(Failure::at(
                path,
                Some(bytes),
                "spelling data returned an invalid source interval",
            ));
        }
        spans.sort_by_key(|span| (span.start, span.end));
        Ok(spans)
    }

    pub fn catalog_spans(&self, source: &str) -> Vec<Range<usize>> {
        let mut spans = Vec::new();
        let boundary =
            |character: char| unicode_ident::is_xid_continue(character) || character == '-';
        for name in &self.names {
            for (start, matched) in source.match_indices(name.as_str()) {
                let end = start + matched.len();
                if source[..start].chars().next_back().is_some_and(boundary)
                    || source[end..].chars().next().is_some_and(boundary)
                {
                    continue;
                }
                spans.push(start..end);
            }
        }
        spans
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CorrectionCorpus {
    role: String,
    corrections: Vec<CorrectionCase>,
    accepted: Vec<AcceptedCase>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CorrectionCase {
    name: String,
    input: Spanned<String>,
    case: Case,
    expected: Vec<Spanned<String>>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct AcceptedCase {
    input: Spanned<String>,
    case: Case,
}

fn correction_fixture_spans(source: &[u8]) -> Result<Vec<Range<usize>>, Failure> {
    let corpus: CorrectionCorpus = document(FIXTURES, source)?;
    if corpus.role != "spelling-correction-controls"
        || corpus.corrections.is_empty()
        || corpus.accepted.is_empty()
    {
        return Err(Failure::at(
            FIXTURES,
            Some(source),
            "spelling correction controls are absent or unsupported",
        ));
    }
    let mut names = BTreeSet::new();
    let mut spans = Vec::new();
    for case in corpus.corrections {
        if case.name.is_empty()
            || !names.insert(case.name)
            || case.input.get_ref().is_empty()
            || case.expected.is_empty()
            || case.expected.iter().any(|value| value.get_ref().is_empty())
            || case.case == Case::None
        {
            return Err(Failure::at(
                FIXTURES,
                Some(source),
                "spelling correction control has invalid operands",
            ));
        }
        spans.push(case.input.span());
        spans.extend(case.expected.into_iter().map(|value| value.span()));
    }
    for case in corpus.accepted {
        if case.input.get_ref().is_empty()
            || (case.case == Case::None
                && !case
                    .input
                    .get_ref()
                    .bytes()
                    .all(|byte| byte.is_ascii_digit()))
        {
            return Err(Failure::at(
                FIXTURES,
                Some(source),
                "spelling accepted control has invalid operands",
            ));
        }
        spans.push(case.input.span());
    }
    Ok(spans)
}

#[cfg(test)]
mod tests {
    use super::{
        CorrectionCorpus, FIXTURES, correction_fixture_spans, document, valid_identifiers,
    };
    use crate::data_spans::contains;

    #[test]
    fn identifier_policy_accepts_exact_names_and_rejects_invalid_roles() {
        use std::collections::BTreeMap;
        assert!(!valid_identifiers(&BTreeMap::new()));
        for name in ["NdArray", "_Value2", "O_WRONLY"] {
            assert!(valid_identifiers(&BTreeMap::from([(
                name.to_owned(),
                name.to_owned()
            )])));
        }
        for (key, value) in [
            ("", ""),
            ("1Value", "1Value"),
            ("two words", "two words"),
            ("Type::Value", "Type::Value"),
            ("Value", "Other"),
        ] {
            assert!(!valid_identifiers(&BTreeMap::from([(
                key.to_owned(),
                value.to_owned()
            )])));
        }
    }

    #[test]
    fn fixture_inputs_are_data_and_adjacent_comments_stay_governed() {
        let original = include_bytes!("../tests/fixtures/corrections.toml");
        let corpus: CorrectionCorpus = document(FIXTURES, original).unwrap();
        let sample = corpus
            .corrections
            .iter()
            .find(|case| case.name == "lowercase-receive")
            .unwrap()
            .input
            .get_ref();
        let mut source = original.to_vec();
        source.extend_from_slice(b"\n# ordinary adjacent prose: ");
        let start = source.len();
        source.extend_from_slice(sample.as_bytes());
        source.push(b'\n');
        let spans = correction_fixture_spans(&source).unwrap();
        assert!(!spans.is_empty());
        assert!(!contains(&spans, start, start + sample.len()));
        let first = corpus.corrections[0].input.span();
        assert!(contains(&spans, first.start, first.end));
        assert!(
            correction_fixture_spans(
                b"role='spelling-correction-controls'\ncorrections=[]\naccepted=[]\n"
            )
            .is_err()
        );
        let mut unknown = original.to_vec();
        unknown.extend_from_slice(b"\nunknown_property = true\n");
        assert!(correction_fixture_spans(&unknown).is_err());
    }
}
