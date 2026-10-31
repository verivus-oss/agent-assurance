#![forbid(unsafe_code)]

use std::path::{Path, PathBuf};

use dagtoml_osv::{digest, https::Native};
use serde_json::Value;

struct Fixture(PathBuf);

impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

fn copy_tree(source: &Path, target: &Path) {
    std::fs::create_dir_all(target).unwrap();
    for entry in std::fs::read_dir(source).unwrap() {
        let entry = entry.unwrap();
        let kind = entry.file_type().unwrap();
        if kind.is_dir() {
            copy_tree(&entry.path(), &target.join(entry.file_name()));
        } else {
            assert!(kind.is_file(), "fixture source is not a regular file");
            std::fs::copy(entry.path(), target.join(entry.file_name())).unwrap();
        }
    }
}

fn set_record(path: &Path, value: &Value) {
    std::fs::write(path, serde_json::to_vec(value).unwrap()).unwrap();
}

#[test]
#[ignore = "requires the current native HTTPS artifact; CI runs this explicitly"]
fn actual_artifact_requires_complete_current_inputs_and_executed_identity() {
    let checkout = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap();
    Native::new(checkout).expect("build the current native HTTPS producer before these controls");
    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let fixture = Fixture(std::env::temp_dir().join(format!(
        "dagtoml-https-artifact-{}-{nonce}",
        std::process::id()
    )));
    for module in ["dagtoml-osv-http-go", "dagtoml-postgres-go"] {
        copy_tree(
            &checkout.join("tools").join(module),
            &fixture.0.join("tools").join(module),
        );
    }
    let artifact = fixture.0.join(".local/osv-https");
    std::fs::create_dir_all(&artifact).unwrap();
    for name in ["dagtoml-osv-http-go", "dagtoml-osv-http-go.build.json"] {
        std::fs::copy(
            checkout.join(".local/osv-https").join(name),
            artifact.join(name),
        )
        .unwrap();
    }
    let accepted = Native::new(&fixture.0).unwrap();
    accepted.require_unchanged().unwrap();
    let record_path = artifact.join("dagtoml-osv-http-go.build.json");
    let original: Value = serde_json::from_slice(&std::fs::read(&record_path).unwrap()).unwrap();
    let mut observed_sources = 0;
    for (key, module) in [
        ("sources", "dagtoml-osv-http-go"),
        ("builder_sources", "dagtoml-postgres-go"),
    ] {
        let population = original[key].as_array().unwrap();
        assert!(!population.is_empty());
        for (index, file) in population.iter().enumerate() {
            let path = fixture
                .0
                .join("tools")
                .join(module)
                .join(file["path"].as_str().unwrap());
            let data = std::fs::read(&path).unwrap();
            std::fs::remove_file(&path).unwrap();
            assert!(
                Native::new(&fixture.0).is_err(),
                "missing source was admitted"
            );
            std::fs::write(&path, &data).unwrap();
            let mut changed = data.clone();
            changed.push(b'\n');
            std::fs::write(&path, changed).unwrap();
            assert!(
                accepted.require_unchanged().is_err(),
                "changed source was admitted"
            );
            std::fs::write(&path, &data).unwrap();
            let mut omitted = original.clone();
            omitted[key].as_array_mut().unwrap().remove(index);
            set_record(&record_path, &omitted);
            assert!(
                Native::new(&fixture.0).is_err(),
                "omitted roster member was admitted"
            );
            set_record(&record_path, &original);
            observed_sources += 1;
        }
        let extra = fixture
            .0
            .join("tools")
            .join(module)
            .join("unexpected-source");
        std::fs::write(&extra, b"extra").unwrap();
        assert!(
            Native::new(&fixture.0).is_err(),
            "extra source was admitted"
        );
        std::fs::remove_file(&extra).unwrap();
        std::os::unix::fs::symlink(
            checkout.join("tools").join(module).join("README.md"),
            &extra,
        )
        .unwrap();
        assert!(
            Native::new(&fixture.0).is_err(),
            "linked source was admitted"
        );
        std::fs::remove_file(extra).unwrap();
        let mut repeated = original.clone();
        repeated[key]
            .as_array_mut()
            .unwrap()
            .push(population[0].clone());
        set_record(&record_path, &repeated);
        assert!(
            Native::new(&fixture.0).is_err(),
            "repeated roster member was admitted"
        );
        set_record(&record_path, &original);
    }
    assert_eq!(
        observed_sources,
        original["sources"].as_array().unwrap().len()
            + original["builder_sources"].as_array().unwrap().len()
    );
    for key in [
        "protocol",
        "go_version",
        "source_sha256",
        "builder_sha256",
        "compiled_graph_sha256",
        "binary_sha256",
    ] {
        let mut changed = original.clone();
        changed[key] = Value::String("changed".into());
        set_record(&record_path, &changed);
        assert!(
            Native::new(&fixture.0).is_err(),
            "changed build field was admitted: {key}"
        );
    }
    for package in ["regexp", "regexp/syntax"] {
        let mut changed = original.clone();
        changed["compiled_packages"]
            .as_array_mut()
            .unwrap()
            .push(Value::String(package.into()));
        changed["compiled_packages"]
            .as_array_mut()
            .unwrap()
            .sort_by(|a, b| a.as_str().cmp(&b.as_str()));
        set_record(&record_path, &changed);
        assert!(
            Native::new(&fixture.0).is_err(),
            "matching package was admitted"
        );
    }
    // A self-consistent altered graph still differs from the executed identity.
    let mut graph_changed = original.clone();
    graph_changed["compiled_packages"]
        .as_array_mut()
        .unwrap()
        .remove(0);
    let mut framed = b"dagtoml-stdlib-capsule-graph-v1\0".to_vec();
    for name in graph_changed["compiled_packages"].as_array().unwrap() {
        let name = name.as_str().unwrap().as_bytes();
        framed.extend_from_slice(&(name.len() as u64).to_be_bytes());
        framed.extend_from_slice(name);
    }
    graph_changed["compiled_graph_sha256"] = Value::String(digest::sha256(&framed));
    set_record(&record_path, &graph_changed);
    assert_eq!(
        Native::new(&fixture.0).unwrap_err(),
        "HTTPS executed identity differs from its complete build inputs"
    );
    set_record(&record_path, &original);
    let binary = artifact.join("dagtoml-osv-http-go");
    let data = std::fs::read(&binary).unwrap();
    let mut changed = data.clone();
    changed.push(0);
    std::fs::write(&binary, changed).unwrap();
    assert!(
        accepted.require_unchanged().is_err(),
        "changed executable was admitted"
    );
    std::fs::write(&binary, data).unwrap();
    accepted.require_unchanged().unwrap();
    println!(
        "actual HTTPS artifact controls: every producer/builder source and roster member; restored positive; graph, binary and executed identity; live archives skipped"
    );
}
