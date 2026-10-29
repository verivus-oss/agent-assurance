"""Compare raw working and indexed bytes with immutable committed blobs."""

from contextlib import contextmanager, ExitStack
import hashlib
import os
import stat

from _credential_git import git
from _git_objects import BlobReader, object_id


DIFF_FORMAT = 'git-source-bytes-v1'


def _entries(raw, *, index):
    if raw and not raw.endswith(b'\0'):
        raise ValueError('working source index/tree framing is incomplete')
    result = {}
    for row in raw.split(b'\0')[:-1]:
        header, separator, path = row.partition(b'\t')
        fields = header.split(b' ')
        if not separator or len(fields) != 3 or not path or path.startswith(b'/'):
            raise ValueError('working source entry has invalid framing')
        if any(part in (b'', b'.', b'..') for part in path.split(b'/')) or path in result:
            raise ValueError('working source entry has an invalid or repeated path')
        mode = fields[0]
        key = fields[1] if index else fields[2]
        if mode not in (b'100644', b'100755', b'120000'):
            raise ValueError('working source requires regular files and captured link text; submodules are unsupported')
        if not object_id(key) or (fields[2] != b'0' if index else fields[1] != b'blob'):
            raise ValueError('working source entry is unmerged or has an invalid object identity')
        result[path] = (mode, key)
    return result


@contextmanager
def _descriptor(path, flags, *, parent=None):
    descriptor = os.open(path, flags, dir_fd=parent)
    try:
        yield descriptor
    finally:
        os.close(descriptor)


def _identity(metadata):
    return (metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_size,
            metadata.st_mtime_ns, metadata.st_ctime_ns)


def _state(mode, data):
    return mode, hashlib.sha256(data).digest(), len(data)


def _current(root_descriptor, path):
    parts = path.split(b'/')
    with ExitStack() as owned:
        parent = root_descriptor
        try:
            for part in parts[:-1]:
                before = os.stat(part, dir_fd=parent, follow_symlinks=False)
                if stat.S_ISLNK(before.st_mode):
                    raise ValueError('working source has a symlinked ancestor')
                parent = owned.enter_context(_descriptor(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, parent=parent))
            before = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        except (FileNotFoundError, NotADirectoryError):
            return None
        if stat.S_ISLNK(before.st_mode):
            data = os.readlink(parts[-1], dir_fd=parent)
            after = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            if _identity(before) != _identity(after):
                raise ValueError('working source link changed during capture')
            return _state(b'120000', data)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('working source has an unsupported file type')
        descriptor = owned.enter_context(_descriptor(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, parent=parent))
        if _identity(os.fstat(descriptor)) != _identity(before):
            raise ValueError('working source changed before capture')
        digest, length = hashlib.sha256(), 0
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            digest.update(chunk)
            length += len(chunk)
        if _identity(os.fstat(descriptor)) != _identity(before) or length != before.st_size:
            raise ValueError('working source changed during capture')
        mode = b'100755' if before.st_mode & stat.S_IXUSR else b'100644'
        return mode, digest.digest(), length


def working_delta(root, commit):
    """Return byte/mode equality and a framed delta without rendering a patch.

    Index assumption flags and content filters do not participate in the
    comparison. Link text is captured; linked directories are not followed.
    """
    if os.name != 'posix' or not all(hasattr(os, name) for name in ('O_DIRECTORY', 'O_NOFOLLOW')):
        raise ValueError('working source byte capture requires POSIX descriptor support')
    if (type(commit) is not str or len(commit) not in (40, 64)
            or any(char not in '0123456789abcdef' for char in commit)):
        raise ValueError('working source requires an exact commit identity')
    head = _entries(git(root, ['ls-tree', '-r', '--full-tree', '-z', commit]), index=False)
    raw_index = git(root, ['ls-files', '--stage', '-z'])
    indexed = _entries(raw_index, index=True)
    frame = bytearray()
    cache = {}

    def stored(entry, reader):
        if entry is None:
            return None
        mode, key = entry
        if key not in cache:
            cache[key] = _state(b'', reader.read(key))[1:]
        return mode, *cache[key]

    def append(value):
        frame.extend(len(value).to_bytes(8, 'big'))
        frame.extend(value)

    with BlobReader(root) as reader, _descriptor(
            os.fspath(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW) as root_descriptor:
        for path in sorted(set(head) | set(indexed)):
            committed = stored(head.get(path), reader)
            staged = stored(indexed.get(path), reader)
            current = _current(root_descriptor, path)
            if committed == staged == current:
                continue
            if not frame:
                frame.extend(DIFF_FORMAT.encode('ascii') + b'\0')
            append(path)
            for state in (committed, staged, current):
                mode, digest, length = state if state is not None else (b'absent', b'', 0)
                append(mode)
                append(digest)
                append(length.to_bytes(8, 'big'))
    if (git(root, ['rev-parse', '--verify', 'HEAD^{commit}']).strip() != commit.encode('ascii')
            or git(root, ['ls-files', '--stage', '-z']) != raw_index):
        raise ValueError('working source commit or index moved during capture')
    return not frame, hashlib.sha256(frame).hexdigest()
