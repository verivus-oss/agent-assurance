use std::collections::BTreeMap;

use serde::Deserialize;
use serde::de::{IgnoredAny, MapAccess, Visitor};

use crate::{
    locks::canonical_python_name,
    model::{Ecosystem, Package},
    versions::{self, EventKind},
};

#[derive(Deserialize)]
pub struct Record {
    pub id: String,
    pub modified: String,
    #[serde(default, deserialize_with = "present_string")]
    pub schema_version: Option<String>,
    #[serde(default, deserialize_with = "present_string")]
    withdrawn: Option<String>,
    #[serde(default)]
    pub affected: Vec<Affected>,
    #[serde(flatten)]
    _metadata: BTreeMap<String, IgnoredAny>,
}

fn present_string<'de, D: serde::Deserializer<'de>>(
    deserializer: D,
) -> Result<Option<String>, D::Error> {
    String::deserialize(deserializer).map(Some)
}

fn timestamp(value: &str) -> bool {
    fn number(value: &[u8]) -> Option<u32> {
        if value.is_empty() || !value.iter().all(u8::is_ascii_digit) {
            return None;
        }
        value
            .iter()
            .try_fold(0, |total, byte| Some(total * 10 + u32::from(byte - b'0')))
    }
    let b = value.as_bytes();
    if b.len() < 20
        || b[4] != b'-'
        || b[7] != b'-'
        || !matches!(b[10], b'T' | b't')
        || b[13] != b':'
        || b[16] != b':'
    {
        return false;
    }
    let (Some(year), Some(month), Some(day), Some(hour), Some(minute), Some(second)) = (
        number(&b[..4]),
        number(&b[5..7]),
        number(&b[8..10]),
        number(&b[11..13]),
        number(&b[14..16]),
        number(&b[17..19]),
    ) else {
        return false;
    };
    let days = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if year % 4 == 0 && (year % 100 != 0 || year % 400 == 0) => 29,
        2 => 28,
        _ => 0,
    };
    if year == 0 || day == 0 || day > days || hour > 23 || minute > 59 || second > 59 {
        return false;
    }
    let mut index = 19;
    if b[index] == b'.' {
        index += 1;
        let start = index;
        while b.get(index).is_some_and(u8::is_ascii_digit) {
            index += 1;
        }
        if index == start {
            return false;
        }
    }
    let tail = &b[index..];
    matches!(tail, [b'Z' | b'z'])
        || (tail.len() == 6
            && matches!(tail[0], b'+' | b'-')
            && tail[3] == b':'
            && number(&tail[1..3]).is_some_and(|value| value <= 23)
            && number(&tail[4..6]).is_some_and(|value| value <= 59))
}

#[derive(Deserialize)]
pub struct Affected {
    #[serde(default)]
    pub package: Option<Name>,
    #[serde(default)]
    ranges: Vec<Range>,
    #[serde(default)]
    versions: Vec<String>,
    #[serde(flatten)]
    _metadata: BTreeMap<String, IgnoredAny>,
}

#[derive(Deserialize)]
pub struct Name {
    pub ecosystem: String,
    pub name: String,
    #[serde(flatten)]
    _metadata: BTreeMap<String, IgnoredAny>,
}

#[derive(Deserialize)]
struct Range {
    #[serde(rename = "type")]
    kind: String,
    #[serde(default)]
    events: Vec<RawEvent>,
    #[serde(flatten)]
    _metadata: BTreeMap<String, IgnoredAny>,
}

struct RawEvent(Vec<(String, String)>);

impl<'de> Deserialize<'de> for RawEvent {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct EventVisitor;
        impl<'de> Visitor<'de> for EventVisitor {
            type Value = RawEvent;
            fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
                formatter.write_str("one typed advisory event")
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
                let mut values = Vec::new();
                while let Some(pair) = map.next_entry::<String, String>()? {
                    values.push(pair);
                }
                Ok(RawEvent(values))
            }
        }
        deserializer.deserialize_map(EventVisitor)
    }
}

pub fn label(ecosystem: &Ecosystem) -> &'static str {
    match ecosystem {
        Ecosystem::Go => "Go",
        Ecosystem::PyPI => "PyPI",
        Ecosystem::Crates => "crates.io",
    }
}

