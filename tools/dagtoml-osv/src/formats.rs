// The complete lockfile preset is recorded in data/extractor-scope.toml.
// Recognize the supplier population first, then admit implemented extractors.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum Kind {
    Cargo,
    Go,
    Python,
    Unsupported,
}

const NAMED_FORMATS: &[(&str, &[&str])] = &[
    ("cpp/conanlock", &["conan.lock"]),
    ("erlang/mixlock", &["mix.lock"]),
    ("dart/pubspec", &["pubspec.lock"]),
    ("dart/packageconfig", &["package_config.json"]),
    ("golang/gomod", &["go.mod"]),
    (
        "java/gradlelockfile",
        &["gradle.lockfile", "buildscript-gradle.lockfile"],
    ),
    ("java/pomxml", &["pom.xml"]),
    (
        "javascript/packagelockjson",
        &["package-lock.json", "npm-shrinkwrap.json"],
    ),
    ("javascript/pnpmlock", &["pnpm-lock.yaml"]),
    ("javascript/yarnlock", &["yarn.lock"]),
    ("javascript/bunlock", &["bun.lock", "bun.lockb"]),
    ("php/composerlock", &["composer.lock"]),
    ("python/pipfilelock", &["Pipfile.lock"]),
    ("python/pdmlock", &["pdm.lock"]),
    ("python/poetrylock", &["poetry.lock"]),
    ("python/pylock", &["pylock.toml"]),
    ("python/uvlock", &["uv.lock"]),
    ("r/renvlock", &["renv.lock"]),
    ("ruby/gemfilelock", &["Gemfile.lock", "gems.locked"]),
    ("swift/packageresolved", &["Package.resolved"]),
    ("rust/cargolock", &["Cargo.lock"]),
    (
        "dotnet/nugetcpm",
        &["Directory.Packages.props", "Directory.Build.props"],
    ),
    ("dotnet/packagesconfig", &["packages.config"]),
    ("dotnet/packageslockjson", &["packages.lock.json"]),
    ("haskell/cabal", &["cabal.project.freeze"]),
    ("haskell/stacklock", &["stack.yaml.lock"]),
    ("osv/osvscannerjson", &["osv-scanner-custom.json"]),
];

fn recognized(path: &str) -> Option<&'static str> {
    let basename = path.rsplit('/').next().unwrap_or(path);
    if basename.ends_with(".txt")
        && (basename.contains("requirements") || path.starts_with("requirements/"))
    {
        return Some("python/requirements");
    }
    if let Some((format, _)) = NAMED_FORMATS
        .iter()
        .find(|(_, names)| names.contains(&basename))
    {
        return Some(format);
    }
    if basename.starts_with("pylock.") && basename.ends_with(".toml") {
        return Some("python/pylock");
    }
    if path == "gradle/verification-metadata.xml"
        || path.ends_with("/gradle/verification-metadata.xml")
    {
        return Some("java/gradleverificationmetadataxml");
    }
    if basename.ends_with(".pom") {
        return Some("java/pomxml");
    }
    if [".csproj", ".vbproj", ".fsproj"]
        .iter()
        .any(|suffix| basename.ends_with(suffix))
    {
        return Some("dotnet/csproj");
    }
    if basename.ends_with(".deps.json") {
        return Some("dotnet/depsjson");
    }
    if [
        "lib/apk/db/installed",
        "var/lib/apk/db/installed",
        "usr/lib/apk/db/installed",
    ]
    .contains(&path)
    {
        return Some("os/apk");
    }
    if ["var/lib/dpkg/status", "usr/lib/opkg/status"].contains(&path)
        || path.starts_with("var/lib/dpkg/status.d/") && !basename.ends_with(".md5sums")
    {
        return Some("os/dpkg");
    }
    let lower = basename.to_ascii_lowercase();
    if ["bom.json", "bom.xml"].contains(&lower.as_str())
        || [".cdx.json", ".cdx.xml"]
            .iter()
            .any(|suffix| lower.ends_with(suffix))
    {
        return Some("sbom/cdx");
    }
    if lower.ends_with(".spdx") || lower.contains(".spdx.") {
        return Some("sbom/spdx");
    }
    None
}

