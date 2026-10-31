//! Evaluate the declared identifier-prefix constraint subset used by this gate.
//! This deliberately has no general SPARQL or SHACL execution interface.

use oxrdf::{Literal, NamedNode, Term, Triple};
use std::collections::BTreeSet;
use std::path::Path;

const DAG: &str = "https://verivus-oss.org/dagtoml/v1#";
const SH: &str = "http://www.w3.org/ns/shacl#";
const RDF_TYPE: &str = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
const RDFS: &str = "http://www.w3.org/2000/01/rdf-schema#";
const CASES: [(&str, &str, &str); 3] = [
    ("Requirement", "RequirementIdPrefixShape", "REQ:"),
    ("Implementation", "ImplementationIdPrefixShape", "IMP:"),
    ("Test", "TestIdPrefixShape", "TEST:"),
];

fn graph(source: &[u8]) -> Result<Vec<Triple>, String> {
    let mut result = Vec::new();
    for item in oxttl::TurtleParser::new().for_slice(source) {
        let triple = item.map_err(|error| format!("invalid Turtle: {}", error.message()))?;
        if !result.contains(&triple) {
            result.push(triple);
        }
    }
    Ok(result)
}

fn objects<'a>(graph: &'a [Triple], subject: &str, predicate: &str) -> Vec<&'a Term> {
    graph
        .iter()
        .filter(|triple| {
            triple.subject.to_string() == subject && triple.predicate.as_str() == predicate
        })
        .map(|triple| &triple.object)
        .collect()
}

fn one<'a>(graph: &'a [Triple], subject: &str, predicate: &str) -> Result<&'a Term, String> {
    let values = objects(graph, subject, predicate);
    match values.as_slice() {
        [value] => Ok(value),
        _ => Err(format!("expected one {predicate} on {subject}")),
    }
}

fn literal(term: &Term) -> Result<&str, String> {
    match term {
        Term::Literal(value)
            if value.datatype().as_str() == "http://www.w3.org/2001/XMLSchema#string" =>
        {
            Ok(value.value())
        }
        _ => Err("expected an untagged string literal".into()),
    }
}

#[derive(Debug, PartialEq)]
enum Token {
    Word(String),
    String(String),
    Punctuation(char),
}

fn tokens(source: &str) -> Result<Vec<Token>, String> {
    let mut input = source.chars().peekable();
    let mut result = Vec::new();
    while let Some(ch) = input.next() {
        if ch.is_ascii_whitespace() {
            continue;
        }
        if ch == '#' {
            for next in input.by_ref() {
                if next == '\n' || next == '\r' {
                    break;
                }
            }
        } else if ch == '"' {
            let mut value = String::new();
            loop {
                match input.next() {
                    Some('"') => break,
                    Some('\\') => match input.next() {
                        Some('"') => value.push('"'),
                        Some('\\') => value.push('\\'),
                        _ => return Err("unsupported escape in prefix constraint".into()),
                    },
                    Some('\n' | '\r') | None => return Err("unterminated prefix string".into()),
                    Some(value_ch) => value.push(value_ch),
                }
            }
            result.push(Token::String(value));
        } else if "{}().!,".contains(ch) {
            result.push(Token::Punctuation(ch));
        } else if ch.is_ascii_alphanumeric() || "$?:_".contains(ch) {
            let mut word = String::from(ch);
            while input
                .peek()
                .is_some_and(|c| c.is_ascii_alphanumeric() || "$?:_".contains(*c))
            {
                word.push(input.next().expect("peeked word character"));
            }
            if let Some(keyword) = ["SELECT", "WHERE", "FILTER", "STRSTARTS", "STR"]
                .iter()
                .find(|keyword| keyword.eq_ignore_ascii_case(&word))
            {
                word = (*keyword).to_owned();
            }
            result.push(Token::Word(word));
        } else {
            return Err("unsupported token in prefix constraint".into());
        }
    }
    Ok(result)
}

