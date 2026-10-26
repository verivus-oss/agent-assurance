"""Accepted and rejected declarations for the safe native tooling gate."""
from _test_require import require
from check_safe_tools import go_unsafe_import, rust_has_forbid

def test_rust() -> None:
    require(rust_has_forbid('#![forbid(unsafe_code)]\nfn main() {}'))
    require(not rust_has_forbid('// #![forbid(unsafe_code)]\nfn main() {}'))
    require(not rust_has_forbid('/*\n#![forbid(unsafe_code)]\n*/\nfn main() {}'))
    require(not rust_has_forbid('/* outer /*\n#![forbid(unsafe_code)]\n*/ inner */\nfn main() {}'))
    require(not rust_has_forbid('const NOTE: &str = r#"\n#![forbid(unsafe_code)]\n"#;'))
    require(not rust_has_forbid('fn main() {}\n#![forbid(unsafe_code)]'))

def test_go() -> None:
    require(not go_unsafe_import('package x\nimport "fmt"\n// import "unsafe"'))
    require(go_unsafe_import('package x\nimport "unsafe"'))
    require(go_unsafe_import('package x\nimport (\n "fmt"\n _ "unsafe"\n)'))
    require(go_unsafe_import('package x\nimport alias /* note */ "unsafe"'))
    require(go_unsafe_import('package x\nimport (\n alias "unsafe"\n)'))
    require(go_unsafe_import('package x\nimport /* note */ (`unsafe`)'))
    require(not go_unsafe_import('package x\n/* import alias "unsafe" */\nimport "fmt"'))
    require(not go_unsafe_import('package x\nconst note = `import "unsafe"`\nimport "fmt"'))
    try:
        go_unsafe_import('package x\nimport "un\\u0073afe"')
    except ValueError:
        pass
    else:
        raise AssertionError('escaped Go import path was accepted without review')
if __name__ == '__main__':
    test_rust()
    test_go()
    print('safe tools: accepted and rejected declarations passed')
