#![forbid(unsafe_code)]

use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};

use dagtoml_spell::digest::sha256;
use dagtoml_spell::git;
use dagtoml_spell::project::Project;

static NEXT: AtomicU64 = AtomicU64::new(0);

struct Fixture {
    root: PathBuf,
}

fn copy(source: &Path, destination: &Path, root: &Path) {
    for entry in std::fs::read_dir(source).unwrap() {
        let entry = entry.unwrap();
        let path = entry.path();
        if path == root.join("target") || path == root.join(".git") {
            continue;
        }
        let target = destination.join(entry.file_name());
        let kind = entry.file_type().unwrap();
        if kind.is_dir() {
            std::fs::create_dir(&target).unwrap();
            copy(&path, &target, root);
        } else {
            assert!(kind.is_file());
            std::fs::copy(path, target).unwrap();
        }
    }
}

impl Fixture {
    fn new() -> Self {
        let time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "spelling-command-{}-{time}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        let mut builder = std::fs::DirBuilder::new();
        #[cfg(unix)]
        {
            use std::os::unix::fs::DirBuilderExt;
            builder.mode(0o700);
        }
        builder.create(&root).unwrap();
        let package = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        let repository = package.parent().unwrap().parent().unwrap();
        std::fs::create_dir_all(root.join("tools/dagtoml-spell")).unwrap();
        copy(&package, &root.join("tools/dagtoml-spell"), &package);
        std::fs::create_dir(root.join("validators")).unwrap();
        for name in [
            "credential-rule-population.toml",
            "_credential_words.py",
            "_credential_structures.py",
            "_credential_controls.py",
        ] {
            std::fs::copy(
                repository.join("validators").join(name),
                root.join("validators").join(name),
            )
            .unwrap();
        }
        git::run(&root, &["init", "--quiet"]).unwrap();
        // This identity belongs only to the disposable repository fixture.
        git::run(&root, &["config", "user.name", "Spelling fixture"]).unwrap();
        git::run(&root, &["config", "user.email", "fixture@example.invalid"]).unwrap();
        git::run(&root, &["config", "commit.gpgsign", "false"]).unwrap();
        let fixture = Self { root };
        fixture.write("sample.md", b"ordinary accepted source\n");
        git::run(&fixture.root, &["add", "--", "sample.md"]).unwrap();
        git::run(
            &fixture.root,
            &["commit", "--quiet", "-m", "Fixture subject"],
        )
        .unwrap();
        fixture
    }

    fn write(&self, path: &str, bytes: &[u8]) {
        std::fs::write(self.root.join(path), bytes).unwrap();
    }

    fn run(&self, options: &[&str], input: Option<&[u8]>) -> (i32, toml::Value) {
        let mut command = Command::new(env!("CARGO_BIN_EXE_dagtoml-spell"));
        command
            .arg("--repo-root")
            .arg(&self.root)
            .args(options)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        let mut child = command.spawn().unwrap();
        if let Some(bytes) = input {
            child.stdin.take().unwrap().write_all(bytes).unwrap();
        } else {
            drop(child.stdin.take());
        }
        let output = child.wait_with_output().unwrap();
        assert!(output.stderr.is_empty(), "unexpected diagnostic stream");
        let text = String::from_utf8(output.stdout).unwrap();
        let report: toml::Value = toml::from_str(&text).unwrap();
        assert_no_coordinates(&report);
        (output.status.code().unwrap(), report)
    }
}

impl Drop for Fixture {
    fn drop(&mut self) {
        if let Err(error) = std::fs::remove_dir_all(&self.root) {
            if !std::thread::panicking() {
                panic!("owned spelling fixture cleanup failed: {error}");
            }
        }
    }
}

fn assert_no_coordinates(value: &toml::Value) {
    match value {
        toml::Value::Table(table) => {
            for (key, value) in table {
                assert!(!matches!(
                    key.as_str(),
                    "line" | "column" | "line_num" | "column_num"
                ));
                assert_no_coordinates(value);
            }
        }
        toml::Value::Array(values) => values.iter().for_each(assert_no_coordinates),
        _ => {}
    }
}

fn controls() -> (String, Vec<String>) {
    let corpus: toml::Value = toml::from_str(include_str!("fixtures/corrections.toml")).unwrap();
    let cases = corpus["corrections"].as_array().unwrap();
    let case = cases
        .iter()
        .find(|case| case["name"].as_str() == Some("lowercase-receive"))
        .unwrap();
    (
        case["input"].as_str().unwrap().to_owned(),
        case["expected"]
            .as_array()
            .unwrap()
            .iter()
            .map(|value| value.as_str().unwrap().to_owned())
            .collect(),
    )
}