fn prefix_query(source: &str) -> Result<String, String> {
    use Token::{Punctuation as P, String as S, Word as W};
    let query = tokens(source)?;
    let prefix = match query.get(19) {
        Some(S(value)) => value.clone(),
        _ => return Err("prefix constraint has no supported prefix expression".into()),
    };
    let expected = vec![
        W("SELECT".into()),
        W("$this".into()),
        W("?value".into()),
        W("WHERE".into()),
        P('{'),
        W("$this".into()),
        W("rdfs:label".into()),
        W("?value".into()),
        P('.'),
        W("FILTER".into()),
        P('('),
        P('!'),
        W("STRSTARTS".into()),
        P('('),
        W("STR".into()),
        P('('),
        W("?value".into()),
        P(')'),
        P(','),
        S(prefix.clone()),
        P(')'),
        P(')'),
        P('}'),
    ];
    if query != expected {
        return Err("unsupported identifier-prefix query; update the bounded evaluator before changing its language".into());
    }
    Ok(prefix)
}

fn violations(data: &[Triple], target: &Term, prefix: &str) -> BTreeSet<(String, String)> {
    let subjects: BTreeSet<String> = data
        .iter()
        .filter(|triple| triple.predicate.as_str() == RDF_TYPE && &triple.object == target)
        .map(|triple| triple.subject.to_string())
        .collect();
    data.iter()
        .filter_map(|triple| {
            if triple.predicate.as_str() != format!("{RDFS}label")
                || !subjects.contains(&triple.subject.to_string())
            {
                return None;
            }
            let value = match &triple.object {
                Term::Literal(value) => value.value(),
                Term::NamedNode(value) => value.as_str(),
                _ => return None,
            };
            (!value.starts_with(prefix)).then(|| (triple.subject.to_string(), value.to_owned()))
        })
        .collect()
}

fn iri(value: &str) -> Result<NamedNode, String> {
    NamedNode::new(value).map_err(|_| "invalid identifier in the prefix control".into())
}

fn supported_properties(graph: &[Triple], subject: &str, allowed: &[String]) -> Result<(), String> {
    if graph.iter().any(|triple| {
        triple.subject.to_string() == subject
            && !allowed.iter().any(|name| name == triple.predicate.as_str())
    }) {
        return Err(format!(
            "unsupported property on identifier-prefix constraint {subject}"
        ));
    }
    Ok(())
}

fn check_graph(shapes: &[Triple]) -> Result<(), String> {
    let expected: BTreeSet<String> = CASES
        .iter()
        .map(|(_, name, _)| format!("<{DAG}{name}>"))
        .collect();
    let declared: BTreeSet<String> = shapes
        .iter()
        .filter(|triple| {
            triple.predicate.as_str() == RDF_TYPE
                && triple.object.to_string() == format!("<{SH}NodeShape>")
                && triple.subject.to_string().ends_with("IdPrefixShape>")
        })
        .map(|triple| triple.subject.to_string())
        .collect();
    if declared != expected {
        return Err("identifier prefix shape population changed".into());
    }
    for (class, name, expected_prefix) in CASES {
        let shape = format!("<{DAG}{name}>");
        supported_properties(
            shapes,
            &shape,
            &[
                RDF_TYPE.to_owned(),
                format!("{SH}targetClass"),
                format!("{SH}sparql"),
            ],
        )?;
        if one(shapes, &shape, RDF_TYPE)?.to_string() != format!("<{SH}NodeShape>") {
            return Err(format!("{name} shape type changed"));
        }
        let target = one(shapes, &shape, &format!("{SH}targetClass"))?;
        if target.to_string() != format!("<{DAG}{class}>") {
            return Err(format!("{name} target class changed"));
        }
        let constraint = one(shapes, &shape, &format!("{SH}sparql"))?.to_string();
        supported_properties(
            shapes,
            &constraint,
            &[
                format!("{SH}message"),
                format!("{SH}prefixes"),
                format!("{SH}select"),
            ],
        )?;
        let source = literal(one(shapes, &constraint, &format!("{SH}select"))?)?;
        let prefix = prefix_query(source)?;
        if prefix != expected_prefix {
            return Err(format!("{name} declared identifier prefix changed"));
        }
        let prefixes = one(shapes, &constraint, &format!("{SH}prefixes"))?.to_string();
        let mut rdfs_namespaces = Vec::new();
        for declaration in objects(shapes, &prefixes, &format!("{SH}declare")) {
            let declaration = declaration.to_string();
            if literal(one(shapes, &declaration, &format!("{SH}prefix"))?)? == "rdfs" {
                let namespace = one(shapes, &declaration, &format!("{SH}namespace"))?;
                if let Term::Literal(value) = namespace {
                    if value.value() == RDFS
                        && value.datatype().as_str() == "http://www.w3.org/2001/XMLSchema#anyURI"
                    {
                        rdfs_namespaces.push(RDFS);
                    } else {
                        return Err("wrong rdfs namespace in prefix constraint".into());
                    }
                } else {
                    return Err("prefix namespace must be an anyURI literal".into());
                }
            }
        }
        if rdfs_namespaces != [RDFS] {
            return Err("expected one rdfs prefix declaration".into());
        }
        // The supported query binds only label triples on the target class,
        // then reports exactly the labels that fail its literal prefix.
        let labels = [
            (format!("{expected_prefix}7"), false),
            (expected_prefix.to_owned(), false),
            (format!("{expected_prefix}ü"), false),
            ("WRONG:7".to_owned(), true),
            (String::new(), true),
            (format!("x{expected_prefix}7"), true),
        ];
        for (label, expected_violation) in labels {
            let subject = iri(&format!("{DAG}control"))?;
            let mut data = vec![
                Triple::new(subject.clone(), iri(RDF_TYPE)?, target.clone()),
                Triple::new(
                    subject.clone(),
                    iri(&format!("{RDFS}label"))?,
                    Literal::new_simple_literal(&label),
                ),
            ];
            let expected_results = if expected_violation {
                BTreeSet::from([(subject.to_string(), label)])
            } else {
                BTreeSet::new()
            };
            if violations(&data, target, &prefix) != expected_results {
                return Err(format!(
                    "{name} prefix query changed the declared graph outcome"
                ));
            }
            data.remove(1);
            if !violations(&data, target, &prefix).is_empty() {
                return Err("missing label created a query binding".into());
            }
            data = vec![
                Triple::new(
                    subject.clone(),
                    iri(RDF_TYPE)?,
                    iri(&format!("{DAG}Unrelated"))?,
                ),
                Triple::new(
                    subject,
                    iri(&format!("{RDFS}label"))?,
                    Literal::new_simple_literal("WRONG:7"),
                ),
            ];
            if !violations(&data, target, &prefix).is_empty() {
                return Err("prefix constraint applied to an unrelated class".into());
            }
        }
    }
    Ok(())
}

