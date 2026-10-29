"""Bind receipt metadata to the supplied checkout despite inherited Git settings."""

from contextlib import contextmanager
import hashlib
import os
import sys

from _credential_git import git
from _credential_test_support import TemporaryTree
from _literal_json import dumps
from _literal_path import Path
from _test_require import expect_raises, require
from check_database_vocabularies import source_identity
import _toml11 as toml
from _receipts import validate_receipts

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def git_settings(values):
    previous = {key: value for key, value in os.environ.items() if key.startswith('GIT_')}
    for key in previous:
        del os.environ[key]
    os.environ.update(values)
    try:
        yield
    finally:
        for key in list(os.environ):
            if key.startswith('GIT_'):
                del os.environ[key]
        os.environ.update(previous)


def test_source_identity_uses_supplied_root_and_complete_status():
    commit = git(ROOT, ['rev-parse', 'HEAD']).strip().decode()
    with TemporaryTree() as directory:
        work = Path(directory)
        subject = work / 'subject'
        git(ROOT, ['worktree', 'add', '--detach', str(subject), commit])
        original_paths = list(sys.path)
        try:
            baseline = source_identity(subject)
            require(baseline['commit'] == commit and baseline['working_tree_clean']
                    and baseline['tracked_tree_clean'] and baseline['bundle_files_tracked'])
            require(baseline['diff_sha256'] == baseline['status_sha256'] == hashlib.sha256(b'').hexdigest())
            foreign = {'GIT_DIR': git(ROOT, ['rev-parse', '--absolute-git-dir']).strip().decode(),
                       'GIT_WORK_TREE': str(ROOT)}
            with git_settings(foreign):
                require(source_identity(subject) == baseline, 'foreign checkout changed the selected source identity')
            unused_index = work / 'must-not-be-opened-index'
            for settings in ({'GIT_INDEX_FILE': str(unused_index)},
                             {'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.worktree',
                              'GIT_CONFIG_VALUE_0': str(ROOT)}):
                with git_settings(settings):
                    require(source_identity(subject) == baseline, 'inherited Git settings changed source binding')
            require(not unused_index.exists(), 'source binding wrote to an inherited index path')
            tracked = subject / 'reference/database/_parallel_checks.py'
            original = tracked.read_bytes()
            tracked.write_bytes(original + b'\n# Private source identity refusal witness.\n')
            with git_settings(foreign):
                dirty = source_identity(subject)
            require(not dirty['working_tree_clean'] and not dirty['tracked_tree_clean']
                    and dirty['diff_sha256'] != baseline['diff_sha256']
                    and dirty['status_sha256'] != baseline['status_sha256'],
                    'foreign Git settings concealed a changed selected source')
            tracked.write_bytes(original)
            require(source_identity(subject) == baseline, 'restored source did not recover its original identity')
            untracked = subject / 'untracked-source-identity-witness.txt'
            untracked.write_text('untracked evidence must prevent a clean receipt\n')
            with git_settings(foreign):
                dirty = source_identity(subject)
            require(not dirty['working_tree_clean'] and dirty['tracked_tree_clean']
                    and dirty['bundle_files_tracked'] and dirty['diff_sha256'] == baseline['diff_sha256']
                    and dirty['status_sha256'] != baseline['status_sha256'],
                    'untracked source was labelled clean')
            lock = toml.loads_bytes((subject / 'reference/database/engine-lock.toml').read_bytes())
            receipts = []
            for lane in lock['lanes']:
                path = work / (lane['id'] + '.json')
                path.write_text(dumps({'lane': lane['id']}))
                receipts.append(path)
            error = expect_raises(ValueError,
                                  lambda: validate_receipts(subject, receipts, include_loaders=False),
                                  'untracked source reached receipt acceptance')
            require(str(error) == 'full executed receipt gate requires a clean tree at a named commit',
                    'untracked source failed outside the explicit clean-tree requirement')
            untracked.unlink()
            require(source_identity(subject) == baseline)
            error = expect_raises(ValueError, lambda: source_identity(subject / 'core'),
                                  'nested directory was accepted as the repository root')
            require('requires the repository root' in str(error))
        finally:
            sys.path[:] = original_paths
            git(ROOT, ['worktree', 'remove', '--force', str(subject)])


if __name__ == '__main__':
    test_source_identity_uses_supplied_root_and_complete_status()
    print('database source binding: clean, changed and untracked source; foreign checkout/index/config refusal; skipped=[]')
