#![forbid(unsafe_code)]

use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

use dagtoml_osv::{
    build_support,
    source::{Git, Snapshot},
};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct Fixture {
    root: PathBuf,
    git: Git,
}

impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.root);
    }
}

impl Fixture {
    fn new() -> Self {
        let nonce = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "dagtoml-osv-control-{}-{nonce}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        let fixture = Self {
            root: root.canonicalize().unwrap(),
            git: Git::new().unwrap(),
        };
        fixture.command(&["init", "--quiet"]);
        fixture
    }

    fn command(&self, arguments: &[&str]) -> Vec<u8> {
        self.git.require_unchanged().unwrap();
        let mut command = Command::new(&self.git.path);
        command.current_dir(&self.root);
        for (key, _) in std::env::vars_os() {
            if key.to_string_lossy().starts_with("GIT_") {
                command.env_remove(key);
            }
        }
        let result = command
            .env("GIT_CONFIG_NOSYSTEM", "1")
            .env("GIT_CONFIG_GLOBAL", "/dev/null")
            .args([
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "user.name=Advisory controls",
                "-c",
                "user.email=controls@example.invalid",
            ])
            .args(arguments)
            .output()
            .unwrap();
        assert!(result.status.success(), "fixture Git setup failed");
        self.git.require_unchanged().unwrap();
        result.stdout
    }

    fn write(&self, path: &str, bytes: &[u8]) {
        let target = self.root.join(path);
        std::fs::create_dir_all(target.parent().unwrap()).unwrap();
        std::fs::write(target, bytes).unwrap();
    }

    fn commit(&self) {
        self.command(&["add", "--all"]);
        self.command(&[
            "commit",
            "--quiet",
            "--no-gpg-sign",
            "-m",
            "advisory control",
        ]);
    }
    fn capture(&self) -> Result<Snapshot, String> {
        Snapshot::capture(&self.root, &self.git)
    }

    fn instrument(&self) {
        let root = Path::new(env!("CARGO_MANIFEST_DIR"));
        let records = build_support::snapshot(root).unwrap();
        assert!(!records.is_empty());
        for (relative, _) in records {
            self.write(
                &format!("tools/dagtoml-osv/{relative}"),
                &std::fs::read(root.join(relative)).unwrap(),
            );
        }
        dagtoml_osv::require_current_instrument(&self.root.join("tools/dagtoml-osv")).unwrap();
    }
}

#[test]
fn exact_tracked_population_and_missing_or_changed_source() {
    let fixture = Fixture::new();
    fixture.write("requirements.txt", b"Example_Package==1!2.0\n");
    fixture.commit();
    let before = fixture.capture().unwrap();
    assert_eq!(before.tree_state, "clean");
    assert_eq!(before.subjects.len(), 1);
    assert_eq!(before.tracked_population, 1);
    let package = before.packages().into_iter().next().unwrap();
    assert_eq!(
        (package.name.as_str(), package.version.as_str()),
        ("example-package", "1!2.0")
    );
    assert_eq!(before.subjects[0].packages.len(), 1);
    fixture.write("requirements.txt", b"Example_Package==2.0\n");
    let after = fixture.capture().unwrap();
    assert_ne!(after, before);
    assert_eq!(after.source_commit, before.source_commit);
    assert_ne!(
        after.subjects[0].source_sha256,
        before.subjects[0].source_sha256
    );
    std::fs::remove_file(fixture.root.join("requirements.txt")).unwrap();
    assert!(fixture.capture().is_err());
}

#[test]
fn absent_subjects_and_external_packages_fail() {
    for (path, bytes) in [
        ("ordinary.txt", b"ordinary source\n".as_slice()),
        ("requirements.txt", b"# no runtime packages\n".as_slice()),
    ] {
        let fixture = Fixture::new();
        fixture.write(path, bytes);
        fixture.commit();
        assert_eq!(
            fixture.capture().unwrap_err(),
            "advisory source or external package population is absent"
        );
    }
}

#[test]
fn symlink_sources_and_ancestors_fail() {
    for ancestor in [false, true] {
        let fixture = Fixture::new();
        let path = if ancestor {
            "requirements/inner/pins.txt"
        } else {
            "requirements.txt"
        };
        fixture.write(path, b"package==1.0\n");
        fixture.commit();
        assert_eq!(fixture.capture().unwrap().subjects.len(), 1);
        if ancestor {
            std::fs::rename(
                fixture.root.join("requirements/inner"),
                fixture.root.join("outside"),
            )
            .unwrap();
            std::os::unix::fs::symlink(
                fixture.root.join("outside"),
                fixture.root.join("requirements/inner"),
            )
            .unwrap();
        } else {
            std::fs::rename(fixture.root.join(path), fixture.root.join("outside.txt")).unwrap();
            std::os::unix::fs::symlink(fixture.root.join("outside.txt"), fixture.root.join(path))
                .unwrap();
        }
        assert_eq!(
            fixture.capture().unwrap_err(),
            "advisory source is symlinked, nonregular or exceeds its bound"
        );
    }
}

#[test]
fn newly_tracked_sources_are_derived_and_unsupported_formats_fail() {
    let fixture = Fixture::new();
    fixture.write("requirements.txt", b"package==1.0\n");
    fixture.commit();
    assert_eq!(fixture.capture().unwrap().subjects.len(), 1);
    fixture.write("requirements/new.txt", b"different==2.0\n");
    fixture.commit();
    let expanded = fixture.capture().unwrap();
    assert_eq!(expanded.subjects.len(), 2);
    assert_eq!(expanded.packages().len(), 2);
    fixture.write("nested/package-lock.json", b"{}\n");
    fixture.commit();
    assert_eq!(
        fixture.capture().unwrap_err(),
        "advisory source format needs an implemented extractor: nested/package-lock.json"
    );
}

