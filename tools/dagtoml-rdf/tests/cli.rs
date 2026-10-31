use std::path::Path;
use std::process::Command;

fn invoke(args: &[&str]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_dagtoml-rdf"))
        .args(args)
        .output()
        .expect("RDF generator executable should start")
}

#[test]
fn prefix_gate_requires_its_declared_subject() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap();
    assert!(
        invoke(&["check-prefix-shapes", "--repo-root", root.to_str().unwrap()])
            .status
            .success()
    );
    let absent = root.join("tools/dagtoml-rdf/no-such-prefix-root");
    assert!(!absent.exists());
    let output = invoke(&[
        "check-prefix-shapes",
        "--repo-root",
        absent.to_str().unwrap(),
    ]);
    assert_eq!(output.status.code(), Some(1));
    assert!(String::from_utf8_lossy(&output.stderr).contains("cannot read"));
    for args in [
        &["verify", "check-prefix-shapes"][..],
        &["check-prefix-shapes", "-o", "ignored.ttl"],
    ] {
        assert_eq!(invoke(args).status.code(), Some(2));
    }
}

#[test]
fn options_require_nonempty_values() {
    for args in [
        &["--repo-root"][..],
        &["--repo-root", ""],
        &["-o"],
        &["-o", ""],
    ] {
        let output = invoke(args);
        assert_eq!(output.status.code(), Some(2), "arguments: {args:?}");
        assert!(
            String::from_utf8_lossy(&output.stderr).contains("requires a path"),
            "arguments: {args:?}"
        );
    }
    assert!(invoke(&["--help"]).status.success());
}
