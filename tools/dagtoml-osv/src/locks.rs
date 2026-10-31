use std::collections::BTreeSet;

use crate::digest::sha256;
use crate::model::{Ecosystem, Package};

#[derive(Debug, Eq, PartialEq)]
pub struct Extracted {
    pub packages: BTreeSet<Package>,
    pub local_packages: BTreeSet<Package>,
}

fn invalid(kind: &str, source: &[u8]) -> String {
    format!(
        "invalid or unsupported {kind}; source sha256 {}; bytes 0:{}",
        sha256(source),
        source.len()
    )
}

fn text<'a>(kind: &str, source: &'a [u8]) -> Result<&'a str, String> {
    std::str::from_utf8(source).map_err(|_| invalid(kind, source))
}

fn atom(value: &str, extra: &[u8]) -> bool {
    !value.is_empty()
        && value.len() <= 1024
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || extra.contains(&byte))
}

fn package(ecosystem: Ecosystem, name: &str, value: &str) -> Package {
    Package {
        ecosystem,
        name: name.into(),
        version: value.into(),
    }
}

pub fn canonical_python_name(name: &str) -> Option<String> {
    if !atom(name, b"-_.")
        || !name.as_bytes().first()?.is_ascii_alphanumeric()
        || !name.as_bytes().last()?.is_ascii_alphanumeric()
    {
        return None;
    }
    let mut result = String::new();
    for byte in name.bytes() {
        if b"-_.".contains(&byte) {
            if !result.ends_with('-') {
                result.push('-');
            }
        } else {
            result.push(char::from(byte.to_ascii_lowercase()));
        }
    }
    Some(result)
}

pub fn python(source: &[u8]) -> Result<Extracted, String> {
    let mut packages = BTreeSet::new();
    let mut continuation = false;
    let mut had_package = false;
    for raw in text("Python lock", source)?.lines() {
        let raw = raw.trim();
        if raw.is_empty() || raw.starts_with('#') {
            continue;
        }
        let continued = raw.ends_with('\\');
        let value = raw.strip_suffix('\\').unwrap_or(raw).trim();
        if let Some(hash) = value.strip_prefix("--hash=sha256:") {
            if !had_package
                || !continuation
                || hash.len() != 64
                || !hash
                    .bytes()
                    .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
            {
                return Err(invalid("Python hash continuation", source));
            }
        } else {
            if continuation {
                return Err(invalid("unfinished Python hash continuation", source));
            }
            let (pin, _) = value.split_once(';').unwrap_or((value, ""));
            let (name, value) = pin
                .trim()
                .split_once("==")
                .ok_or_else(|| invalid("Python pin", source))?;
            let name = canonical_python_name(name)
                .ok_or_else(|| invalid("Python package name", source))?;
            let value = value.trim();
            if value.is_empty()
                || value.len() > 1024
                || value.parse::<pep440_rs::Version>().is_err()
                || !packages.insert(package(Ecosystem::PyPI, &name, value))
            {
                return Err(invalid("Python version or repeated pin", source));
            }
            had_package = true;
        }
        continuation = continued;
    }
    if continuation {
        return Err(invalid("unfinished Python hash continuation", source));
    }
    Ok(Extracted {
        packages,
        local_packages: BTreeSet::new(),
    })
}

pub fn cargo(source: &[u8], manifest_source: &[u8]) -> Result<Extracted, String> {
    let lock: toml::Value =
        toml::from_str(text("Cargo lock", source)?).map_err(|_| invalid("Cargo lock", source))?;
    let manifest: toml::Value = toml::from_str(text("Cargo manifest", manifest_source)?)
        .map_err(|_| invalid("Cargo manifest", manifest_source))?;
    let local = manifest
        .get("package")
        .and_then(toml::Value::as_table)
        .ok_or_else(|| invalid("Cargo root package", manifest_source))?;
    let local_name = local
        .get("name")
        .and_then(toml::Value::as_str)
        .ok_or_else(|| invalid("Cargo root package name", manifest_source))?;
    let local_version = local
        .get("version")
        .and_then(toml::Value::as_str)
        .ok_or_else(|| invalid("Cargo root package version", manifest_source))?;
    if !matches!(
        lock.get("version").and_then(toml::Value::as_integer),
        Some(3 | 4)
    ) {
        return Err(invalid("Cargo lock version", source));
    }
    let rows = lock
        .get("package")
        .and_then(toml::Value::as_array)
        .filter(|rows| !rows.is_empty())
        .ok_or_else(|| invalid("Cargo package population", source))?;
    let mut packages = BTreeSet::new();
    let mut local_packages = BTreeSet::new();
    for row in rows {
        let name = row
            .get("name")
            .and_then(toml::Value::as_str)
            .ok_or_else(|| invalid("Cargo package name", source))?;
        let value = row
            .get("version")
            .and_then(toml::Value::as_str)
            .ok_or_else(|| invalid("Cargo package version", source))?;
        if !atom(name, b"-_") || value.len() > 1024 || semver::Version::parse(value).is_err() {
            return Err(invalid("Cargo package identity", source));
        }
        let identity = package(Ecosystem::Crates, name, value);
        match row.get("source") {
            None if name == local_name && value == local_version => {
                if !local_packages.insert(identity) {
                    return Err(invalid("repeated Cargo root", source));
                }
            }
            Some(toml::Value::String(registry))
                if registry == "registry+https://github.com/rust-lang/crates.io-index" =>
            {
                let hash = row
                    .get("checksum")
                    .and_then(toml::Value::as_str)
                    .ok_or_else(|| invalid("Cargo checksum", source))?;
                if hash.len() != 64
                    || !hash
                        .bytes()
                        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
                    || !packages.insert(identity)
                {
                    return Err(invalid("Cargo checksum or repeated identity", source));
                }
            }
            _ => {
                return Err(invalid(
                    "unregistered local, Git or alternate Cargo source",
                    source,
                ));
            }
        }
    }
    if local_packages.len() != 1 || packages.len() + local_packages.len() != rows.len() {
        return Err(invalid("Cargo root or package population", source));
    }
    Ok(Extracted {
        packages,
        local_packages,
    })
}

