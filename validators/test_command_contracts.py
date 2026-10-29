"""Exercise the actual shared CLI entry points and declared discovery exclusions."""

import os
import sys

import _literal_ast as ast
from _credential_git import git
from _credential_test_support import TemporaryTree
from _literal_path import Path
from _test_require import require
from test_cold_import_boundary import workflow_python
from test_cold_guard_integrity import run


ROOT = Path(__file__).resolve().parents[1]


def parser_programs():
    programs = set()
    for raw in git(ROOT, ['ls-files', '-z']).split(b'\0'):
        if not raw.endswith(b'.py'):
            continue
        path = Path(raw.decode())
        if path.name.startswith(('test_', '_')):
            continue
        tree = ast.parse((ROOT / path).read_bytes())
        imports, wrapper = set(), False
        main = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
                if node.module == '_runtime_validation':
                    wrapper |= any(alias.name == 'cli' for alias in node.names)
            elif (isinstance(node, ast.Compare) and isinstance(node.left, ast.Name)
                  and node.left.id == '__name__'):
                main |= any(isinstance(value, ast.Constant) and value.value == '__main__'
                            for value in node.comparators)
        if main and (imports & {'_literal_args', '_argument_parser'} or wrapper):
            programs.add(path)
    require({Path('validators/validate_provenance.py'), Path('validators/validate_adapter_contract.py'),
             Path('reference/database/ingest_runtime_document.py')} <= programs,
            'shared CLI population is incomplete')
    return programs


def test_help_and_unknown_options_for_every_shared_cli():
    programs, executed = parser_programs(), set()
    for path in sorted(programs):
        outputs = []
        for switch in ('-h', '--help'):
            command = [sys.executable, '-B', str(ROOT / path), switch]
            status, output, errors = run(command)
            require(status == 0 and not errors and b'usage:' in output and b'--help' in output,
                    repr(command) + ': ' + repr((status, output, errors)))
            outputs.append(output)
        require(outputs[0] == outputs[1], 'help aliases differ for ' + str(path))
        for switch in ('--unknown-command-contract-option', '-x'):
            command = [sys.executable, '-B', str(ROOT / path), switch]
            status, output, errors = run(command)
            require(status == 2 and errors, repr(command) + ': ' + repr((status, output, errors)))
        executed.add(path)
    require(executed == programs, 'shared CLI controls did not execute the complete population')


def test_subcommand_help_does_not_open_destination():
    with TemporaryTree() as directory:
        destination = Path(directory) / 'must-not-be-created.db'
        for engine, target in (('--engine', '--destination'), ('--eng', '--dest')):
            for switch in ('-h', '--help'):
                command = [sys.executable, '-B', str(ROOT / 'reference/database/ingest_runtime_document.py'),
                           engine, 'sqlite', target, str(destination), 'initialize', switch]
                status, output, errors = run(command)
                require(status == 0 and not errors and b'--exclusive-unpublished' in output,
                        repr(command) + ': ' + repr((status, output, errors)))
                require(not destination.exists(), 'help opened the database destination')


def test_version_prefix_retains_release_action():
    outputs = []
    for switch in ('--version', '--ver'):
        command = [sys.executable, '-B', str(ROOT / 'validators/validate_review_readiness.py'), switch]
        status, output, errors = run(command)
        require(status == 0 and output == b'0.1.0\n' and not errors,
                repr(command) + ': ' + repr((status, output, errors)))
        outputs.append(output)
    require(outputs[0] == outputs[1])


def test_option_flags_and_dash_filenames_stay_distinct():
    with TemporaryTree() as directory:
        root = Path(directory)
        source = (ROOT / 'examples/minimal-adapter-contract.toml').read_bytes()
        base_command = [sys.executable, '-B', str(ROOT / 'validators/validate_provenance.py'),
                        '--repo-root', str(root)]
        previous = os.getcwd()
        try:
            os.chdir(root)
            for name in ('-h', '-x', '-1', '-.5'):
                (root / name).write_bytes(source)
                command = base_command + ['--', name]
                status, output, errors = run(command)
                require(status == 0 and b'PROVENANCE VALIDATION PASSED' in output and not errors,
                        repr(command) + ': ' + repr((status, output, errors)))
                if name in ('-1', '-.5'):
                    status, output, errors = run(base_command + [name])
                    require(status == 0 and b'PROVENANCE VALIDATION PASSED' in output and not errors)
            for operands in (['-x'], ['-1', '-x'], ['-1', '--unknown-command-contract-option']):
                command = base_command + operands
                status, output, errors = run(command)
                require(status == 2 and b'unrecognized arguments' in errors,
                        'unknown option became a filename: ' + repr((status, output, errors)))
        finally:
            os.chdir(previous)


def test_missing_destination_value_has_no_filesystem_side_effect():
    with TemporaryTree() as directory:
        root, previous = Path(directory), os.getcwd()
        try:
            os.chdir(root)
            for value in ('-x', '-h', '--help'):
                command = [sys.executable, '-B', str(ROOT / 'reference/database/ingest_runtime_document.py'),
                           '--engine', 'sqlite', '--destination', value, 'initialize', '--exclusive-unpublished']
                status, output, errors = run(command)
                created = (root / value).exists()
                require(status == 2 and errors and not created,
                        repr(command) + ': ' + repr({'exit_code': status, 'destination_created': created,
                                                     'stdout': output, 'stderr': errors}))
            require(list(root.iterdir()) == [], 'invalid command created an unexpected file')
        finally:
            os.chdir(previous)