pub fn name_key(ecosystem: &Ecosystem, name: &str) -> Option<String> {
    match ecosystem {
        Ecosystem::PyPI => canonical_python_name(name),
        Ecosystem::Crates => {
            if name.is_empty()
                || !name
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || b"-_".contains(&byte))
            {
                return None;
            }
            Some(name.to_ascii_lowercase().replace('_', "-"))
        }
        Ecosystem::Go => {
            if name.is_empty()
                || name.len() > 1024
                || !name
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || b"./_-~".contains(&byte))
                || name
                    .split('/')
                    .any(|part| part.is_empty() || matches!(part, "." | ".."))
            {
                return None;
            }
            Some(name.to_owned())
        }
    }
}

fn identity(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 256
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || b":-_.".contains(&byte))
}

impl Record {
    pub fn parse(source: &[u8]) -> Result<Self, String> {
        let record: Self =
            serde_json::from_slice(source).map_err(|_| "invalid advisory JSON structure")?;
        if !identity(&record.id)
            || !timestamp(&record.modified)
            || record
                .withdrawn
                .as_ref()
                .is_some_and(|value| !timestamp(value))
            || record.schema_version.as_ref().is_some_and(|value| {
                !semver::Version::parse(value)
                    .is_ok_and(|version| version.major == 1 && version.pre.is_empty())
            })
        {
            return Err("invalid advisory identity, modification or schema version".into());
        }
        Ok(record)
    }

    pub fn unparsable_package_names(&self) -> usize {
        self.affected
            .iter()
            .filter_map(|affected| affected.package.as_ref())
            .filter(|name| {
                let ecosystem = match name.ecosystem.as_str() {
                    "PyPI" => Ecosystem::PyPI,
                    "Go" => Ecosystem::Go,
                    "crates.io" => Ecosystem::Crates,
                    _ => return false,
                };
                name_key(&ecosystem, &name.name).is_none()
            })
            .count()
    }

    pub fn applies(&self, package: &Package) -> bool {
        let Some(query) = name_key(&package.ecosystem, &package.name) else {
            return false;
        };
        self.affected.iter().any(|affected| {
            affected.package.as_ref().is_some_and(|name| {
                name.ecosystem == label(&package.ecosystem)
                    && name_key(&package.ecosystem, &name.name).as_ref() == Some(&query)
            })
        })
    }

    pub fn commit_ranges_outside_subject(&self, package: &Package) -> usize {
        let query = name_key(&package.ecosystem, &package.name);
        self.affected
            .iter()
            .filter(|affected| {
                affected.package.as_ref().is_some_and(|name| {
                    name.ecosystem == label(&package.ecosystem)
                        && name_key(&package.ecosystem, &name.name) == query
                })
            })
            .map(|affected| {
                affected
                    .ranges
                    .iter()
                    .filter(|range| range.kind == "GIT")
                    .count()
            })
            .sum()
    }

    pub fn matches(&self, package: &Package) -> Result<bool, String> {
        self.evaluate(package).map(|(matched, _)| matched)
    }

