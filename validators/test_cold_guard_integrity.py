"""Require every cold instrument to detect swallowed forbidden imports."""

import _ast as ast
import builtins
import errno
import os
import sys
import time

from _credential_git import git
from _posix_process import run
from _literal_path import Path
from _random_id import random_id_hex
from _test_require import expect_raises, require


DIAGNOSTICS = {
    'test_literal_ast_cold_start.py': 'AST component suppressed forbidden import attempts: ',
    'test_credential_cold_start.py': 'credential component suppressed forbidden import attempts: ',
    'test_literal_json_cold_start.py': 'JSON component suppressed forbidden import attempts: ',
    'test_literal_records_cold_start.py': 'record component suppressed forbidden import attempts: ',
    'test_path_primitives_cold_start.py': 'path component suppressed forbidden import attempts: ',
    'test_reference_store_cold_start.py': 'reference store suppressed forbidden import attempts: ',
}


def walk(tree):
    pending = [tree]
    while pending:
        node = pending.pop()
        yield node
        for name in node._fields:
            value = getattr(node, name, None)
            if isinstance(value, ast.AST):
                pending.append(value)
            elif isinstance(value, list):
                pending.extend(child for child in value if isinstance(child, ast.AST))


def zero_index(node):
    return (isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant)
            and type(node.slice.value) is int and node.slice.value == 0)


def import_root_expression(node):
    if not zero_index(node) or not isinstance(node.value, ast.Call):
        return False
    call = node.value
    if (not isinstance(call.func, ast.Attribute) or call.func.attr != 'split' or call.keywords
            or len(call.args) != 1 or not isinstance(call.args[0], ast.Constant) or call.args[0].value != '.'):
        return False
    receiver = call.func.value
    return zero_index(receiver) and isinstance(receiver.value, ast.Name) and receiver.value.id == 'arguments'


def forbidden_roots(source):
    tree = compile(source, '<cold-guard-source>', 'exec', flags=ast.PyCF_ONLY_AST, dont_inherit=True)
    named = [node.value for node in walk(tree) if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == 'retired' for target in node.targets)]
    candidates = []
    for node in walk(tree):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1 or not isinstance(node.ops[0], ast.In):
            continue
        if not import_root_expression(node.left):
            continue
        operand = node.comparators[0]
        if isinstance(operand, ast.Name):
            require(operand.id == 'retired' and len(named) == 1, 'cold guard root binding is ambiguous')
            operand = named[0]
        require(isinstance(operand, (ast.Tuple, ast.Set)), 'cold guard roots require a literal tuple or set')
        require(operand.elts and all(isinstance(value, ast.Constant) and type(value.value) is str and value.value.isidentifier()
                                     for value in operand.elts), 'cold guard roots require nonempty literal names')
        candidates.append({value.value for value in operand.elts})
    require(len(candidates) == 1 and {'re', 'regex', '_sre'} <= candidates[0], 'cold guard root population is absent or ambiguous')
    return candidates[0]


def test_root_derivation():
    prefix = "if event == 'import' and arguments[0].split('.')[0] in "
    expected = {'re', 'regex', '_sre'}
    require(forbidden_roots(prefix + "('re', 'regex', '_sre'):\n    pass") == expected)
    require(forbidden_roots("retired = {'re', 'regex', '_sre'}\n" + prefix + 'retired:\n    pass') == expected)
    for operand in ("()", "('re',)", "('re', 'regex', '_sre', '')", "('re', 'regex', '_sre', 're.part')",
                    "('re', 'regex', '_sre', dynamic)", 'dynamic'):
        expect_raises(AssertionError, lambda: forbidden_roots(prefix + operand + ':\n    pass'),
                      'unsupported or incomplete guard roots passed')
    source = prefix + "('re', 'regex', '_sre'):\n    pass\n"
    expect_raises(AssertionError, lambda: forbidden_roots(source + source), 'ambiguous guard predicate passed')
    expect_raises(AssertionError, lambda: forbidden_roots(source.replace('arguments[0]', 'arguments[1]')),
                  'wrong import-event operand passed')
    expect_raises(AssertionError, lambda: forbidden_roots(source.replace("split('.')", "split('/')")),
                  'wrong import-root separator passed')


