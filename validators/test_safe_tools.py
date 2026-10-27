"""Accepted and rejected declarations for the safe native tooling gate."""
from pathlib import Path
from tempfile import TemporaryDirectory

from _test_require import expect_raises, require
from check_safe_tools import check, go_unsafe_import, rust_has_forbid, rust_unsafe_keyword

def test_rust() -> None:
    require(rust_has_forbid('#![forbid(unsafe_code)]\nfn main() {}'))
    require(not rust_has_forbid('// #![forbid(unsafe_code)]\nfn main() {}'))
    require(not rust_has_forbid('/*\n#![forbid(unsafe_code)]\n*/\nfn main() {}'))
    require(not rust_has_forbid('/* outer /*\n#![forbid(unsafe_code)]\n*/ inner */\nfn main() {}'))
    require(not rust_has_forbid('const NOTE: &str = r#"\n#![forbid(unsafe_code)]\n"#;'))
    require(not rust_has_forbid('fn main() {}\n#![forbid(unsafe_code)]'))
    require(not rust_unsafe_keyword('// unsafe fn ignored() {}\nconst NOTE: &str = "unsafe fn";'))
    require(not rust_unsafe_keyword('const NOTE: &str = r#"unsafe {"#; /* unsafe fn */ fn main() {}'))
    require(rust_unsafe_keyword('fn main() { unsafe { touch(); } }'))
    require(rust_unsafe_keyword('/* safe */ unsafe fn touch() {}'))


def test_rust_roots() -> None:
    with TemporaryDirectory(prefix="safe-tools-") as work:
        root = Path(work)
        crate = root / "tools" / "example"
        source = crate / "src"
        source.mkdir(parents=True)
        (crate / "Cargo.toml").write_text('[package]\nname="example"\nversion="0.1.0"\n')
        (crate / "go.mod").write_text("module example\n")
        (crate / "main.go").write_text("package main\n")
        main = source / "main.rs"
        lib = source / "lib.rs"
        helper = source / "helper.rs"
        main.write_text("#![forbid(unsafe_code)]\nfn main() {}\n")
        lib.write_text("pub fn safe() {}\n")
        try:
            check(root)
        except ValueError as exc:
            require("lacks a forbid" in str(exc))
        else:
            raise AssertionError("unprotected Rust lib root passed")
        lib.write_text("#![forbid(unsafe_code)]\npub fn safe() {}\n")
        helper.write_text("unsafe fn touch() {}\n")
        try:
            check(root)
        except ValueError as exc:
            require("unsafe keyword" in str(exc))
        else:
            raise AssertionError("uncompiled unsafe Rust source passed")
        helper.write_text("// unsafe fn touch() {}\npub fn safe() {}\n")
        require(check(root) == (1, 1))

def test_go() -> None:
    require(not go_unsafe_import('package x\nimport "fmt"\n// import "unsafe"'))
    require(go_unsafe_import('package x\nimport "unsafe"'))
    require(go_unsafe_import('package x\nimport (\n "fmt"\n _ "unsafe"\n)'))
    require(go_unsafe_import('package x\nimport alias /* note */ "unsafe"'))
    require(go_unsafe_import('package x\nimport (\n alias "unsafe"\n)'))
    require(go_unsafe_import('package x\nimport /* note */ (`unsafe`)'))
    require(not go_unsafe_import('package x\n/* import alias "unsafe" */\nimport "fmt"'))
    require(not go_unsafe_import('package x\nconst note = `import "unsafe"`\nimport "fmt"'))
    expect_raises(ValueError, lambda: go_unsafe_import('package x\nimport "un\\u0073afe"'),
                  'escaped Go import path was accepted without review')
if __name__ == '__main__':
    test_rust()
    test_rust_roots()
    test_go()
    print('safe tools: accepted and rejected declarations passed')
