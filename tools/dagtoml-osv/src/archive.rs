use std::collections::{BTreeMap, BTreeSet};

use serde::Serialize;

use crate::{
    digest::sha256,
    model::{Ecosystem, Package},
    records::{self, Record},
};

const MAX_ARCHIVE: usize = 256 * 1024 * 1024;
const MAX_MEMBER: u64 = 4 * 1024 * 1024;
const MAX_RECORDS: usize = 65_534;
const MAX_EXPANDED: u64 = 2 * 1024 * 1024 * 1024;

#[derive(Clone, Debug, Serialize)]
pub struct Evidence {
    pub advisory_id: String,
    pub record_sha256: String,
    pub member: String,
}

#[derive(Debug, Serialize)]
pub struct Assessment {
    pub package: Package,
    pub applicable_records: usize,
    pub commit_ranges_outside_version_subject: usize,
    pub opaque_git_tag_literals: usize,
    pub advisories: Vec<Evidence>,
}

#[derive(Debug, Serialize)]
pub struct Control {
    pub package: Package,
    pub advisory_id: String,
    pub record_sha256: String,
    pub expected: bool,
    pub affected: bool,
}

#[derive(Debug, Serialize)]
pub struct Dataset {
    pub ecosystem: Ecosystem,
    pub archive_sha256: String,
    pub archive_bytes: usize,
    pub members: usize,
    pub directory_members: usize,
    pub records: usize,
    pub expanded_bytes: u64,
    pub applicable_records: usize,
    pub unparseable_package_names: Vec<Evidence>,
    pub assessments: Vec<Assessment>,
    pub controls: Vec<Control>,
}

fn control(ecosystem: &Ecosystem) -> (&'static str, &'static str, &'static str, &'static str) {
    match ecosystem {
        Ecosystem::PyPI => ("PYSEC-2014-8", "jinja2", "2.4.1", "3.1.6"),
        Ecosystem::Go => ("GO-2021-0263", "stdlib", "1.17.0", "1.26.10"),
        Ecosystem::Crates => ("RUSTSEC-2020-0071", "time", "0.1.44", "0.3.44"),
    }
}

fn member_id<'a>(ecosystem: &Ecosystem, name: &'a str) -> Option<&'a str> {
    let prefix = format!("{}/", records::label(ecosystem));
    let name = name.strip_prefix(&prefix).unwrap_or(name);
    let id = name.strip_suffix(".json")?;
    if id.is_empty()
        || id.len() > 256
        || !id
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || b":-_.".contains(&byte))
    {
        return None;
    }
    Some(id)
}