#[test]
fn requirements_filename_variants_are_discovered() {
    for path in [
        "nested/requirements-dev.txt",
        "nested/my-requirements.txt",
        "nested/the_requirements_for_test.txt",
        "nested/requirements.prod.txt",
    ] {
        let fixture = Fixture::new();
        fixture.write("requirements.txt", b"original==1.0\n");
        fixture.write(path, b"additional==2.0\n");
        fixture.commit();
        let subject = fixture.capture().unwrap();
        assert_eq!(
            subject.subjects.len(),
            2,
            "omitted requirement source: {path}"
        );
        assert_eq!(subject.packages().len(), 2);
        assert!(subject.subjects.iter().any(|source| source.path == path));
    }
}

#[test]
fn legacy_recognized_subjects_cannot_disappear() {
    let paths = [
        "conan.lock",
        "mix.lock",
        "pubspec.lock",
        "package_config.json",
        "gradle.lockfile",
        "buildscript-gradle.lockfile",
        "gradle/verification-metadata.xml",
        "pom.xml",
        "library.pom",
        "package-lock.json",
        "npm-shrinkwrap.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lock",
        "bun.lockb",
        "composer.lock",
        "Pipfile.lock",
        "pdm.lock",
        "poetry.lock",
        "pylock.toml",
        "pylock.production.toml",
        "pylock..toml",
        "uv.lock",
        "renv.lock",
        "Gemfile.lock",
        "gems.locked",
        "Package.resolved",
        "project.csproj",
        "project.vbproj",
        "project.fsproj",
        "project.deps.json",
        "Directory.Packages.props",
        "Directory.Build.props",
        "packages.config",
        "packages.lock.json",
        "cabal.project.freeze",
        "stack.yaml.lock",
        "osv-scanner-custom.json",
        "lib/apk/db/installed",
        "var/lib/apk/db/installed",
        "usr/lib/apk/db/installed",
        "var/lib/dpkg/status",
        "usr/lib/opkg/status",
        "var/lib/dpkg/status.d/package",
        "bom.json",
        "BOM.XML",
        "project.cdx.json",
        "PROJECT.CDX.XML",
        "project.spdx",
        "project.spdx.json",
        ".spdx.project.yml",
        "project.spdx.rdf",
        "project.spdx.xml",
    ];
    assert_eq!(paths.len(), 53);
    let fixture = Fixture::new();
    fixture.write("requirements.txt", b"original==1.0\n");
    fixture.commit();
    for path in paths {
        fixture.write(path, b"unsupported source must not be silently omitted\n");
        fixture.commit();
        assert_eq!(
            fixture.capture().unwrap_err(),
            format!("advisory source format needs an implemented extractor: {path}")
        );
        std::fs::remove_file(fixture.root.join(path)).unwrap();
        fixture.commit();
    }
}

#[test]
fn cargo_ownership_requires_a_tracked_manifest() {
    let fixture = Fixture::new();
    fixture.write("requirements.txt", b"package==1.0\n");
    fixture.write(
        "nested/Cargo.lock",
        b"version=4\n[[package]]\nname='local'\nversion='0.1.0'\n",
    );
    fixture.commit();
    assert_eq!(
        fixture.capture().unwrap_err(),
        "Cargo lock has no tracked regular owning manifest"
    );
    fixture.write(
        "nested/Cargo.toml",
        b"[package]\nname='local'\nversion='0.1.0'\n",
    );
    assert_eq!(
        fixture.capture().unwrap_err(),
        "Cargo lock has no tracked regular owning manifest"
    );
    fixture.commit();
    let snapshot = fixture.capture().unwrap();
    assert_eq!(snapshot.subjects.len(), 2);
    assert_eq!(
        snapshot
            .subjects
            .iter()
            .map(|subject| subject.local_packages.len())
            .sum::<usize>(),
        1
    );
    assert_eq!(snapshot.packages().len(), 1);
}

#[test]
fn cli_rejects_dirty_subjects_before_retrieval() {
    let fixture = Fixture::new();
    fixture.instrument();
    fixture.commit();
    fixture.write("untracked.txt", b"dirty\n");
    let output = Command::new(env!("CARGO_BIN_EXE_dagtoml-osv"))
        .arg(&fixture.root)
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert_eq!(
        String::from_utf8(output.stderr).unwrap(),
        "advisory evaluation incomplete: advisory verdict requires an empty Git porcelain status\n"
    );
}

#[test]
fn cli_rejects_a_stale_instrument_before_retrieval() {
    let fixture = Fixture::new();
    fixture.instrument();
    fixture.commit();
    fixture.write("tools/dagtoml-osv/README.md", b"changed instrument\n");
    fixture.commit();
    assert_eq!(
        dagtoml_osv::require_current_instrument(&fixture.root.join("tools/dagtoml-osv"))
            .unwrap_err(),
        "advisory executable differs from its complete current source; rebuild before scanning"
    );
    let output = Command::new(env!("CARGO_BIN_EXE_dagtoml-osv"))
        .arg(&fixture.root)
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert_eq!(
        String::from_utf8(output.stderr).unwrap(),
        "advisory evaluation incomplete: advisory executable differs from its complete current source; rebuild before scanning\n"
    );
}
