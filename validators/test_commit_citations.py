"""Accepted and rejected cases for the commit citation scanner."""
from _test_require import require
import pathlib
import sys
from check_commit_citations import commit_tokens, governed_file, parse_args

def test_commit_words_and_noncommit_words() -> None:
    require(commit_tokens('opened_in_commit: 9996826') == {'9996826'})
    require(commit_tokens('commit `A1b2C3d`') == {'a1b2c3d'})
    require(commit_tokens('feedback 123456 0123456789abcdef') == {'0123456789abcdef'})
    require(commit_tokens('prefix_abcdef0 suffixabcdef0') == set())

def test_uuid_segments_are_not_citations() -> None:
    require(commit_tokens('job 12345678-1234-abcd-5678-123456789abc') == set())
    require(commit_tokens('commit 9996826 beside 12345678-1234-abcd-5678-123456789abc') == {'9996826'})
    require(commit_tokens('deadbeefcafe 12345678-1234-1234-1234-123456789abc') == {'deadbeefcafe'})
    require(commit_tokens('deadbeefcafe12345678-1234-1234-1234-123456789abc') == set())
    require(commit_tokens('12345678-1234-1234-1234-123456789abcdeadbeefcafe') == set())

def test_scan_population_excludes_vendor_and_unit_fixtures() -> None:
    root = pathlib.Path('/repo')
    require(governed_file(root / 'docs/issues/issue.md', root))
    require(governed_file(root / 'validators/check_commit_citations.py', root))
    require(not governed_file(root / 'validators/_toml11_vendor/_scan.py', root))
    require(not governed_file(root / 'validators/test_toml11_scanner.py', root))

def test_cli_accepts_exact_options_and_rejects_missing_values() -> None:
    original = sys.argv
    try:
        sys.argv = ['checker', '--repo-root', 'repo', '--baseline=record.toml']
        args = parse_args()
        require((args.repo_root, args.baseline) == ('repo', 'record.toml'))
        sys.argv = ['checker', '--repo-root']
        try:
            parse_args()
        except SystemExit as exc:
            require(exc.code == 2)
        else:
            raise AssertionError('missing option value accepted')
    finally:
        sys.argv = original
if __name__ == '__main__':
    test_commit_words_and_noncommit_words()
    test_uuid_segments_are_not_citations()
    test_scan_population_excludes_vendor_and_unit_fixtures()
    test_cli_accepts_exact_options_and_rejects_missing_values()
    print('commit citation scanner: 4 test groups passed')