pub(crate) fn classify(path: &str) -> Option<Kind> {
    recognized(path).map(|format| match format {
        "rust/cargolock" => Kind::Cargo,
        "golang/gomod" => Kind::Go,
        "python/requirements" => Kind::Python,
        _ => Kind::Unsupported,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pinned_entry_point_inventory_equals_the_recognized_extractor_population() {
        use std::collections::BTreeSet;
        let source = include_str!("../data/extractor-scope.toml");
        let data: toml::Value = toml::from_str(source).unwrap();
        assert_eq!(data["schema_version"].as_integer(), Some(1));
        assert_eq!(
            data["scanner_commit"].as_str(),
            Some("bfe2f84abd2f09fe0b83ba7f6dad40d296762f40")
        );
        assert_eq!(
            data["supplier_commit"].as_str(),
            Some("5be78a00e3c294c19a0b03949e4eb643653c0218")
        );
        let rows = data["extractor"].as_array().unwrap();
        let inventory: BTreeSet<_> = rows
            .iter()
            .map(|row| row["name"].as_str().unwrap())
            .collect();
        let governed: BTreeSet<_> = NAMED_FORMATS
            .iter()
            .map(|(name, _)| *name)
            .chain([
                "python/requirements",
                "java/gradleverificationmetadataxml",
                "dotnet/csproj",
                "dotnet/depsjson",
                "os/apk",
                "os/dpkg",
                "sbom/cdx",
                "sbom/spdx",
            ])
            .collect();
        assert_eq!(inventory, governed);
        assert_eq!(rows.len(), inventory.len());
        assert_eq!(rows.len(), 35);
        let admitted: BTreeSet<_> = rows
            .iter()
            .filter(|row| row["action"].as_str() == Some("extract"))
            .map(|row| row["name"].as_str().unwrap())
            .collect();
        assert_eq!(
            admitted,
            BTreeSet::from(["rust/cargolock", "golang/gomod", "python/requirements"])
        );
        for row in rows {
            assert!(matches!(row["action"].as_str(), Some("extract" | "reject")));
            let blob = row["blob"].as_str().unwrap();
            assert_eq!(blob.len(), 40);
            assert!(
                blob.bytes()
                    .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
            );
            assert!(row["source"].as_str().unwrap().ends_with(".go"));
            assert_eq!(
                row["supplier"].as_str(),
                Some(if row["name"].as_str() == Some("osv/osvscannerjson") {
                    "osv-scanner"
                } else {
                    "osv-scalibr"
                })
            );
        }
    }

    #[test]
    fn implemented_subjects_and_neighboring_non_sources_are_distinct() {
        for (path, expected) in [
            ("nested/Cargo.lock", Kind::Cargo),
            ("nested/go.mod", Kind::Go),
            ("requirements.txt", Kind::Python),
            ("requirements/native.txt", Kind::Python),
            ("nested/requirements-dev.txt", Kind::Python),
            ("nested/my-requirements.txt", Kind::Python),
        ] {
            assert_eq!(classify(path), Some(expected), "{path}");
        }
        for path in [
            "reference/database/engine-lock.toml",
            "requirements.in",
            "requirements/notes.md",
            "nested/Requirements.txt",
            "nested/package-lock.json.backup",
            "nested/project.csproj.md",
            "nested/project.deps.json.md",
            "nested/pylock-production.toml",
            "nested/verification-metadata.xml",
            "var/lib/dpkg/status.d/package.md5sums",
            "docs/status",
            "project.cdx.json.md",
        ] {
            assert_eq!(classify(path), None, "{path}");
        }
        assert_eq!(
            classify("node_modules/nested/package-lock.json"),
            Some(Kind::Unsupported)
        );
        assert_eq!(
            classify("project.spdx.unsupported"),
            Some(Kind::Unsupported)
        );
    }
}
