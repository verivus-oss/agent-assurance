"""Inspect every tracked Python source for retired cold dependency imports."""

import _literal_ast as ast
import hashlib
from _literal_path import Path

from _credential_git import git
from _test_require import require


RETIRED = ("json", "dataclasses", "pathlib", "uuid", "ast", "unittest")


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


def workflow_python(source):
    """Read the literal Python shell forms currently supported by CI."""
    lines = source.splitlines()
    fragments = []
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        command = line.lstrip(' ')
        require(command not in ('python3 -', 'python -'), 'unsupported inline Python stdin')
        if not command.startswith(('python3 ', 'python ')):
            continue
        prefix = line[:len(line) - len(command)]
        if '<<' in command:
            before, separator, after = command.partition("<<'")
            require(separator and before.split()[1] == '-', 'unsupported inline Python input form')
            terminator, quote, _tail = after.partition("'")
            require(quote and terminator and all('A' <= c <= 'Z' or c == '_' for c in terminator),
                    'unsupported inline Python terminator')
            kind = 'heredoc'
        elif command.startswith(('python3 -c ', 'python -c ')):
            value = command.split(' -c ', 1)[1]
            require(value.startswith("'"), 'inline Python command requires a literal operand')
            if value != "'":
                require(value.endswith("'"), 'unterminated inline Python literal')
                fragments.append(('literal-command', value[1:-1]))
                continue
            terminator = "'"
            kind = 'literal-command'
        else:
            require(not command.startswith(('python3 - ', 'python - ')), 'unsupported inline Python stdin')
            continue
        body = []
        while index < len(lines) and lines[index] != prefix + terminator:
            require(lines[index].startswith(prefix) or not lines[index], 'inline Python indentation changed')
            body.append(lines[index][len(prefix):])
            index += 1
        require(index < len(lines), 'inline Python terminator is absent')
        index += 1
        require(body, 'inline Python subject is absent')
        fragments.append((kind, '\n'.join(body)))
    return fragments


def test_workflow_python_shapes():
    from _test_require import expect_raises

    for source in ("python3 - <<'PY'\nimport pathlib\nPY", "python3 -c '\nimport uuid\n'",
                   "python3 -c 'import dataclasses'"):
        fragments = workflow_python(source)
        require(len(fragments) == 1 and direct_retired_imports(ast.parse(fragments[0][1])))
    require(not workflow_python('python3 validators/example.py'))
    for source in ("python3 - <<'PY'\nimport os", "python3 -c 'import os", 'python3 -c "$SOURCE"', 'python3 -'):
        expect_raises(AssertionError, lambda: workflow_python(source), 'unsupported inline Python form passed')


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


def test_tracked_workflow_python_import_population():
    root = Path(__file__).resolve().parents[1]
    raw = git(root, ['ls-files', '-z'])
    require(raw.endswith(b'\0'))
    paths = raw[:-1].split(b'\0')
    required = {path.decode() for path in paths if path.startswith(b'.github/workflows/')
                and path.endswith((b'.yml', b'.yaml'))}
    require(required and '.github/workflows/validate.yml' in required)
    visited = set()
    selected = set()
    kinds = set()
    for relative in sorted(required):
        source = (root / relative).read_bytes()
        for kind, fragment in workflow_python(source.decode()):
            require(not direct_retired_imports(ast.parse(fragment)),
                    'retired inline workflow dependency: ' + relative + ' SHA256 ' + hashlib.sha256(source).hexdigest())
            kinds.add(kind)
            selected.add(relative)
        visited.add(relative)
    require(visited == required and '.github/workflows/validate.yml' in selected)
    require(kinds == {'heredoc', 'literal-command'})


if __name__ == "__main__":
    test_import_shapes()
    test_workflow_python_shapes()
    test_tracked_python_import_population()
    test_tracked_workflow_python_import_population()
    print("cold import boundary: complete tracked Python and workflow literal-Python populations and accepted/rejected shapes checked")