fn array<'a>(report: &'a toml::Value, key: &str) -> &'a Vec<toml::Value> {
    report[key].as_array().unwrap()
}

fn failed(result: (i32, toml::Value), message: &str) {
    let (code, report) = result;
    assert_eq!(code, 2);
    assert_eq!(report["status"].as_str(), Some("failed"));
    let errors = array(&report, "errors");
    assert_eq!(errors.len(), 1);
    assert_eq!(errors[0]["message"].as_str(), Some(message));
}

#[test]
fn command_accepts_source_and_reproduces_content_and_filename_findings() {
    let fixture = Fixture::new();
    let (code, report) = fixture.run(&[], None);
    assert_eq!(code, 0);
    assert_eq!(report["status"].as_str(), Some("no-corrections"));
    assert_eq!(
        report["base_commit"].as_str(),
        Some(git::head(&fixture.root).unwrap().as_str())
    );
    assert_eq!(report["tree_state"].as_str(), Some("working-files"));
    assert!(array(&report, "findings").is_empty());
    assert!(array(&report, "errors").is_empty());
    let subjects = array(&report, "subjects");
    assert_eq!(subjects.len(), 1);
    assert_eq!(subjects[0]["path"].as_str(), Some("sample.md"));
    assert_eq!(subjects[0]["state"].as_str(), Some("checked"));
    let (input, expected) = controls();
    let source = format!("ordinary {input} ordinary\n");
    fixture.write("sample.md", source.as_bytes());
    let (code, report) = fixture.run(&[], None);
    assert_eq!(code, 1);
    assert!(array(&report, "errors").is_empty());
    let findings = array(&report, "findings");
    assert_eq!(findings.len(), 1);
    assert_eq!(findings[0]["source_kind"].as_str(), Some("content"));
    assert_eq!(findings[0]["token"].as_str(), Some(input.as_str()));
    assert_eq!(
        findings[0]["source_sha256"].as_str(),
        Some(sha256(source.as_bytes()).as_str())
    );
    assert_eq!(
        findings[0]["byte_span"],
        toml::Value::Array(vec![9.into(), (9 + input.len() as i64).into()])
    );
    assert_eq!(
        findings[0]["corrections"],
        toml::Value::Array(expected.into_iter().map(toml::Value::String).collect())
    );
    fixture.write("sample.md", b"ordinary accepted source\n");
    let name = format!("{input}.md");
    git::run(&fixture.root, &["mv", "--", "sample.md", &name]).unwrap();
    let (code, report) = fixture.run(&[], None);
    assert_eq!(code, 1);
    let findings = array(&report, "findings");
    assert_eq!(findings.len(), 1);
    assert_eq!(findings[0]["source_kind"].as_str(), Some("path"));
    assert_eq!(findings[0]["path"].as_str(), Some(name.as_str()));
    assert_eq!(
        findings[0]["source_sha256"].as_str(),
        Some(sha256(name.as_bytes()).as_str())
    );
}

#[test]
fn command_rejects_absent_empty_invalid_and_unclassified_input() {
    let fixture = Fixture::new();
    for (input, message) in [
        (b"".as_slice(), "spelling input subject is absent"),
        (
            b" \n\t".as_slice(),
            "spelling scan did not examine any language words",
        ),
        (
            b"123".as_slice(),
            "spelling scan did not examine any language words",
        ),
        (&[0xff], "spelling text source is not UTF-8"),
        (
            b"ordinary\0source".as_slice(),
            "spelling text has an unclassified binary control byte",
        ),
    ] {
        failed(fixture.run(&["--stdin", "probe.md"], Some(input)), message);
    }
    let (code, report) = fixture.run(&["--stdin", "probe.md"], Some(b"ordinary accepted source"));
    assert_eq!(code, 0);
    assert_eq!(array(&report, "subjects").len(), 1);
    assert!(array(&report, "findings").is_empty());
    assert!(array(&report, "errors").is_empty());
    assert!(
        report["comparison"]
            .as_str()
            .unwrap()
            .contains("filenames and tracked-file population were not scanned")
    );
    failed(
        fixture.run(&["--stdin", "../outside"], Some(b"ordinary")),
        "spelling source identity must be a repository-relative path",
    );
    std::fs::remove_file(fixture.root.join("sample.md")).unwrap();
    failed(
        fixture.run(&[], None),
        "spelling source cannot be inspected",
    );
    git::run(&fixture.root, &["rm", "--cached", "--", "sample.md"]).unwrap();
    failed(
        fixture.run(&[], None),
        "spelling source population is absent",
    );
}

