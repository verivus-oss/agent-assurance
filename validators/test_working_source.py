"""Exercise committed-byte binding independently of Git's cached status."""

import hashlib
import errno
import os
import stat

from _credential_test_support import TemporaryTree, command, commit, initialize, write
from _literal_path import Path
from _test_require import expect_raises, require
from _temporary_attribute import temporary_attribute, raising
from _working_source import working_delta, _current


def test_every_capture_descriptor_is_closed_on_results_and_failures():
    with TemporaryTree() as directory:
        root = Path(directory)
        (root / 'first/second').mkdir(parents=True)
        write(root / 'first/second/subject', b'captured bytes')
        (root / 'alias').symlink_to(root / 'first', target_is_directory=True)
        os.mkfifo(root / 'first/second/pipe')
        root_descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        original_open = os.open
        cases = {
            'accepted': (b'first/second/subject', [b'first', b'second', b'subject']),
            'missing': (b'first/second/missing', [b'first', b'second']),
            'linked-parent': (b'alias/subject', []),
            'special-leaf': (b'first/second/pipe', [b'first', b'second']),
            'first-open': (b'first/second/subject', []),
            'second-open': (b'first/second/subject', [b'first']),
            'leaf-open': (b'first/second/subject', [b'first', b'second']),
            'read': (b'first/second/subject', [b'first', b'second', b'subject']),
        }
        visited = set()
        try:
            for name, (path, expected) in cases.items():
                opened = []
                failure = OSError(errno.EACCES, 'independent source capture refusal')
                def capture(member, flags, *, selected=name, captures=opened, error=failure, **options):
                    refused = {'first-open': b'first', 'second-open': b'second', 'leaf-open': b'subject'}
                    if member == refused.get(selected):
                        raise error
                    descriptor = original_open(member, flags, **options)
                    captures.append((member, descriptor))
                    return descriptor
                with temporary_attribute(os, 'open', capture):
                    if name == 'accepted':
                        actual = _current(root_descriptor, path)
                        require(actual == (b'100644', hashlib.sha256(b'captured bytes').digest(), len(b'captured bytes')))
                    elif name == 'missing':
                        require(_current(root_descriptor, path) is None)
                    elif name in ('linked-parent', 'special-leaf'):
                        expect_raises(ValueError, lambda: _current(root_descriptor, path), 'unsafe capture passed')
                    elif name == 'read':
                        with temporary_attribute(os, 'read', raising(failure)):
                            error = expect_raises(OSError, lambda: _current(root_descriptor, path), 'read refusal was suppressed')
                        require(error is failure)
                    else:
                        error = expect_raises(OSError, lambda: _current(root_descriptor, path), 'open refusal was suppressed')
                        require(error is failure)
                require([member for member, _descriptor in opened] == expected, 'descriptor fixture did not reach its declared sites')
                for _member, descriptor in opened:
                    error = expect_raises(OSError, lambda: os.fstat(descriptor), 'capture descriptor leaked')
                    require(error.errno == errno.EBADF, 'descriptor failure was not the closed-state property')
                require(stat.S_ISDIR(os.fstat(root_descriptor).st_mode), 'capture closed its borrowed root')
                visited.add(name)
            require(visited == set(cases))
        finally:
            os.close(root_descriptor)


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
