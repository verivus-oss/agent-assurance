"""Derive every tracked Python source and reject direct standard JSON imports."""

import ast
import hashlib
from pathlib import Path

from _credential_git import git
from _test_require import require


def direct_json_imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names
                         if alias.name == "json" or alias.name.startswith("json."))
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            if node.module == "json" or node.module.startswith("json."):
                names.add(node.module)
    return names


def test_import_shapes():
    for source in ('import json', 'import json as alternate', 'import json.scanner',
                   'from json import loads', 'from json.decoder import JSONDecoder'):
        require(direct_json_imports(ast.parse(source)))
    for source in ('import _json', 'import _literal_json as json',
                   'from _literal_json import loads', '# import json', 'value = "import json"',
                   'from .json import local_value'):
        require(not direct_json_imports(ast.parse(source)))


def test_tracked_python_import_population():
    root = Path(__file__).resolve().parents[1]
    raw = git(root, ["ls-files", "-z"])
    require(raw.endswith(b"\0"), "tracked source population has incomplete framing")
    paths = raw[:-1].split(b"\0")
    require(paths and all(paths) and len(paths) == len(set(paths)))
    required = {path.decode("utf-8") for path in paths if path.endswith(b".py")}
    require(required, "tracked Python source population is absent")
    visited = set()
    observed = {}
    for relative in sorted(required):
        source = (root / relative).read_bytes()
        try:
            tree = ast.parse(source)
        except (SyntaxError, UnicodeError):
            raise RuntimeError("cannot inspect Python source: " + relative + " SHA256 " + hashlib.sha256(source).hexdigest()) from None
        imports = direct_json_imports(tree)
        if imports:
            observed[relative] = sorted(imports)
        visited.add(relative)
    require(visited == required)
    require(not observed, "direct standard JSON imports in tracked Python source: " + repr(observed))


if __name__ == "__main__":
    test_import_shapes()
    test_tracked_python_import_population()
    print("JSON import boundary: complete tracked Python source population and accepted/rejected import shapes checked")
