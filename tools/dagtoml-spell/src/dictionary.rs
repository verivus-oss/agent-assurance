use crate::digest::sha256;
use unicase::UniCase;

use crate::tokens::{Case, Word};

pub const SOURCE_SHA256: &str = "a13ac44993f5f85724161107172b3bd5a69afefe784912b094497129939b001c";
const SOURCE: &str = include_str!("../data/words.csv");

pub struct Dictionary {
    entries: Vec<(&'static str, Vec<&'static str>)>,
    accepted: Vec<String>,
}

impl Dictionary {
    pub fn pinned(accepted: Vec<String>) -> Result<Self, &'static str> {
        let mut dictionary = Self::from_source(SOURCE, SOURCE_SHA256)?;
        if accepted.iter().any(String::is_empty) {
            return Err("spelling word acceptance must identify a nonempty literal");
        }
        dictionary.accepted = accepted;
        Ok(dictionary)
    }

    fn from_source(source: &'static str, expected: &str) -> Result<Self, &'static str> {
        if sha256(source.as_bytes()) != expected {
            return Err("spelling dictionary digest differs from the pinned supplier data");
        }
        if source.is_empty() || !source.ends_with('\n') || source.contains(['\r', '"', '\t']) {
            return Err("spelling dictionary has an unsupported literal record format");
        }
        let mut entries = Vec::new();
        for record in source.split_terminator('\n') {
            let mut fields = record.split(',');
            let key = fields
                .next()
                .ok_or("spelling dictionary record is absent")?;
            if key.is_empty() {
                return Err("spelling dictionary has an empty lookup identity");
            }
            let values: Vec<_> = fields.collect();
            if values.iter().any(|value| value.is_empty()) {
                return Err("spelling dictionary has an empty correction operand");
            }
            entries.push((key, values));
        }
        if entries.is_empty() {
            return Err("spelling dictionary has no literal records");
        }
        entries.sort_by(|(a, _), (b, _)| UniCase::new(*a).cmp(&UniCase::new(*b)));
        if entries
            .windows(2)
            .any(|pair| UniCase::new(pair[0].0) == UniCase::new(pair[1].0))
        {
            return Err("spelling dictionary repeats a case-folded identity");
        }
        Ok(Self {
            entries,
            accepted: Vec::new(),
        })
    }

    fn raw(&self, word: &str) -> Option<&[&'static str]> {
        let position = self
            .entries
            .binary_search_by(|(key, _)| UniCase::new(*key).cmp(&UniCase::new(word)))
            .ok()?;
        Some(&self.entries[position].1)
    }

    pub fn identifier_is_accepted(identifier: &str) -> bool {
        // Preserve exact supplier compression identities without accepting
        // their component word or longer surrounding identifiers.
        matches!(identifier, "O_WRONLY" | "dBA" | "HashiCorp" | "flate2")
    }

    pub fn correct(&self, word: Word<'_>) -> Option<Vec<String>> {
        if word.case == Case::None
            || self
                .accepted
                .iter()
                .any(|item| UniCase::new(item.as_str()) == UniCase::new(word.text))
        {
            return None;
        }
        self.raw(word.text).map(|values| {
            values
                .iter()
                .map(|value| match word.case {
                    Case::Lower | Case::None => (*value).to_owned(),
                    Case::Upper => value.to_uppercase(),
                    Case::Title => {
                        let mut characters = value.chars();
                        let mut result = String::new();
                        if let Some(first) = characters.next() {
                            result.extend(first.to_uppercase());
                        }
                        result.push_str(characters.as_str());
                        result
                    }
                })
                .collect()
        })
    }
}

#[cfg(test)]
mod tests {
    use super::{Dictionary, SOURCE_SHA256};
    use crate::digest::sha256;
    use crate::tokens::{Case, Word};

    fn word(text: &str, case: Case) -> Word<'_> {
        Word {
            text,
            start: 0,
            end: text.len(),
            case,
        }
    }

    #[test]
    fn independently_declared_corrections_and_case() {
        let dictionary = Dictionary::pinned(vec!["COSE".to_owned()]).unwrap();
        #[derive(serde::Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Corpus {
            role: String,
            corrections: Vec<Correction>,
            accepted: Vec<Accepted>,
        }
        #[derive(serde::Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Correction {
            name: String,
            input: String,
            case: Case,
            expected: Vec<String>,
        }
        #[derive(serde::Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Accepted {
            input: String,
            case: Case,
        }
        let corpus: Corpus =
            toml::from_str(include_str!("../tests/fixtures/corrections.toml")).unwrap();
        assert_eq!(corpus.role, "spelling-correction-controls");
        assert!(!corpus.corrections.is_empty() && !corpus.accepted.is_empty());
        let mut names = std::collections::BTreeSet::new();
        for case in corpus.corrections {
            assert!(!case.name.is_empty() && names.insert(case.name));
            assert!(!case.input.is_empty() && !case.expected.is_empty());
            assert_eq!(
                dictionary.correct(word(&case.input, case.case)),
                Some(case.expected)
            );
        }
        for case in corpus.accepted {
            assert!(!case.input.is_empty());
            assert_eq!(dictionary.correct(word(&case.input, case.case)), None);
        }
        for identifier in ["O_WRONLY", "dBA", "HashiCorp", "flate2"] {
            assert!(Dictionary::identifier_is_accepted(identifier));
            assert!(!Dictionary::identifier_is_accepted(&format!(
                "{identifier}Other"
            )));
        }
        let component = "flate2".strip_suffix('2').unwrap();
        assert!(!Dictionary::identifier_is_accepted(component));
        assert!(dictionary.correct(word(component, Case::Lower)).is_some());
        let accepted = "HashiCorp";
        assert!(!Dictionary::identifier_is_accepted(&format!(
            "{accepted}Other"
        )));
        assert!(Dictionary::pinned(vec![String::new()]).is_err());
    }

    #[test]
    fn absent_stale_malformed_and_duplicate_data_fail() {
        assert!(Dictionary::from_source("word,correction\n", SOURCE_SHA256).is_err());
        for source in [
            "",
            "word,correction",
            "word,correction\r\n",
            "word,\"correction\"\n",
            "word,\n",
            ",correction\n",
            "word,correction\nword,correction\n",
            "Word,correction\nword,correction\n",
        ] {
            let digest = sha256(source.as_bytes());
            assert!(
                Dictionary::from_source(source, &digest).is_err(),
                "invalid dictionary accepted: {source:?}"
            );
        }
        let source = "forbiddenterm\n";
        let digest = sha256(source.as_bytes());
        let dictionary = Dictionary::from_source(source, &digest).unwrap();
        assert_eq!(
            dictionary.correct(word("forbiddenterm", Case::Lower)),
            Some(vec![])
        );
    }

    #[test]
    fn every_pinned_literal_record_has_its_declared_lookup() {
        let dictionary = Dictionary::pinned(Vec::new()).unwrap();
        let mut required = std::collections::BTreeSet::new();
        let mut visited = std::collections::BTreeSet::new();
        for record in super::SOURCE.split_terminator('\n') {
            let (key, tail) = record.split_once(',').unwrap_or((record, ""));
            assert!(!key.is_empty() && required.insert(key));
            let expected: Vec<_> = if tail.is_empty() {
                Vec::new()
            } else {
                tail.split(',').collect()
            };
            assert_eq!(dictionary.raw(key), Some(expected.as_slice()));
            assert!(visited.insert(key));
        }
        assert!(!required.is_empty());
        assert_eq!(visited, required);
        assert_eq!(dictionary.entries.len(), required.len());
    }
}
