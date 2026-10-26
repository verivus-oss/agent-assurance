"""Symbol results retain stable identities and omit parser coordinates."""

from _test_require import require
from validate_code_symbols import SymbolRef, result_summary


if __name__ == "__main__":
    source = SymbolRef("CODE:1", "src/component.rs", "process", "rust")
    result = result_summary(source, [{"qualified_name": "component::process", "kind": "function",
                                      "start_line": 7, "start_column": 4}])
    require(result["matches"] == [{"qualified_name": "component::process", "kind": "function"}])
    require(result["path"] == "src/component.rs" and result["symbol"] == "process")
    print("symbol output: durable identity retained without parser coordinates")