def test_closure_cli_prunes_excluded_directories_before_traversal():
    with TemporaryTree() as directory:
        root = Path(directory)
        selected = root / 'canonical.toml'
        selected.write_bytes((ROOT / 'examples/minimal-adapter-contract.toml').read_bytes())
        command = [sys.executable, '-B', str(ROOT / 'validators/validate_closure_root.py'),
                   '--repo-root', str(ROOT), '--discover=' + str(root), str(root / 'ignored-positional.toml')]
        status, output, errors = run(command)
        require(status == 0 and b'PASSED (1 file(s))' in output and not errors,
                repr(command) + ': ' + repr((status, output, errors)))
        for name in ('.venv', 'target', 'node_modules', '__pycache__', 'explicit-exclusion'):
            omitted = root / name
            (omitted / 'lib').mkdir(parents=True)
            (omitted / 'lib64').symlink_to('lib')
            (omitted / 'malformed.toml').write_text('[broken\n')
        command.extend(['--exclude', str(root / 'explicit-exclusion')])
        status, output, errors = run(command)
        require(status == 0 and b'PASSED (1 file(s))' in output and not errors,
                repr(command) + ': ' + repr((status, output, errors)))
        selected.write_text('[broken\n')
        status, output, errors = run(command)
        require(status == 1 and b'cannot inspect TOML candidate' in errors,
                'excluded directories concealed a malformed selected document: ' + repr((status, output, errors)))
        selected.write_bytes((ROOT / 'examples/minimal-adapter-contract.toml').read_bytes())
        for name in ('target-extra', 'explicit-exclusion-extra'):
            sibling = root / name
            sibling.mkdir()
            malformed = sibling / 'malformed.toml'
            malformed.write_text('[broken\n')
            status, output, errors = run(command)
            require(status == 1 and b'cannot inspect TOML candidate' in errors,
                    'a sibling prefix escaped selected-source validation: ' + repr((status, output, errors)))
            malformed.unlink()
            sibling.rmdir()


def execute_workflow(source, root):
    previous = os.getcwd()
    program = 'import sys\nsys.path.insert(0, ' + repr(str(ROOT / 'validators')) + ')\n' + source
    try:
        os.chdir(root)
        status, output, errors = run([sys.executable, '-B', '-S', '-c', program])
    finally:
        os.chdir(previous)
    return status, output.decode(), errors.decode()


def test_workflow_discovery_prunes_declared_exclusions():
    source = (ROOT / '.github/workflows/validate.yml').read_text()
    fragments = [text for _kind, text in workflow_python(source)
                 if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == 'rglob' for node in ast.walk(ast.parse(text)))]
    require(len(fragments) == 2, 'whole-tree workflow discovery population changed')
    parse_step = next(text for text in fragments if 'parsed OK:' in text)
    closure_step = next(text for text in fragments if 'spec_reserved_kinds' in text)
    require(parse_step != closure_step)
    with TemporaryTree() as directory:
        root = Path(directory)
        (root / 'core').mkdir()
        (root / 'profiles').mkdir()
        (root / 'core/widget-kind.toml').write_text('[meta]\ntemplate_kind = "kind-descriptor"\n'
                                                   'describes_kind = "widget"\n[kind]\nname = "widget"\n')
        (root / 'positive.toml').write_text('[meta]\ntemplate_kind = "widget"\n')
        (root / '.venv/lib').mkdir(parents=True)
        (root / '.venv/lib64').symlink_to('lib')
        (root / '.venv/malformed.toml').write_text('[broken\n')
        status, output, errors = execute_workflow(parse_step, root)
        require(status == 0 and output == 'parsed OK: 2 selected files; pruned 1 hidden paths\n' and not errors,
                repr((status, output, errors)))
        for name in ('target', 'node_modules', '__pycache__'):
            (root / name / 'lib').mkdir(parents=True)
            (root / name / 'lib64').symlink_to('lib')
        for hidden in ('.negative-source', '.invalid-source'):
            (root / hidden).mkdir()
            (root / hidden / 'malformed.toml').write_text('[broken\n')
        (root / 'examples').mkdir()
        (root / 'examples/negative').symlink_to(root / '.negative-source')
        (root / 'examples/negative-extra').mkdir()
        (root / 'examples/negative-extra/accepted.toml').write_text('[meta]\ntemplate_kind = "widget"\n')
        (root / 'conformance/cases/widget/valid').mkdir(parents=True)
        (root / 'conformance/cases/widget/invalid').symlink_to(root / '.invalid-source')
        (root / 'conformance/cases/widget/valid/canonical.toml').write_text('[meta]\ntemplate_kind = "widget"\n')
        expected = {'core/widget-kind.toml', 'positive.toml', 'examples/negative-extra/accepted.toml',
                    'conformance/cases/widget/valid/canonical.toml'}
        status, output, errors = execute_workflow(closure_step, root)
        require(status == 0 and not errors and set(output.splitlines()) == expected
                and len(output.splitlines()) == len(expected), repr((status, output, errors)))
        (root / 'examples/negative-extra/malformed.toml').write_text('[broken\n')
        status, output, errors = execute_workflow(closure_step, root)
        require(status != 0 and 'cannot inspect TOML candidate' in errors,
                'workflow pruning hid a malformed selected sibling: ' + repr((status, output, errors)))


def test_workflow_closure_discovery_instrument():
    with TemporaryTree() as directory:
        status, output, errors = execute_workflow(
            'from check_closure_discovery import main\nraise SystemExit(main())\n', Path(directory))
        require(status == 0 and not errors and output.startswith('PASS: ')
                and output.endswith('skipped=[]\n'), repr((status, output, errors)))


if __name__ == '__main__':
    tests = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(tests)
    executed = set()
    for name, test in sorted(tests.items()):
        test()
        executed.add(name)
    require(executed == set(tests))
    print('command contracts: shared CLI help, option refusal, subcommand side effects and excluded-directory discovery exercised')
