#![forbid(unsafe_code)]

use dagtoml_spell::data_spans::{Container, contains, python_table};
use dagtoml_spell::dictionary::Dictionary;
use dagtoml_spell::project::{Project, read_source};
use dagtoml_spell::tokens::{identifiers, words};
use std::path::PathBuf;

fn root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .to_owned()
}

#[test]
fn current_data_agrees_with_independent_ast_operand_answers() {
    let root = root();
    let project = Project::load(&root).unwrap();
    let facts = [
        (
            "validators/_credential_words.py",
            "GENERIC_STOPWORDS",
            Container::FrozenSet,
            "ba744bd6fa659705d11a073fe32a1c6d1d1c7c78d4664b18228d1d18f5f9faca",
        ),
        (
            "validators/_credential_structures.py",
            "JWT_HEADER_PREFIXES",
            Container::Tuple,
            "3173f991f1c13bb771d12ef39c09a5571cec22c67a32c5986bd5d2c46292d526",
        ),
    ];
    for (path, binding, container, expected) in facts {
        let bytes = read_source(&root, path).unwrap();
        let source = std::str::from_utf8(&bytes).unwrap();
        let table = python_table(source, binding, container).unwrap();
        assert_eq!(table.digest().unwrap(), expected);
        assert_eq!(table.values.len(), table.spans.len());
        assert!(!table.values.is_empty());
        for (value, span) in table.values.iter().zip(&table.spans) {
            assert!(source[span.clone()].contains(value));
        }
        let spans = project.spans(path, &bytes).unwrap();
        for span in &table.spans {
            assert!(contains(&spans, span.start, span.end));
        }
    }
    let bytes = read_source(&root, "validators/_credential_words.py").unwrap();
    let source = std::str::from_utf8(&bytes).unwrap();
    let start = source.find("Pinned literal").unwrap();
    assert!(!contains(
        &project
            .spans("validators/_credential_words.py", &bytes)
            .unwrap(),
        start,
        start + "Pinned literal".len()
    ));
}

#[test]
fn supplier_identity_does_not_exempt_neighboring_prose() {
    #[derive(serde::Deserialize)]
    struct Corpus {
        corrections: Vec<Control>,
    }
    #[derive(serde::Deserialize)]
    struct Control {
        name: String,
        input: String,
        expected: Vec<String>,
    }
    let corpus: Corpus = toml::from_str(include_str!("fixtures/corrections.toml")).unwrap();
    let control = corpus
        .corrections
        .into_iter()
        .find(|case| case.name == "lowercase-receive")
        .unwrap();
    let project = Project::load(&root()).unwrap();
    let dictionary = Dictionary::pinned(project.accepted_words.clone()).unwrap();
    let catalog_name = "airtable-personnal-access-token";
    let source = format!("ordinary '{catalog_name}' {} ordinary", control.input);
    let spans = project.spans("sample.md", source.as_bytes()).unwrap();
    let start = source.find(catalog_name).unwrap();
    assert!(contains(&spans, start, start + catalog_name.len()));
    let outside = source.find(&control.input).unwrap();
    assert!(!contains(&spans, outside, outside + control.input.len()));
    let mut findings = Vec::new();
    for identifier in identifiers(&source).unwrap() {
        for word in words(identifier).unwrap() {
            if !contains(&spans, word.start, word.end) {
                if let Some(corrections) = dictionary.correct(word) {
                    findings.push((word.text, corrections));
                }
            }
        }
    }
    assert_eq!(findings, vec![(control.input.as_str(), control.expected)]);
    let lookalike = format!("prefix-{catalog_name}-suffix");
    assert!(
        project
            .spans("sample.md", lookalike.as_bytes())
            .unwrap()
            .is_empty()
    );
}

#[test]
fn moved_data_source_is_rejected() {
    let project = Project::load(&root()).unwrap();
    project.verify_sources(&root()).unwrap();
    let path = "validators/_credential_words.py";
    let mut source = read_source(&root(), path).unwrap();
    source.extend_from_slice(b"\n# ordinary additional prose\n");
    assert!(project.spans(path, &source).is_err());
}
