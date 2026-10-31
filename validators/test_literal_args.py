"""Accepted and rejected command shapes for the exact-option parser."""
from _test_require import require
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from _literal_path import Path
from _literal_args import ArgumentParser

def rejected(parser: ArgumentParser, tokens: list[str]) -> None:
    with redirect_stderr(StringIO()):
        try:
            parser.parse_args(tokens)
        except SystemExit as exc:
            require(exc.code == 2, exc.code)
        else:
            raise AssertionError('invalid command was accepted: ' + str(tokens))

def test_options_and_values() -> None:
    parser = ArgumentParser(description='Test command')
    parser.add_argument('paths', nargs='+', type=Path)
    parser.add_argument('--repo-root', default=Path('.'), type=Path)
    parser.add_argument('--exclude', action='append')
    parser.add_argument('--mode', choices=('strict', 'relaxed'), required=True)
    parser.add_argument('--quiet', action='store_true')
    result = parser.parse_args(['--mode=strict', 'first.toml', '--quiet', 'second.toml', '--exclude', 'ignored'])
    require(result.paths == [Path('first.toml'), Path('second.toml')])
    require(result.mode == 'strict' and result.quiet is True)
    require(result.exclude == ['ignored'] and result.repo_root == Path('.'))
    for tokens in (['first.toml'], ['--mode', 'strict'], ['--mode', 'unknown', 'first.toml'], ['--mode', 'strict', '--unknown', 'first.toml']):
        rejected(parser, tokens)

def test_groups_and_subcommands() -> None:
    parser = ArgumentParser()
    parser.add_argument('--engine', required=True, choices=('sqlite', 'duckdb'))
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument('--lane')
    selector.add_argument('--loader')
    actions = parser.add_subparsers(dest='action', required=True)
    actions.add_parser('initialize').add_argument('--exclusive', action='store_true')
    actions.add_parser('ingest').add_argument('paths', nargs='+')
    result = parser.parse_args(['--engine', 'sqlite', '--lane', 'floor', 'initialize', '--exclusive'])
    require(result.engine == 'sqlite' and result.lane == 'floor')
    require(result.action == 'initialize' and result.exclusive is True)
    result = parser.parse_args(['ingest', 'a.toml', '--engine', 'duckdb', '--loader', 'go'])
    require(result.action == 'ingest' and result.paths == ['a.toml'])
    for tokens in (['--engine', 'sqlite', 'initialize'], ['--engine', 'sqlite', '--lane', 'floor'], ['--engine', 'sqlite', '--lane', 'floor', '--loader', 'go', 'initialize'], ['--engine', 'sqlite', '--lane', 'floor', 'ingest']):
        rejected(parser, tokens)
    collision = ArgumentParser()
    collision.add_argument('--destination', required=True)
    commands = collision.add_subparsers(dest='action', required=True)
    commands.add_parser('initialize')
    commands.add_parser('ingest')
    selected = collision.parse_args(['--destination', 'ingest', 'initialize'])
    require(selected.destination == 'ingest' and selected.action == 'initialize')
    rejected(collision, ['--destination', 'ingest'])

def test_help_and_version() -> None:
    parser = ArgumentParser()
    parser.add_argument('--version', action='version', version='1.2.3')
    parser.add_argument('file')
    for token, expected in (('-h', 'usage:'), ('--help', 'usage:'), ('--version', '1.2.3')):
        output = StringIO()
        with redirect_stdout(output):
            try:
                parser.parse_args([token])
            except SystemExit as exc:
                require(exc.code == 0, exc.code)
            else:
                raise AssertionError('help or version did not exit')
        require(expected in output.getvalue())
    require(parser.parse_args(['--', '--help']).file == '--help')
    require(parser.parse_args(['--', '-h']).file == '-h')
    require(parser.parse_args(['--', '--he']).file == '--he')
    rejected(parser, ['--version=forged'])
    rejected(parser, ['--ver=forged'])

def test_attached_variable_option_preserves_following_paths() -> None:
    parser = ArgumentParser()
    parser.add_argument('paths', nargs='*')
    parser.add_argument('--discover', nargs='+')
    result = parser.parse_args(['--discover=selected', 'ignored.toml'])
    require(result.discover == ['selected'] and result.paths == ['ignored.toml'])
    result = parser.parse_args(['--discover', 'selected', 'another'])
    require(result.discover == ['selected', 'another'] and result.paths == [])
    rejected(parser, ['--discover'])

def test_unambiguous_long_option_prefixes() -> None:
    parser = ArgumentParser()
    parser.add_argument('--repo-root')
    parser.add_argument('--report')
    parser.add_argument('--quiet', action='store_true')
    result = parser.parse_args(['--repo-r=selected', '--report', 'report.json', '--qu'])
    require(result.repo_root == 'selected' and result.report == 'report.json' and result.quiet)
    rejected(parser, ['--repo', 'ambiguous'])
    rejected(parser, ['--unrecognized'])
    for length in range(3, len('--help') + 1):
        switch = '--help'[:length]
        output = StringIO()
        with redirect_stdout(output):
            try:
                parser.parse_args([switch])
            except SystemExit as exc:
                require(exc.code == 0 and 'usage:' in output.getvalue())
            else:
                raise AssertionError('help prefix did not exit')

def test_option_values_and_dash_filenames_stay_distinct() -> None:
    parser = ArgumentParser()
    parser.add_argument('--destination', required=True)
    parser.add_argument('paths', nargs='*')
    for tokens in (['--destination', '-x'], ['--destination', '-h'],
                   ['--destination', '--help'], ['--destination', 'selected', '-x']):
        rejected(parser, tokens)
    result = parser.parse_args(['--destination=-x', '--', '-h'])
    require(result.destination == '-x' and result.paths == ['-h'])
    for value in ('-', '-1', '-1.25', '-.5', '-١'):
        result = parser.parse_args(['--destination', value])
        require(result.destination == value and result.paths == [])
if __name__ == '__main__':
    test_options_and_values()
    test_groups_and_subcommands()
    test_help_and_version()
    test_attached_variable_option_preserves_following_paths()
    test_unambiguous_long_option_prefixes()
    test_option_values_and_dash_filenames_stay_distinct()
    print('literal argument parser: accepted and rejected option, command, help and literal-path cases exercised')