pub fn evaluate(
    ecosystem: &Ecosystem,
    bytes: &[u8],
    required: &BTreeSet<Package>,
) -> Result<Dataset, String> {
    let mut queries: BTreeMap<Package, Assessment> = required
        .iter()
        .filter(|package| &package.ecosystem == ecosystem)
        .cloned()
        .map(|package| {
            (
                package.clone(),
                Assessment {
                    package,
                    applicable_records: 0,
                    commit_ranges_outside_version_subject: 0,
                    opaque_git_tag_literals: 0,
                    advisories: vec![],
                },
            )
        })
        .collect();
    if queries.is_empty() {
        return Err("advisory dataset has no selected package subjects".into());
    }
    for package in queries.keys() {
        if records::name_key(ecosystem, &package.name).is_none() {
            return Err("advisory subject has an invalid package name".into());
        }
        crate::versions::equal(ecosystem, &package.version, &package.version)?;
    }
    if bytes.is_empty() || bytes.len() > MAX_ARCHIVE {
        return Err("advisory archive is absent or exceeds its bound".into());
    }
    let archive_sha256 = sha256(bytes);
    let archive = crate::zip_records::Archive::parse(bytes)?;
    let members = archive.members.len();
    if members == 0 || members > MAX_RECORDS {
        return Err("advisory archive member population is absent or exceeds its bound".into());
    }
    let (control_id, control_name, old, fixed) = control(ecosystem);
    let mut controls = Vec::new();
    let mut identities = BTreeSet::new();
    let mut records = 0usize;
    let mut directories = 0usize;
    let mut expanded = 0u64;
    let mut applicable_records = 0usize;
    let mut unparseable_package_names = Vec::new();
    for file in archive.members {
        let name = file.name.to_owned();
        if name.ends_with('/') {
            if name != format!("{}/", records::label(ecosystem)) || file.size() != 0 {
                return Err("unexpected advisory archive directory".into());
            }
            directories += 1;
            if directories > 1 {
                return Err("advisory archive repeats its directory identity".into());
            }
            file.read(0)?;
            continue;
        }
        if file
            .unix_mode
            .is_some_and(|mode| mode & 0o170000 != 0 && mode & 0o170000 != 0o100000)
        {
            return Err("nonregular advisory archive member is unsupported".into());
        }
        let expected_id =
            member_id(ecosystem, &name).ok_or("unexpected advisory archive member name")?;
        if !identities.insert(expected_id.to_owned()) {
            return Err("advisory archive repeats a record identity".into());
        }
        if file.size() == 0 || file.size() > MAX_MEMBER {
            return Err("advisory record is absent or exceeds its bound".into());
        }
        expanded = expanded
            .checked_add(file.size())
            .filter(|total| *total <= MAX_EXPANDED)
            .ok_or("advisory archive expansion exceeds its bound")?;
        let declared = file.size();
        let source = file.read(MAX_MEMBER)?;
        if source.len() as u64 != declared {
            return Err("advisory record byte population differs from its header".into());
        }
        let digest = sha256(&source);
        let record = Record::parse(&source).map_err(|message| {
            format!(
                "{message}; record {expected_id}; source sha256 {digest}; bytes 0:{}",
                source.len()
            )
        })?;
        if record.id != expected_id {
            return Err("advisory identity differs from its archive member".into());
        }
        records += 1;
        if record.unparseable_package_names() > 0 {
            unparseable_package_names.push(Evidence {
                advisory_id: record.id.clone(),
                record_sha256: digest.clone(),
                member: name.clone(),
            });
        }
        let mut applicable = false;
        for assessment in queries.values_mut() {
            if !record.applies(&assessment.package) {
                continue;
            }
            applicable = true;
            assessment.applicable_records += 1;
            assessment.commit_ranges_outside_version_subject +=
                record.commit_ranges_outside_subject(&assessment.package);
            let (matched, opaque) = record.evaluate(&assessment.package).map_err(|message| {
                format!("{message}; advisory {}; source sha256 {digest}", record.id)
            })?;
            assessment.opaque_git_tag_literals += opaque;
            if matched {
                assessment.advisories.push(Evidence {
                    advisory_id: record.id.clone(),
                    record_sha256: digest.clone(),
                    member: name.clone(),
                });
            }
        }
        applicable_records += usize::from(applicable);
        if record.id == control_id {
            if !controls.is_empty() {
                return Err("advisory dataset repeats its independent control record".into());
            }
            for (version, expected) in [(old, true), (fixed, false)] {
                let package = Package {
                    ecosystem: ecosystem.clone(),
                    name: control_name.into(),
                    version: version.into(),
                };
                if !record.applies(&package) {
                    return Err("advisory control record names a different package".into());
                }
                let affected = record.matches(&package)?;
                if affected != expected {
                    return Err("local advisory evaluator failed its independent affected/unaffected control".into());
                }
                controls.push(Control {
                    package,
                    advisory_id: control_id.into(),
                    record_sha256: digest.clone(),
                    expected,
                    affected,
                });
            }
        }
    }
    let expected_queries: BTreeSet<_> = required
        .iter()
        .filter(|package| &package.ecosystem == ecosystem)
        .cloned()
        .collect();
    if records == 0
        || records + directories != members
        || records != identities.len()
        || controls.len() != 2
        || queries.keys().cloned().collect::<BTreeSet<_>>() != expected_queries
    {
        return Err("advisory archive, control or assessment population is incomplete".into());
    }
    Ok(Dataset {
        ecosystem: ecosystem.clone(),
        archive_sha256,
        archive_bytes: bytes.len(),
        members,
        directory_members: directories,
        records,
        expanded_bytes: expanded,
        applicable_records,
        unparseable_package_names,
        assessments: queries.into_values().collect(),
        controls,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture(target: &str, include_control: bool) -> Vec<u8> {
        let mut files = Vec::new();
        if include_control {
            files.push(("PYSEC-2014-8.json",br#"{"id":"PYSEC-2014-8","modified":"2023-11-08T03:57:34.512953Z","affected":[{"package":{"ecosystem":"PyPI","name":"jinja2"},"ranges":[{"type":"ECOSYSTEM","events":[{"introduced":"0"},{"fixed":"2.7.2"}]}]}]}"#.as_slice()));
        }
        files.push(("CONTROL-1.json", target.as_bytes()));
        crate::zip_records::stored_fixture(&files)
    }

    fn query(version: &str) -> BTreeSet<Package> {
        [Package {
            ecosystem: Ecosystem::PyPI,
            name: "example-package".into(),
            version: version.into(),
        }]
        .into()
    }

    fn target() -> &'static str {
        r#"{"id":"CONTROL-1","modified":"2026-01-01T00:00:00Z","affected":[{"package":{"ecosystem":"PyPI","name":"example-package"},"ranges":[{"type":"ECOSYSTEM","events":[{"introduced":"0"},{"fixed":"2.0"}]}]}]}"#
    }

    #[test]
    fn complete_archive_population_and_independent_target_answers() {
        let bytes = fixture(target(), true);
        let accepted = evaluate(&Ecosystem::PyPI, &bytes, &query("1.0")).unwrap();
        assert_eq!(
            (
                accepted.members,
                accepted.records,
                accepted.directory_members
            ),
            (2, 2, 0)
        );
        assert_eq!(accepted.applicable_records, 1);
        assert_eq!(accepted.assessments.len(), 1);
        assert_eq!(accepted.assessments[0].advisories.len(), 1);
        assert_eq!(
            accepted.assessments[0].advisories[0].advisory_id,
            "CONTROL-1"
        );
        assert_eq!(
            accepted
                .controls
                .iter()
                .map(|control| control.affected)
                .collect::<Vec<_>>(),
            [true, false]
        );
        let fixed = evaluate(&Ecosystem::PyPI, &bytes, &query("2.0")).unwrap();
        assert!(fixed.assessments[0].advisories.is_empty());
    }

    #[test]
    fn malformed_incomplete_and_corrupt_inputs_do_not_become_clear_results() {
        assert!(evaluate(&Ecosystem::PyPI, &[], &query("1.0")).is_err());
        assert!(evaluate(&Ecosystem::PyPI, &fixture(target(), false), &query("1.0")).is_err());
        assert!(evaluate(&Ecosystem::PyPI, &fixture("not JSON", true), &query("1.0")).is_err());
        assert!(evaluate(&Ecosystem::PyPI, &fixture(target(), true), &BTreeSet::new()).is_err());
        for package in [
            Package {
                ecosystem: Ecosystem::PyPI,
                name: "unrelated-package".into(),
                version: "unknown".into(),
            },
            Package {
                ecosystem: Ecosystem::PyPI,
                name: "".into(),
                version: "1.0".into(),
            },
        ] {
            assert!(
                evaluate(
                    &Ecosystem::PyPI,
                    &fixture(target(), true),
                    &[package].into()
                )
                .is_err()
            );
        }
        let mut corrupted = fixture(target(), true);
        let needle = b"example-package";
        let positions: Vec<_> = corrupted
            .windows(needle.len())
            .enumerate()
            .filter(|(_, value)| *value == needle)
            .map(|(index, _)| index)
            .collect();
        assert_eq!(positions.len(), 1);
        corrupted[positions[0]] = b'E';
        assert_eq!(
            evaluate(&Ecosystem::PyPI, &corrupted, &query("1.0")).unwrap_err(),
            "advisory member integrity or decoding failed"
        );
        assert_eq!(
            member_id(&Ecosystem::PyPI, "PyPI/CONTROL-1.json"),
            Some("CONTROL-1")
        );
        for name in [
            "../CONTROL-1.json",
            "CONTROL-1.json/extra",
            "other/CONTROL-1.json",
            "CONTROL-1.txt",
        ] {
            assert!(member_id(&Ecosystem::PyPI, name).is_none());
        }
    }
}
