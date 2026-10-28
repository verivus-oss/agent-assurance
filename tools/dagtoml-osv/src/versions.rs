use std::cmp::Ordering;
use std::str::FromStr;

use crate::model::Ecosystem;

#[derive(Clone, Debug)]
enum Version {
    Python(pep440_rs::Version),
    Semantic(semver::Version),
}

impl Version {
    fn parse(ecosystem: &Ecosystem, value: &str) -> Result<Self, String> {
        if value.is_empty() || value.len() > 4096 {
            return Err("advisory version is absent or exceeds its bound".into());
        }
        match ecosystem {
            Ecosystem::PyPI => pep440_rs::Version::from_str(value)
                .map(Self::Python)
                .map_err(|_| "unsupported Python advisory version".into()),
            Ecosystem::Go => semver::Version::parse(value.strip_prefix('v').unwrap_or(value))
                .map(Self::Semantic)
                .map_err(|_| "unsupported Go advisory version".into()),
            Ecosystem::Crates => semver::Version::parse(value)
                .map(Self::Semantic)
                .map_err(|_| "unsupported Cargo advisory version".into()),
        }
    }

    fn compare(&self, other: &Self) -> Ordering {
        match (self, other) {
            (Self::Python(left), Self::Python(right)) => left.cmp(right),
            (Self::Semantic(left), Self::Semantic(right)) => left.cmp_precedence(right),
            (Self::Python(_), Self::Semantic(_)) => Ordering::Less,
            (Self::Semantic(_), Self::Python(_)) => Ordering::Greater,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EventKind {
    Introduced,
    Fixed,
    LastAffected,
    Limit,
}

#[derive(Clone, Debug)]
struct Event {
    kind: EventKind,
    version: Option<Version>,
}

fn boundary(left: &Option<Version>, right: &Option<Version>) -> Ordering {
    match (left, right) {
        (None, None) => Ordering::Equal,
        (None, Some(_)) => Ordering::Less,
        (Some(_), None) => Ordering::Greater,
        (Some(left), Some(right)) => left.compare(right),
    }
}

pub fn equal(ecosystem: &Ecosystem, left: &str, right: &str) -> Result<bool, String> {
    Ok(
        Version::parse(ecosystem, left)?.compare(&Version::parse(ecosystem, right)?)
            == Ordering::Equal,
    )
}

// Mixed GIT/packaging entries may enumerate tags outside the package version
// grammar. They have literal identity, never a position in a version range.
pub fn enumerated_equal(
    ecosystem: &Ecosystem,
    query: &str,
    value: &str,
    git_tags: bool,
) -> Result<(bool, bool), String> {
    let query_version = Version::parse(ecosystem, query)?;
    match Version::parse(ecosystem, value) {
        Ok(version) => Ok((query_version.compare(&version) == Ordering::Equal, false)),
        Err(_)
            if git_tags
                && !value.is_empty()
                && value.len() <= 4096
                && !value.chars().any(char::is_control) =>
        {
            Ok((query == value, true))
        }
        Err(error) => Err(error),
    }
}

pub fn interval(
    ecosystem: &Ecosystem,
    query: &str,
    events: &[(EventKind, String)],
) -> Result<bool, String> {
    if events.is_empty() {
        return Err("applicable advisory interval has no events".into());
    }
    if !events
        .iter()
        .any(|(kind, _)| *kind == EventKind::Introduced)
        || (events.iter().any(|(kind, _)| *kind == EventKind::Fixed)
            && events
                .iter()
                .any(|(kind, _)| *kind == EventKind::LastAffected))
    {
        return Err(
            "advisory interval lacks an introduction or mixes fixed and last-affected events"
                .into(),
        );
    }
    let query = Version::parse(ecosystem, query)?;
    let mut before_limit = !events.iter().any(|(kind, _)| *kind == EventKind::Limit);
    let mut parsed = Vec::new();
    for (kind, value) in events {
        if *kind == EventKind::Limit {
            // Limits bound the whole range by a union of ceilings. They are
            // not timeline transitions and do not consume introductions.
            before_limit |= if value.contains('*') {
                true
            } else {
                query.compare(&Version::parse(ecosystem, value)?) == Ordering::Less
            };
            continue;
        }
        let version = if *kind == EventKind::Introduced && value == "0" {
            None
        } else {
            Some(Version::parse(ecosystem, value)?)
        };
        parsed.push(Event {
            kind: *kind,
            version,
        });
    }
    parsed.sort_by(|left, right| boundary(&left.version, &right.version));
    let mut active = 0usize;
    let mut matched = false;
    let mut start = 0;
    while start < parsed.len() {
        let mut end = start + 1;
        while end < parsed.len()
            && boundary(&parsed[start].version, &parsed[end].version) == Ordering::Equal
        {
            end += 1;
        }
        let group = &parsed[start..end];
        let introduced = group
            .iter()
            .filter(|event| event.kind == EventKind::Introduced)
            .count();
        let fixed = group
            .iter()
            .filter(|event| event.kind == EventKind::Fixed)
            .count();
        let inclusive = group
            .iter()
            .filter(|event| event.kind == EventKind::LastAffected)
            .count();
        if [introduced, fixed, inclusive]
            .into_iter()
            .any(|count| count > 1)
        {
            return Err("advisory interval repeats a boundary event".into());
        }
        active = active
            .checked_sub(fixed)
            .ok_or("advisory interval closes without an introduction")?;
        active += introduced;
        let point_included = active > 0;
        active = active
            .checked_sub(inclusive)
            .ok_or("advisory interval closes without an introduction")?;
        if active > 1 {
            return Err("advisory interval introduces an already-open range".into());
        }
        let comparison = parsed[start]
            .version
            .as_ref()
            .map_or(Ordering::Greater, |version| query.compare(version));
        if comparison == Ordering::Equal {
            matched = point_included;
        }
        if comparison == Ordering::Greater {
            matched = active > 0;
        }
        start = end;
    }
    Ok(matched && before_limit)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn events(values: &[(EventKind, &str)]) -> Vec<(EventKind, String)> {
        values
            .iter()
            .map(|(kind, value)| (*kind, (*value).into()))
            .collect()
    }

    #[test]
    fn independent_ecosystem_ordering_and_identity_answers() {
        assert!(equal(&Ecosystem::PyPI, "1.0", "1.0.0").unwrap());
        assert!(!equal(&Ecosystem::PyPI, "1.0+local", "1.0").unwrap());
        assert!(equal(&Ecosystem::Crates, "1.2.3+build", "1.2.3").unwrap());
        assert!(equal(&Ecosystem::Go, "v1.2.3+incompatible", "1.2.3").unwrap());
        let ordered = [
            "1.0.dev1",
            "1.0a1",
            "1.0b1",
            "1.0rc1",
            "1.0",
            "1.0.post1",
            "1!0.1",
        ];
        for pair in ordered.windows(2) {
            let left = Version::parse(&Ecosystem::PyPI, pair[0]).unwrap();
            let right = Version::parse(&Ecosystem::PyPI, pair[1]).unwrap();
            assert_eq!(left.compare(&right), Ordering::Less);
        }
        for ecosystem in [Ecosystem::Go, Ecosystem::Crates, Ecosystem::PyPI] {
            for value in ["", "unknown", "1.*", ">=1.0"] {
                assert!(Version::parse(&ecosystem, value).is_err());
            }
        }
    }

    #[test]
    fn independently_declared_interval_edges_holes_and_open_ranges() {
        let pair = events(&[
            (EventKind::Introduced, "1.0.0"),
            (EventKind::Fixed, "2.0.0"),
        ]);
        for (value, expected) in [
            ("0.9.9", false),
            ("1.0.0", true),
            ("1.9.9", true),
            ("2.0.0", false),
            ("3.0.0", false),
        ] {
            assert_eq!(
                interval(&Ecosystem::Crates, value, &pair).unwrap(),
                expected
            );
        }
        let closed = events(&[
            (EventKind::Introduced, "1.0.0"),
            (EventKind::LastAffected, "2.0.0"),
        ]);
        assert!(interval(&Ecosystem::Crates, "2.0.0", &closed).unwrap());
        assert!(!interval(&Ecosystem::Crates, "2.0.1", &closed).unwrap());
        let holes = events(&[
            (EventKind::Fixed, "1.17.3"),
            (EventKind::Introduced, "0"),
            (EventKind::Introduced, "1.17.0"),
            (EventKind::Fixed, "1.16.10"),
        ]);
        for (value, expected) in [
            ("1.16.9", true),
            ("1.16.10", false),
            ("1.17.0", true),
            ("1.17.3", false),
        ] {
            assert_eq!(interval(&Ecosystem::Go, value, &holes).unwrap(), expected);
        }
        assert!(
            interval(
                &Ecosystem::Crates,
                "0.0.0-alpha",
                &events(&[(EventKind::Introduced, "0")])
            )
            .unwrap()
        );
        assert!(
            !interval(
                &Ecosystem::Crates,
                "1.0.0",
                &events(&[(EventKind::Introduced, "0"), (EventKind::Limit, "1.0.0")])
            )
            .unwrap()
        );
        let touching = events(&[
            (EventKind::Introduced, "0"),
            (EventKind::Fixed, "1.0.0"),
            (EventKind::Introduced, "1.0.0"),
            (EventKind::Fixed, "2.0.0"),
        ]);
        assert!(interval(&Ecosystem::Crates, "1.0.0", &touching).unwrap());
        let singleton = events(&[
            (EventKind::Introduced, "1.0.0"),
            (EventKind::LastAffected, "1.0.0"),
        ]);
        for (value, expected) in [("0.9.9", false), ("1.0.0", true), ("1.0.1", false)] {
            assert_eq!(
                interval(&Ecosystem::Crates, value, &singleton).unwrap(),
                expected
            );
        }
        let shared_point = events(&[
            (EventKind::Introduced, "0"),
            (EventKind::LastAffected, "1.0.0"),
            (EventKind::Introduced, "1.0.0"),
            (EventKind::LastAffected, "2.0.0"),
        ]);
        assert!(interval(&Ecosystem::Crates, "1.0.0", &shared_point).unwrap());
        assert!(interval(&Ecosystem::Crates, "2.0.0", &shared_point).unwrap());
        assert!(!interval(&Ecosystem::Crates, "2.0.1", &shared_point).unwrap());
        for infinity in ["*", "1.*"] {
            assert!(
                interval(
                    &Ecosystem::Crates,
                    "999.0.0",
                    &events(&[(EventKind::Introduced, "0"), (EventKind::Limit, infinity)])
                )
                .unwrap()
            );
        }
    }

    #[test]
    fn unsupported_or_inconsistent_event_populations_fail() {
        for values in [
            vec![],
            events(&[(EventKind::Fixed, "1.0.0")]),
            events(&[
                (EventKind::Introduced, "0"),
                (EventKind::Fixed, "1.0.0"),
                (EventKind::LastAffected, "2.0.0"),
            ]),
            events(&[(EventKind::Limit, "*")]),
            events(&[
                (EventKind::Introduced, "1.0.0"),
                (EventKind::Introduced, "2.0.0"),
            ]),
            events(&[(EventKind::Introduced, "0"), (EventKind::Fixed, "unknown")]),
            events(&[
                (EventKind::Introduced, "1.0.0"),
                (EventKind::Fixed, "1.0.0"),
            ]),
        ] {
            assert!(interval(&Ecosystem::Crates, "1.0.0", &values).is_err());
        }
    }

    #[test]
    fn mixed_git_tags_have_literal_identity_without_version_ordering() {
        assert_eq!(
            enumerated_equal(&Ecosystem::PyPI, "2.1.0", "v2.1.0", true).unwrap(),
            (true, false)
        );
        assert_eq!(
            enumerated_equal(&Ecosystem::PyPI, "2.1.0", "v0.1.1d", true).unwrap(),
            (false, true)
        );
        for value in ["v0.1.1d", "historical-label"] {
            assert!(enumerated_equal(&Ecosystem::PyPI, "2.1.0", value, false).is_err());
        }
        for value in ["", "bad\nlabel"] {
            assert!(enumerated_equal(&Ecosystem::PyPI, "2.1.0", value, true).is_err());
        }
        assert!(enumerated_equal(&Ecosystem::PyPI, "v0.1.1d", "v0.1.1d", true).is_err());
    }

    #[test]
    fn limits_are_union_ceilings_independent_of_timeline_transitions() {
        let limits = events(&[
            (EventKind::Introduced, "0"),
            (EventKind::Limit, "1.0.0"),
            (EventKind::Limit, "2.0.0"),
        ]);
        for (query, expected) in [
            ("0.5.0", true),
            ("1.0.0", true),
            ("1.5.0", true),
            ("2.0.0", false),
        ] {
            assert_eq!(
                interval(&Ecosystem::Crates, query, &limits).unwrap(),
                expected
            );
        }
        let reopened = events(&[
            (EventKind::Introduced, "0"),
            (EventKind::Fixed, "1.0.0"),
            (EventKind::Introduced, "2.0.0"),
            (EventKind::Limit, "3.0.0"),
        ]);
        for (query, expected) in [
            ("0.5.0", true),
            ("1.0.0", false),
            ("2.0.0", true),
            ("3.0.0", false),
        ] {
            assert_eq!(
                interval(&Ecosystem::Crates, query, &reopened).unwrap(),
                expected
            );
        }
        let infinite = events(&[
            (EventKind::Introduced, "0"),
            (EventKind::Limit, "1.0.0"),
            (EventKind::Limit, "*"),
        ]);
        assert!(interval(&Ecosystem::Crates, "100.0.0", &infinite).unwrap());
        let invalid = events(&[
            (EventKind::Introduced, "0"),
            (EventKind::Limit, "unknown"),
            (EventKind::Limit, "*"),
        ]);
        assert!(interval(&Ecosystem::Crates, "1.0.0", &invalid).is_err());
    }
}
