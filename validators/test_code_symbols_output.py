"""Symbol results retain stable identities and omit parser coordinates."""

from _literal_path import Path
from types import SimpleNamespace
from _temporary_attribute import temporary_attribute, returning
import validate_code_symbols as code_symbols

from _test_require import require
from validate_code_symbols import SymbolRef, result_summary, sqry_search


if __name__ == "__main__":
    source = SymbolRef("CODE:1", "src/component.rs", "process", "rust")
    result = result_summary(source, [{"qualified_name": "component::process", "kind": "function",
                                      "start_line": 7, "start_column": 4}])
    require(result["matches"] == [{"qualified_name": "component::process", "kind": "function"}])
    require(result["path"] == "src/component.rs" and result["symbol"] == "process")
    root = Path(__file__).resolve().parent.parent
    selected = str((root / source.path).resolve())
    good = SimpleNamespace(returncode=0, stdout='{"results":[{"file_path":"' + selected + '"}]}', stderr="")
    with temporary_attribute(code_symbols.subprocess, "run", returning(good)):
        matches, detail = sqry_search("sqry", root, source)
    require(len(matches) == 1 and detail is None)

    bad = SimpleNamespace(returncode=0, stdout='{"results":[{"file_path":"/invalid-source"}]}', stderr="")
    original_resolve = Path.resolve

    def reject_bad_path(path: Path, *args: object, **kwargs: object) -> Path:
        if str(path) == "/invalid-source":
            raise OSError("injected path resolution failure")
        return original_resolve(path, *args, **kwargs)

    with temporary_attribute(code_symbols.subprocess, "run", returning(bad)), temporary_attribute(Path, "resolve", reject_bad_path):
        matches, detail = sqry_search("sqry", root, source)
    require(not matches and detail is not None and "invalid source path" in detail)
    print("symbol output: durable identity retained without parser coordinates")