def require_process_cleanup(owned, children):
    require(len(owned) == 5, 'owned process descriptor population changed')
    for descriptor in owned:
        try:
            os.fstat(descriptor)
        except OSError as error:
            require(error.errno == errno.EBADF, 'owned descriptor failed outside the closed-state property')
        else:
            raise AssertionError('owned process descriptor leaked')
    for child in children:
        expect_raises(ChildProcessError, lambda: os.waitpid(child, os.WNOHANG), 'owned process was not reaped')


def test_owned_process_transport():
    def measured(command, *, expired=False, output_limit=16 * 1024 * 1024):
        owned = []
        children = []
        original_pipe, original_open = os.pipe, builtins.open
        original_spawn, original_clock = os.posix_spawn, time.monotonic

        def pipe():
            pair = original_pipe()
            owned.extend(pair)
            return pair

        def opened(*arguments, **options):
            stream = original_open(*arguments, **options)
            owned.append(stream.fileno())
            return stream

        def spawn(*arguments, **options):
            child = original_spawn(*arguments, **options)
            children.append(child)
            return child

        try:
            os.pipe, builtins.open, os.posix_spawn = pipe, opened, spawn
            if expired:
                ticks = iter((0, 121))
                time.monotonic = lambda: next(ticks)
            return run(command, output_limit=output_limit)
        finally:
            os.pipe, builtins.open, os.posix_spawn, time.monotonic = original_pipe, original_open, original_spawn, original_clock
            require_process_cleanup(owned, children)

    command = [sys.executable, '-S', '-c', "import os; os.write(1, b'O' * 131072); os.write(2, b'E' * 131072)"]
    code, stdout, stderr = measured(command)
    require(code == 0 and stdout == b'O' * 131072 and stderr == b'E' * 131072,
            'owned process did not drain both complete output streams')
    require(measured([sys.executable, '-S', '-c', 'raise SystemExit(7)']) == (7, b'', b''))
    require(measured([sys.executable, '-S', '-c', "import os; os.write(1, b'x' * 64)"], output_limit=64)
            == (0, b'x' * 64, b''))
    error = expect_raises(AssertionError,
                          lambda: measured([sys.executable, '-S', '-c', "import os; os.write(1, b'x' * 65)"], output_limit=64),
                          'excess child output produced a result')
    require(str(error) == 'child output exceeded its declared bound')
    for invalid in (0, -1, False, None):
        expect_raises(AssertionError, lambda: run([sys.executable], output_limit=invalid), 'invalid output bound passed')
    for invalid in (0, -1, False, None, float('inf'), float('nan'), 121):
        expect_raises(AssertionError, lambda: run([sys.executable], timeout=invalid), 'invalid process deadline passed')
    root = Path(__file__).resolve().parents[1]
    missing = root / '.local/cold-guard-absent' / random_id_hex()
    require(not missing.exists())
    expect_raises(FileNotFoundError, lambda: measured([str(missing)]), 'absent executable produced a result')
    error = expect_raises(AssertionError, lambda: measured([sys.executable, '-S', '-c', 'import time; time.sleep(60)'], expired=True),
                          'expired child deadline produced a result')
    require(str(error) == 'child did not complete before its deadline')


