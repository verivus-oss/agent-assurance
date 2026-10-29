"""Exercise committed-byte binding independently of Git's cached status."""

import hashlib
import os

from _credential_test_support import TemporaryTree, command, commit, initialize, write
from _literal_path import Path
from _test_require import expect_raises, require
from _working_source import working_delta


def test_hidden_changes_and_staging_states_are_bound():
    for algorithm in ('sha1', 'sha256'):
        with TemporaryTree() as directory:
            root = Path(directory)
            initialize(root, algorithm)
            subject = root / 'source.txt'
            write(subject, b'original bytes\n')
            head = commit(root, 'committed byte control')
            baseline = working_delta(root, head)
            require(baseline == (True, hashlib.sha256(b'').hexdigest()))
            for invalid in ('HEAD', '', 'a' * 39, 'a' * 41, 'A' * 40, None):
                error = expect_raises(ValueError, lambda: working_delta(root, invalid), 'noncanonical commit selector passed')
                require('exact commit identity' in str(error))
            observed = set()
            for flag in ('assume-unchanged', 'skip-worktree'):
                command(root, 'update-index', '--' + flag, '--', 'source.txt')
                try:
                    write(subject, b'different data\n')
                    require(command(root, 'status', '--porcelain').stdout == b'',
                            'hidden-change control did not conceal its changed bytes')
                    clean, digest = working_delta(root, head)
                    require(not clean and digest != baseline[1], 'index flag concealed changed source bytes')
                    observed.add(flag)
                finally:
                    write(subject, b'original bytes\n')
                    command(root, 'update-index', '--no-' + flag, '--', 'source.txt')
                require(working_delta(root, head) == baseline)
            require(observed == {'assume-unchanged', 'skip-worktree'})
            write(subject, b'staged data\n')
            command(root, 'add', 'source.txt')
            staged = working_delta(root, head)
            require(not staged[0] and staged[1] != baseline[1])
            write(subject, b'original bytes\n')
            require(not working_delta(root, head)[0], 'staged different bytes disappeared from source state')
            command(root, 'reset', '-q', 'HEAD', '--', 'source.txt')
            require(working_delta(root, head) == baseline)
            subject.unlink()
            require(not working_delta(root, head)[0], 'missing committed source was labelled clean')
            write(subject, b'original bytes\n')
            subject.chmod(0o755)
            require(not working_delta(root, head)[0], 'executable mode change was labelled clean')
            subject.chmod(0o644)
            require(working_delta(root, head) == baseline)


def test_link_text_is_bound_without_following_linked_directories():
    with TemporaryTree() as directory:
        root = Path(directory)
        initialize(root)
        (root / 'nested').mkdir()
        write(root / 'nested/source.txt', b'committed\n')
        os.symlink('missing-target', root / 'link')
        head = commit(root, 'literal link control')
        baseline = working_delta(root, head)
        require(baseline[0], 'committed link text required its target to exist')
        (root / 'link').unlink()
        os.symlink('different-missing-target', root / 'link')
        require(not working_delta(root, head)[0], 'changed link text was labelled clean')
        (root / 'link').unlink()
        os.symlink('missing-target', root / 'link')
        require(working_delta(root, head) == baseline)
        (root / 'nested/source.txt').unlink()
        (root / 'nested').rmdir()
        os.symlink('missing-directory', root / 'nested')
        error = expect_raises(ValueError, lambda: working_delta(root, head), 'linked source ancestry was followed')
        require('symlinked ancestor' in str(error))


def test_special_source_types_fail_without_opening_a_pipe():
    with TemporaryTree() as directory:
        root = Path(directory)
        initialize(root)
        subject = root / 'source.txt'
        write(subject, b'committed\n')
        head = commit(root, 'regular source control')
        require(working_delta(root, head)[0])
        subject.unlink()
        os.mkfifo(subject)
        error = expect_raises(ValueError, lambda: working_delta(root, head), 'special source file was opened')
        require('unsupported file type' in str(error))


if __name__ == '__main__':
    controls = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(controls)
    executed = set()
    for name, control in sorted(controls.items()):
        control()
        executed.add(name)
    require(executed == set(controls))
    print('working source: SHA1/SHA256 repositories, hidden changes, staged/missing/mode changes, link text and unsafe file refusal; skipped=[]')