#[test]
fn command_rejects_stale_instrument_and_changed_or_absent_project_data() {
    let fixture = Fixture::new();
    let path = "tools/dagtoml-spell/src/lib.rs";
    let original = std::fs::read(fixture.root.join(path)).unwrap();
    let mut changed = original.clone();
    changed.extend_from_slice(b"\n// ordinary additional source\n");
    fixture.write(path, &changed);
    failed(
        fixture.run(&[], None),
        "spelling executable differs from the current source tree; rebuild it before validation",
    );
    fixture.write(path, &original);
    let catalog = "validators/credential-rule-population.toml";
    let original = std::fs::read(fixture.root.join(catalog)).unwrap();
    let mut changed = original.clone();
    changed.extend_from_slice(b"\n# ordinary additional data\n");
    fixture.write(catalog, &changed);
    failed(
        fixture.run(&[], None),
        "spelling identity catalog differs from its pinned data",
    );
    fixture.write(catalog, &original);
    std::fs::remove_file(fixture.root.join(catalog)).unwrap();
    failed(
        fixture.run(&[], None),
        "spelling source cannot be inspected",
    );
}

#[test]
fn project_identity_rechecks_every_policy_operand_source() {
    let fixture = Fixture::new();
    let project = Project::load(&fixture.root).unwrap();
    let required: std::collections::BTreeSet<_> = [
        "tools/dagtoml-spell/data/project.toml",
        "tools/dagtoml-spell/tests/fixtures/corrections.toml",
        "validators/credential-rule-population.toml",
        "validators/_credential_words.py",
        "validators/_credential_structures.py",
        "validators/_credential_controls.py",
    ]
    .into_iter()
    .collect();
    assert_eq!(
        project
            .source_hashes()
            .keys()
            .map(String::as_str)
            .collect::<std::collections::BTreeSet<_>>(),
        required
    );
    project.verify_sources(&fixture.root).unwrap();
    for (path, digest) in project.source_hashes() {
        let original = std::fs::read(fixture.root.join(path)).unwrap();
        assert_eq!(&sha256(&original), digest);
        let mut changed = original.clone();
        changed.extend_from_slice(b"\n# ordinary additional source\n");
        fixture.write(path, &changed);
        let error = project.verify_sources(&fixture.root).unwrap_err();
        assert_eq!(error.path, *path);
        assert_eq!(
            error.message,
            "spelling project source moved during validation"
        );
        fixture.write(path, &original);
        project.verify_sources(&fixture.root).unwrap();
    }
}

#[test]
fn full_clean_fixture_is_distinct_from_a_working_file_probe() {
    let fixture = Fixture::new();
    git::run(&fixture.root, &["add", "--all"]).unwrap();
    git::run(
        &fixture.root,
        &["commit", "--quiet", "-m", "Fixture policy and source"],
    )
    .unwrap();
    assert!(
        git::run(&fixture.root, &["status", "--porcelain=v1", "-z"])
            .unwrap()
            .is_empty()
    );
    let (code, report) = fixture.run(&[], None);
    assert_eq!(code, 0);
    assert_eq!(report["tree_state"].as_str(), Some("clean"));
    assert_eq!(report["status"].as_str(), Some("no-corrections"));
    assert!(array(&report, "errors").is_empty());
    assert!(array(&report, "findings").is_empty());
    let required: std::collections::BTreeSet<_> = git::entries(
        &git::run(&fixture.root, &["ls-files", "--stage", "-z", "--full-name"]).unwrap(),
    )
    .unwrap()
    .into_iter()
    .map(|entry| entry.path)
    .collect();
    let subjects = array(&report, "subjects");
    let visited: std::collections::BTreeSet<_> = subjects
        .iter()
        .map(|subject| subject["path"].as_str().unwrap().to_owned())
        .collect();
    assert_eq!(visited, required);
    assert_eq!(subjects.len(), required.len());
    let policy = report["policy_sources"].as_table().unwrap();
    let project = Project::load(&fixture.root).unwrap();
    assert_eq!(policy.len(), project.source_hashes().len());
    for (path, digest) in project.source_hashes() {
        assert_eq!(policy[path].as_str(), Some(digest.as_str()));
    }
}

#[test]
fn a_blob_object_is_not_a_commit_identity() {
    let fixture = Fixture::new();
    let blob = git::run(&fixture.root, &["hash-object", "-w", "sample.md"]).unwrap();
    assert!(git::object_id(blob.strip_suffix(b"\n").unwrap()));
    std::fs::write(fixture.root.join(".git/refs/heads/blob-subject"), blob).unwrap();
    std::fs::write(
        fixture.root.join(".git/HEAD"),
        b"ref: refs/heads/blob-subject\n",
    )
    .unwrap();
    // The object exists and has the correct textual digest shape.
    assert!(git::run(&fixture.root, &["rev-parse", "HEAD"]).is_ok());
    failed(
        fixture.run(&[], None),
        "spelling Git operation did not complete",
    );
}