pub fn check(root: &Path) -> Result<(), String> {
    let path = root.join("reference/database/rdf/shapes.ttl");
    let source = std::fs::read(&path).map_err(|error| format!("cannot read {path:?}: {error}"))?;
    check_graph(&graph(&source)?)
}

#[cfg(test)]
mod tests {
    use super::*;

    const SHAPES: &str = include_str!("../../../reference/database/rdf/shapes.ttl");

    #[test]
    fn current_shapes_and_query_failures() {
        check_graph(&graph(SHAPES.as_bytes()).unwrap()).unwrap();
        for (old, new) in [
            ("STRSTARTS", "STRENDS"),
            ("!STRSTARTS", "STRSTARTS"),
            ("\"REQ:\"", "\"OTHER:\""),
            (
                "sh:targetClass dagtoml:Requirement",
                "sh:targetClass dagtoml:Test",
            ),
            (
                "http://www.w3.org/2000/01/rdf-schema#",
                "https://invalid.example/rdfs#",
            ),
            (
                "dagtoml:RequirementIdPrefixShape a sh:NodeShape ;",
                "dagtoml:RequirementIdPrefixShape a sh:NodeShape ; sh:deactivated true ;",
            ),
            (
                "dagtoml:RequirementIdPrefixShape a sh:NodeShape ;",
                "dagtoml:RequirementIdPrefixShape a sh:NodeShape, sh:PropertyShape ;",
            ),
            ("sh:select \"\"\"", "sh:deactivated true ; sh:select \"\"\""),
        ] {
            assert!(SHAPES.contains(old), "mutation subject must exist: {old}");
            let changed = SHAPES.replace(old, new);
            assert!(
                check_graph(&graph(changed.as_bytes()).unwrap()).is_err(),
                "mutation: {old} -> {new}"
            );
        }
        assert!(check_graph(&[]).is_err());
        assert!(graph(b"this is not Turtle").is_err());
        let duplicate = format!(
            "{SHAPES}\n dagtoml:RequirementIdPrefixShape sh:targetClass dagtoml:Requirement ."
        );
        check_graph(&graph(duplicate.as_bytes()).unwrap()).unwrap();
        let keyword_case = SHAPES.replace("SELECT", "select").replace("WHERE", "where");
        check_graph(&graph(keyword_case.as_bytes()).unwrap()).unwrap();
    }
}