def descendant_cleanup_case(failure_mode):
    root = Path(__file__).resolve().parents[1]
    work = root / ".local/process-descendant-controls" / random_id_hex()
    work.mkdir(parents=True)
    pid_file = work / "descendant.pid"
    program = (
        "import os,sys,time\n"
        "if os.fork(): os._exit(0)\n"
        "with open(sys.argv[1], 'w') as stream: stream.write(str(os.getpid()))\n"
        "if sys.argv[2] == 'output':\n"
        " time.sleep(0.2)\n"
        " os.write(1, b'x' * 65)\n"
        "time.sleep(60)\n"
    )

    def running(pid):
        try:
            state = Path("/proc/" + str(pid) + "/stat").read_text().rpartition(")")[2].split()[0]
        except (FileNotFoundError, ProcessLookupError):
            return False
        return state not in ("Z", "X")

    descendant = None
    try:
        error = expect_raises(AssertionError,
            lambda: run([sys.executable, "-S", "-c", program, str(pid_file), failure_mode],
                        timeout=3, output_limit=64),
            "descendant holding inherited streams produced a successful result")
        expected = ("child output exceeded its declared bound" if failure_mode == "output"
                    else "child did not complete before its deadline")
        require(str(error) == expected, "descendant control failed outside its intended bound")
        require(pid_file.is_file(), "descendant did not establish its identity before the failure")
        descendant = int(pid_file.read_text())
        require(descendant > 1, "descendant identity is invalid")
        deadline = time.monotonic() + 3
        while running(descendant) and time.monotonic() < deadline:
            time.sleep(0.01)
        require(not running(descendant), "owned process descendant survived " + failure_mode)
    finally:
        if descendant is None and pid_file.is_file():
            descendant = int(pid_file.read_text())
        if descendant is not None and descendant > 1 and running(descendant):
            os.kill(descendant, 9)


def test_owned_process_descendant_cleanup():
    for failure_mode in ("deadline", "output"):
        descendant_cleanup_case(failure_mode)


def test_complete_cold_guard_population():
    root = Path(__file__).resolve().parents[1]
    raw = git(root, ['ls-files', '-z'])
    require(raw.endswith(b'\0'))
    paths = raw[:-1].decode().split('\0')
    required = {path for path in paths if path.endswith('_cold_start.py')}
    expected = {'validators/' + name for name in DIAGNOSTICS}
    require(required == expected, 'cold guard integrity does not cover the complete tracked instrument population')
    source = {path: (root / path).read_text() for path in required}
    scopes = {path: forbidden_roots(body) for path, body in source.items()}
    workspace = root / '.local/cold-guard-integrity' / random_id_hex()
    workspace.parent.mkdir(parents=True, exist_ok=True)
    git(root, ['-c', 'core.hooksPath=' + os.devnull, 'worktree', 'add', '--detach', str(workspace), 'HEAD'])
    try:
        require(git(workspace, ['rev-parse', 'HEAD']) == git(root, ['rev-parse', 'HEAD']))
        for path, body in source.items():
            (workspace / path).write_text(body)
        visited = set()
        for path in sorted(required):
            target = workspace / path
            original = source[path]
            require(original.count('    sys.setprofile(None)') == 1)
            for optimized in (False, True):
                command = [sys.executable, *(['-O'] if optimized else []), '-S', str(target)]
                code, stdout, stderr = run(command)
                require(code == 0 and stdout and not stderr,
                        'unmodified cold instrument did not execute successfully: ' + path)
                for forbidden in sorted(scopes[path]):
                    injected = ('    try:\n        __import__(' + repr(forbidden) + ')\n'
                                '    except RuntimeError:\n        pass\n\n')
                    target.write_text(original.replace('    sys.setprofile(None)', injected + '    sys.setprofile(None)'))
                    try:
                        code, _stdout, stderr = run(command)
                    finally:
                        target.write_text(original)
                    expected_failure = ('AssertionError: ' + DIAGNOSTICS[target.name] + repr([forbidden])).encode()
                    require(code == 1 and stderr.splitlines()[-1:] == [expected_failure],
                            'swallowed import did not fail its final guard property: ' + path + ' root=' + forbidden)
                    visited.add((path, optimized, forbidden))
        require(visited == {(path, optimized, forbidden) for path in required
                            for optimized in (False, True) for forbidden in scopes[path]})
    finally:
        git(root, ['-c', 'core.hooksPath=' + os.devnull, 'worktree', 'remove', '--force', str(workspace)])


if __name__ == '__main__':
    test_root_derivation()
    test_owned_process_transport()
    test_owned_process_descendant_cleanup()
    test_complete_cold_guard_population()
    print('cold guard integrity: every tracked instrument and declared forbidden root rejected swallowed imports in normal and optimized processes after unmodified controls executed')
    print('scope: guard behavior and its selected subjects; native matching internals and unrelated dependency entry points were not instrumented')
