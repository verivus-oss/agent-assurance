use std::process::Command;

fn invoke(args: &[&str]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_dagtoml-rdf"))
        .args(args)
        .output()
        .expect("RDF generator executable should start")
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