    pub fn evaluate(&self, package: &Package) -> Result<(bool, usize), String> {
        versions::equal(&package.ecosystem, &package.version, &package.version)?;
        let query_name =
            name_key(&package.ecosystem, &package.name).ok_or("invalid queried package name")?;
        if self.withdrawn.is_some() {
            return Ok((false, 0));
        }
        let mut matched = false;
        let mut opaque_git_tags = 0;
        for affected in &self.affected {
            let Some(name) = &affected.package else {
                continue;
            };
            if name.ecosystem != label(&package.ecosystem)
                || name_key(&package.ecosystem, &name.name).as_deref() != Some(&query_name)
            {
                continue;
            }
            if affected.versions.is_empty() && affected.ranges.is_empty() {
                return Err("applicable advisory has no version evidence".into());
            }
            for value in &affected.versions {
                let (included, opaque) = versions::enumerated_equal(
                    &package.ecosystem,
                    &package.version,
                    value,
                    affected.ranges.iter().any(|range| range.kind == "GIT"),
                )?;
                matched |= included;
                opaque_git_tags += usize::from(opaque);
            }
            for range in &affected.ranges {
                if range.kind == "GIT" {
                    if affected.versions.is_empty() {
                        return Err(
                            "named commit range has no required enumerated release versions".into(),
                        );
                    }
                    continue;
                }
                if !matches!(range.kind.as_str(), "SEMVER" | "ECOSYSTEM") {
                    return Err(
                        "applicable advisory range requires unsupported commit or range semantics"
                            .into(),
                    );
                }
                let mut events = Vec::new();
                for raw in &range.events {
                    let [(kind, value)] = raw.0.as_slice() else {
                        return Err("advisory event is absent, repeated or ambiguous".into());
                    };
                    let kind = match kind.as_str() {
                        "introduced" => EventKind::Introduced,
                        "fixed" => EventKind::Fixed,
                        "last_affected" => EventKind::LastAffected,
                        "limit" => EventKind::Limit,
                        _ => return Err("unsupported applicable advisory event".into()),
                    };
                    events.push((kind, value.clone()));
                }
                let ecosystem = if range.kind == "SEMVER" && package.ecosystem == Ecosystem::PyPI {
                    &Ecosystem::Crates
                } else {
                    &package.ecosystem
                };
                matched |= versions::interval(ecosystem, &package.version, &events)?;
            }
        }
        Ok((matched, opaque_git_tags))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn package(value: &str) -> Package {
        Package {
            ecosystem: Ecosystem::PyPI,
            name: "example-package".into(),
            version: value.into(),
        }
    }

    fn record(evidence: &str) -> Record {
        Record::parse(format!(r#"{{"id":"CONTROL-1","modified":"2026-01-01T00:00:00Z","affected":[{{"package":{{"ecosystem":"PyPI","name":"Example_Package"}},{evidence}}}]}}"#).as_bytes()).unwrap()
    }

    #[test]
    fn independently_declared_literal_interval_and_withdrawal_answers() {
        let literal = record(r#""versions":["1.0","0.9"]"#);
        assert!(literal.applies(&package("1.0.0")));
        assert!(literal.matches(&package("1.0.0")).unwrap());
        assert!(!literal.matches(&package("2.0")).unwrap());
        let interval = record(
            r#""ranges":[{"type":"ECOSYSTEM","events":[{"introduced":"0"},{"fixed":"2.0"}]}]"#,
        );
        assert!(interval.matches(&package("1.9")).unwrap());
        assert!(!interval.matches(&package("2.0")).unwrap());
        let mut withdrawn = interval;
        withdrawn.withdrawn = Some("2026-01-02T00:00:00Z".into());
        assert!(!withdrawn.matches(&package("1.9")).unwrap());
        let mixed = record(
            r#""versions":["1.0"],"ranges":[{"type":"GIT","events":[{"introduced":"0"},{"fixed":"opaque-commit-data"}]},{"type":"ECOSYSTEM","events":[{"introduced":"0"},{"fixed":"2.0"}]}]"#,
        );
        assert!(mixed.matches(&package("1.9")).unwrap());
        assert!(!mixed.matches(&package("2.0")).unwrap());
        assert_eq!(mixed.commit_ranges_outside_subject(&package("2.0")), 1);
        let unnamed = Record::parse(br#"{"id":"CONTROL-1","modified":"2026-01-01T00:00:00Z","affected":[{"ranges":[{"type":"GIT","events":[{"introduced":"0"}]}]}]}"#).unwrap();
        assert!(!unnamed.applies(&package("1.0")));
        assert_eq!(
            name_key(&Ecosystem::Crates, "SERDE_JSON"),
            Some("serde-json".into())
        );
        assert_ne!(
            name_key(&Ecosystem::Go, "Example.org/module"),
            name_key(&Ecosystem::Go, "example.org/module")
        );
        for name in ["", "a//b", "a/../b", "a b", "/a"] {
            assert_eq!(name_key(&Ecosystem::Go, name), None);
        }
    }

    #[test]
    fn reject_ambiguous_missing_and_unsupported_applicable_evidence() {
        for evidence in [
            r#""versions":[]"#,
            r#""ranges":[{"type":"ECOSYSTEM","events":[]}]"#,
            r#""ranges":[{"type":"GIT","events":[{"introduced":"0"}]}]"#,
            r#""ranges":[{"type":"ECOSYSTEM","events":[{"introduced":"0","fixed":"2.0"}]}]"#,
            r#""ranges":[{"type":"ECOSYSTEM","events":[{"introduced":"0","introduced":"1.0"}]}]"#,
            r#""ranges":[{"type":"ECOSYSTEM","events":[{"future":"2.0"}]}]"#,
            r#""ranges":[{"type":"ECOSYSTEM","events":[{"introduced":"unknown"}]}]"#,
        ] {
            assert!(
                record(evidence).matches(&package("1.0")).is_err(),
                "unsupported evidence passed: {evidence}"
            );
        }
        assert!(
            Record::parse(br#"{"id":"A","id":"B","modified":"2026-01-01T00:00:00Z"}"#).is_err()
        );
        assert!(
            Record::parse(
                br#"{"id":"A","modified":"2026-01-01T00:00:00Z","schema_version":"2.0.0"}"#
            )
            .is_err()
        );
        assert!(
            Record::parse(
                br#"{"id":"CONTROL:1","modified":"2026-01-01T00:00:00Z","schema_version":"1.9.0"}"#
            )
            .is_ok()
        );
        assert!(Record::parse(br#"{"id":"A","modified":"2026-01-01T00:00:00Z","schema_version":"1.100.0+metadata"}"#).is_ok());
        assert!(
            Record::parse(
                br#"{"id":"A","modified":"2026-01-01T00:00:00Z","schema_version":"1.9.0-rc.1"}"#
            )
            .is_err()
        );
        assert!(Record::parse(b"not JSON").is_err());
        assert!(
            record(r#""versions":["1.0"]"#)
                .matches(&package("unknown"))
                .is_err()
        );
        assert!(
            record(r#""versions":["historical-label"]"#)
                .matches(&package("1.0"))
                .is_err()
        );
        for withdrawn in ["", "unknown", "2026-02-30T00:00:00Z"] {
            let source = serde_json::json!({"id":"CONTROL-1","modified":"2026-01-01T00:00:00Z","withdrawn":withdrawn});
            assert!(Record::parse(&serde_json::to_vec(&source).unwrap()).is_err());
        }
        assert!(
            Record::parse(
                br#"{"id":"CONTROL-1","modified":"2026-01-01T00:00:00Z","withdrawn":null}"#
            )
            .is_err()
        );
    }

    #[test]
    fn withdrawal_and_modification_timestamp_boundaries() {
        for value in [
            "2024-02-29T23:59:59Z",
            "2026-01-01T00:00:00.123456Z",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01t00:00:00-10:30",
        ] {
            assert!(timestamp(value));
        }
        for value in [
            "",
            "2023-02-29T00:00:00Z",
            "0000-01-01T00:00:00Z",
            "2026-01-01T24:00:00Z",
            "2026-01-01T00:60:00Z",
            "2026-01-01T00:00:60Z",
            "2026-01-01T00:00:00.Z",
            "2026-01-01T00:00:00+24:00",
            "2026-01-01T00:00:00+00:60",
            "2026-01-01T00:00:00Ztail",
        ] {
            assert!(!timestamp(value), "unsupported timestamp passed: {value}");
        }
    }

    #[test]
    fn unparsable_names_are_disclosed_and_do_not_equal_typed_queries() {
        for (ecosystem, name, invalid) in [
            (Ecosystem::PyPI, "example-package", "bad/name"),
            (Ecosystem::Go, "example.org/module", ""),
            (Ecosystem::Crates, "example-package", "bad.name"),
        ] {
            let mut source = serde_json::json!({"id":"CONTROL-1","modified":"2026-01-01T00:00:00Z",
                "affected":[{"package":{"ecosystem":label(&ecosystem),"name":name},"versions":["1.2.3"]}]});
            let package = Package {
                ecosystem,
                name: name.into(),
                version: "1.2.3".into(),
            };
            let accepted = Record::parse(&serde_json::to_vec(&source).unwrap()).unwrap();
            assert!(accepted.applies(&package));
            assert!(accepted.matches(&package).unwrap());
            source["affected"][0]["package"]["name"] = serde_json::json!(invalid);
            let opaque = Record::parse(&serde_json::to_vec(&source).unwrap()).unwrap();
            assert_eq!(opaque.unparsable_package_names(), 1);
            assert!(!opaque.applies(&package));
            assert!(!opaque.matches(&package).unwrap());
        }
    }
}
