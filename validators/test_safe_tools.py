"""Accepted and rejected declarations for the safe native tooling gate."""
from _literal_path import Path
from tempfile import TemporaryDirectory

from _test_require import expect_raises, require
from check_safe_tools import cargo_manifests, check, go_unsafe_import, rust_has_forbid, rust_unsafe_keyword

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


def test_cargo_population() -> None:
    with TemporaryDirectory(prefix="native-population-") as work:
        root = Path(work)
        (root / "tools").mkdir()
        expect_raises(ValueError, lambda: cargo_manifests(root), "absent manifests passed")
        required = []
        for name in ("existing", "newly-added"):
            crate = root / "tools" / name
            crate.mkdir()
            manifest = crate / "Cargo.toml"
            manifest.write_text('[package]\nname="fixture"\nversion="0.1.0"\n')
            expect_raises(ValueError, lambda: cargo_manifests(root), "missing lock passed")
            lock = crate / "Cargo.lock"
            lock.write_bytes(b"")
            expect_raises(ValueError, lambda: cargo_manifests(root), "empty lock passed")
            lock.write_text('version = 4\n')
            required.append(manifest)
            require(cargo_manifests(root) == sorted(required))
        lock = required[-1].parent / "Cargo.lock"
        lock.unlink()
        lock.symlink_to(required[0].parent / "Cargo.lock")
        expect_raises(ValueError, lambda: cargo_manifests(root), "linked lock passed")
        lock.unlink()
        lock.write_text('version = 4\n')
        required[-1].unlink()
        required[-1].symlink_to(required[0])
        expect_raises(ValueError, lambda: cargo_manifests(root), "linked manifest passed")


if __name__ == '__main__':
    test_rust()
    test_rust_roots()
    test_go()
    test_cargo_population()
    print('safe tools: accepted and rejected declarations passed')
