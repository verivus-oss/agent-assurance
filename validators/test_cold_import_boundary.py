"""Inspect every tracked Python source for retired cold dependency imports."""

import ast
import hashlib
from pathlib import Path

from _credential_git import git
from _test_require import require


RETIRED = ("json", "dataclasses")


def retired(name):
    return any(name == root or name.startswith(root + ".") for root in RETIRED)


def direct_retired_imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names if retired(alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            if retired(node.module):
                names.add(node.module)
    return names


def test_import_shapes():
    for root in RETIRED:
        for source in (f'import {root}', f'import {root} as alternate', f'import {root}.component',
                       f'from {root} import value', f'from {root}.component import value'):
            require(direct_retired_imports(ast.parse(source)))
    for source in ('import _json', 'import _literal_json as json',
                   'from _literal_json import loads', '# import json', 'value = "import json"',
                   'from .json import local_value', 'import jsonish', 'import dataclasses_extra',
                   'from _literal_records import Vocabulary', 'from .dataclasses import local_value'):
        require(not direct_retired_imports(ast.parse(source)))


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
        imports = direct_retired_imports(tree)
        if imports:
            observed[relative] = sorted(imports)
        visited.add(relative)
    require(visited == required)
    require(not observed, "retired cold dependency imports in tracked Python source: " + repr(observed))


if __name__ == "__main__":
    test_import_shapes()
    test_tracked_python_import_population()
    print("cold import boundary: complete tracked Python source population and accepted/rejected import shapes checked")