pub fn go(source: &[u8]) -> Result<Extracted, String> {
    let mut packages = BTreeSet::new();
    let mut module = false;
    let mut go = false;
    let mut block = false;
    for raw in text("Go module", source)?.lines() {
        let raw = raw.split_once("//").map_or(raw, |(head, _)| head).trim();
        if raw.is_empty() {
            continue;
        }
        let parts: Vec<_> = raw.split_ascii_whitespace().collect();
        if block && parts == [")"] {
            block = false;
            continue;
        }
        let required = if block {
            parts.as_slice()
        } else {
            match parts.as_slice() {
                ["module", name] if !module && atom(name, b"./_-~") => {
                    module = true;
                    continue;
                }
                ["go", value]
                    if !go
                        && semver::Version::parse(value).is_ok_and(|version| {
                            version.major == 1
                                && version.minor >= 17
                                && version.pre.is_empty()
                                && version.build.is_empty()
                        }) =>
                {
                    packages.insert(package(Ecosystem::Go, "stdlib", value));
                    go = true;
                    continue;
                }
                ["require", "("] => {
                    block = true;
                    continue;
                }
                ["require", name, value] => &[*name, *value],
                _ => return Err(invalid("Go declaration", source)),
            }
        };
        match required {
            [name, value]
                if atom(name, b"./_-~")
                    && value.strip_prefix('v').is_some_and(|value| {
                        value.len() <= 1024 && semver::Version::parse(value).is_ok()
                    }) =>
            {
                if !packages.insert(package(Ecosystem::Go, name, value)) {
                    return Err(invalid("repeated Go requirement", source));
                }
            }
            _ => return Err(invalid("Go requirement", source)),
        }
    }
    if !module || !go || block {
        return Err(invalid("Go module boundary", source));
    }
    Ok(Extracted {
        packages,
        local_packages: BTreeSet::new(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn independent_python_pin_and_name_answers() {
        let hash = "a".repeat(64);
        let source = format!(
            "# resolved pins\nExample_Package.Name==1.2.3 ; python_version < '3.13' \\\n  --hash=sha256:{hash}\nother==2.0+local\n"
        );
        assert_eq!(
            python(source.as_bytes()).unwrap(),
            Extracted {
                packages: [
                    package(Ecosystem::PyPI, "example-package-name", "1.2.3"),
                    package(Ecosystem::PyPI, "other", "2.0+local")
                ]
                .into(),
                local_packages: BTreeSet::new()
            }
        );
        assert!(python(b"# bundled parser\n").unwrap().packages.is_empty());
        assert_eq!(
            python(b"pkg==1!2.0\n").unwrap().packages,
            [package(Ecosystem::PyPI, "pkg", "1!2.0")].into()
        );
        assert_eq!(canonical_python_name("A__B..C-D"), Some("a-b-c-d".into()));
        for name in ["", "-bad", "bad_", "bad/name", "é", "[extra]"] {
            assert_eq!(canonical_python_name(name), None);
        }
        for source in [
            "pkg>=1.2",
            "pkg===1.2",
            "pkg==",
            "pkg==1.2 --option",
            "pkg==not-a-version1",
            "pkg==1.2\npkg==1.2",
            "pkg==1.2 \\",
            "--hash=sha256:abcd",
            "pkg==1.2 \\\npkg2==2.0",
            "pkg==1.2 \\\n--hash=sha256:abcd",
        ] {
            assert!(
                python(source.as_bytes()).is_err(),
                "malformed pin passed: {source}"
            );
        }
        let error = python(&[0xff]).unwrap_err();
        assert!(
            error.contains("source sha256")
                && error.contains("bytes 0:1")
                && !error.contains("line")
                && !error.contains("column")
        );
    }

    #[test]
    fn cargo_root_registry_and_source_boundaries() {
        let manifest = b"[package]\nname='local-control'\nversion='0.1.0'\n";
        let source = format!(
            "version=4\n[[package]]\nname='local-control'\nversion='0.1.0'\n[[package]]\nname='remote-control'\nversion='1.2.3+build'\nsource='registry+https://github.com/rust-lang/crates.io-index'\nchecksum='{}'\n",
            "a".repeat(64)
        );
        assert_eq!(
            cargo(source.as_bytes(), manifest).unwrap(),
            Extracted {
                packages: [package(Ecosystem::Crates, "remote-control", "1.2.3+build")].into(),
                local_packages: [package(Ecosystem::Crates, "local-control", "0.1.0")].into()
            }
        );
        for modified in [
            source.replace("1.2.3+build", "not-a-version1"),
            source.replace("version=4", "version=2"),
            source.replace("checksum=", "missing="),
            source.replace(
                "registry+https://github.com/rust-lang/crates.io-index",
                "git+https://example.invalid/repository",
            ),
            source.replace("name='local-control'", "name='unregistered-control'"),
            source.replace(&"a".repeat(64), &"g".repeat(64)),
            source.clone() + "[[package]]\nname='local-control'\nversion='0.1.0'\n",
        ] {
            assert!(cargo(modified.as_bytes(), manifest).is_err());
        }
        assert!(cargo(b"version=4\npackage=[]", manifest).is_err());
        assert!(cargo(source.as_bytes(), b"[package]").is_err());
    }

    #[test]
    fn go_declaration_and_standard_library_answers() {
        let source = b"module example.org/local\ngo 1.26.10\nrequire (\nexample.org/a v1.2.3 // indirect\n)\nrequire example.org/b/v2 v2.0.0\n";
        assert_eq!(
            go(source).unwrap(),
            Extracted {
                packages: [
                    package(Ecosystem::Go, "stdlib", "1.26.10"),
                    package(Ecosystem::Go, "example.org/a", "v1.2.3"),
                    package(Ecosystem::Go, "example.org/b/v2", "v2.0.0")
                ]
                .into(),
                local_packages: BTreeSet::new()
            }
        );
        for source in [
            "",
            "module a\ngo 1.26",
            "module a\ngo 01.26.10",
            "module a\ngo 1.26.10\nrequire a vnot-a-version1",
            "module a\ngo 1.26.10\nrequire (",
            "module a\ngo 1.26.10\nreplace a => b",
            "module a\ngo 1.26.10\nrequire a 1.2.3",
            "module a\ngo 1.26.10\nrequire a v1.2.3\nrequire a v1.2.3",
            "module a\ngo 1.26.10\ngo 1.26.10",
        ] {
            assert!(
                go(source.as_bytes()).is_err(),
                "unsupported Go declaration passed: {source}"
            );
        }
    }

    #[test]
    fn go_graph_scope_accepts_modern_declarations_and_refuses_legacy_fallbacks() {
        let boundary =
            go(b"module example.org/local\ngo 1.17.0\nrequire example.org/dep v0.1.0\n").unwrap();
        assert_eq!(
            boundary.packages,
            [
                package(Ecosystem::Go, "stdlib", "1.17.0"),
                package(Ecosystem::Go, "example.org/dep", "v0.1.0")
            ]
            .into()
        );
        for version in ["1.16.15", "1.0.0", "1.17", "1.26"] {
            assert!(
                go(format!(
                    "module example.org/local\ngo {version}\nrequire example.org/dep v0.1.0\n"
                )
                .as_bytes())
                .is_err(),
                "unsupported Go graph scope accepted: {version}"
            );
        }
    }

    #[test]
    fn malformed_owner_diagnostics_identify_manifest_bytes() {
        let source = b"version=4\n[[package]]\nname='local-control'\nversion='0.1.0'\n";
        let valid = b"[package]\nname='local-control'\nversion='0.1.0'\n";
        let accepted = cargo(source, valid).unwrap();
        assert!(accepted.packages.is_empty());
        assert_eq!(
            accepted.local_packages,
            [package(Ecosystem::Crates, "local-control", "0.1.0")].into()
        );
        for owner in [
            b"[workspace]\n".as_slice(),
            b"[package]\nversion='0.1.0'\n".as_slice(),
            b"[package]\nname='local-control'\n".as_slice(),
        ] {
            let error = cargo(source, owner).unwrap_err();
            assert!(
                error.contains(&sha256(owner)),
                "manifest failure identified the wrong source: {error}"
            );
            assert!(!error.contains(&sha256(source)));
            assert!(error.contains(&format!("bytes 0:{}", owner.len())));
        }
    }
}
