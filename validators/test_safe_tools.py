"""Accepted and rejected declarations for the safe native tooling gate."""
from _test_require import require
from check_safe_tools import go_unsafe_import, rust_has_forbid

def test_rust() -> None:
    require(rust_has_forbid('#![forbid(unsafe_code)]\nfn main() {}'))
    require(not rust_has_forbid('// #![forbid(unsafe_code)]\nfn main() {}'))

def test_go() -> None:
    require(not go_unsafe_import('package x\nimport "fmt"\n// import "unsafe"'))
    require(go_unsafe_import('package x\nimport "unsafe"'))
    require(go_unsafe_import('package x\nimport (\n "fmt"\n _ "unsafe"\n)'))
if __name__ == '__main__':
    test_rust()
    test_go()
    print('safe tools: accepted and rejected declarations passed')
