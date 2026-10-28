"""Independent lexical, containment and filesystem path controls."""

import os
import stat

import _literal_path as paths
from _literal_path import Path, PurePosixPath, PureWindowsPath
from _literal_paths import glob, rglob
from _test_require import expect_raises, require


class Workspace:
    sequence = 0

    def __enter__(self):
        Workspace.sequence += 1
        self.root = Path(__file__).resolve().parents[1] / '.local/path-controls' / (str(os.getpid()) + '-' + str(self.sequence))
        self.root.mkdir(parents=True)
        return self.root

    def __exit__(self, *_error):
        def remove(path):
            if stat.S_ISDIR(path.lstat().st_mode):
                for child in path.iterdir():
                    remove(child)
                path.rmdir()
            else:
                path.unlink()
        remove(self.root)


def test_exported_class_population_and_retired_apis():
    expected = {'Path', 'PosixPath', 'WindowsPath', 'PurePath', 'PurePosixPath', 'PureWindowsPath'}
    public = {name for name, value in vars(paths).items() if not name.startswith('_')
              and isinstance(value, type) and value.__module__ == paths.__name__}
    require(public == expected == set(paths.__all__) and len(paths.__all__) == len(expected))
    for name in expected:
        constructor = getattr(paths, name)
        for retired in ('glob', 'rglob', 'match', 'as_uri'):
            require(not hasattr(constructor, retired), 'retired path API remained: ' + name + '.' + retired)
    expect_raises(TypeError, lambda: Path(b'byte-path'), 'byte path operand passed')
    expect_raises(TypeError, lambda: Path(None), 'absent path operand passed')
    expect_raises(TypeError, lambda: Path(1), 'numeric path operand passed')
    if os.name != 'nt':
        expect_raises(NotImplementedError, lambda: paths.WindowsPath('C:/a'), 'foreign native path was instantiated')


def test_posix_lexical_goldens():
    expected = {
        '': ('.', (), '.', (), '', '', False),
        '.': ('.', (), '.', (), '', '', False),
        '/': ('/', ('/',), '/', (), '', '', True),
        'a//./b/../c.tar.gz': ('a/b/../c.tar.gz', ('a', 'b', '..', 'c.tar.gz'), 'a/b/..',
                              ('a/b/..', 'a/b', 'a', '.'), 'c.tar.gz', '.gz', False),
        '//server/share': ('//server/share', ('//', 'server', 'share'), '//server',
                           ('//server', '//'), 'share', '', True),
        '///a': ('/a', ('/', 'a'), '/', ('/',), 'a', '', True),
        '.hidden': ('.hidden', ('.hidden',), '.', ('.',), '.hidden', '', False),
        'tail.': ('tail.', ('tail.',), '.', ('.',), 'tail.', '', False),
    }
    visited = set()
    for source, answer in expected.items():
        path = PurePosixPath(source)
        observed = (str(path), path.parts, str(path.parent), tuple(str(p) for p in path.parents),
                    path.name, path.suffix, path.is_absolute())
        require(observed == answer, 'POSIX lexical contract differed: ' + repr(source))
        require(os.fspath(path) == str(path) and path.as_posix() == str(path))
        require(path == PurePosixPath(str(path)) and hash(path) == hash(PurePosixPath(str(path))))
        visited.add(source)
    require(visited == set(expected))
    require(PurePosixPath('a', '/b', 'c') == PurePosixPath('/b/c'))
    require(PurePosixPath('a') / 'b' == PurePosixPath('a/b'))
    require('a' / PurePosixPath('b') == PurePosixPath('a/b'))
    require(sorted([PurePosixPath('b'), PurePosixPath('a')]) == [PurePosixPath('a'), PurePosixPath('b')])
    require(PurePosixPath('a') != 'a')
    path = PurePosixPath('a/b/c')
    require(path.parents[-1] == PurePosixPath('.') and path.parents[:2] == (PurePosixPath('a/b'), PurePosixPath('a')))
    expect_raises(IndexError, lambda: path.parents[3], 'absent ancestor passed')
    require(path.with_name('d') == PurePosixPath('a/b/d'))
    require(path.with_suffix('.toml') == PurePosixPath('a/b/c.toml'))
    require(PurePosixPath('a/b.toml').with_suffix('') == PurePosixPath('a/b'))
    for name in ('', '.', 'a/b'):
        expect_raises(ValueError, lambda: path.with_name(name), 'invalid replacement name passed')
    expect_raises(ValueError, lambda: path.with_suffix('toml'), 'invalid suffix passed')


def test_windows_lexical_goldens():
    expected = {
        'C:/a/b': ('C:\\a\\b', ('C:\\', 'a', 'b'), 'C:', True),
        'C:a/b': ('C:a\\b', ('C:', 'a', 'b'), 'C:', False),
        '\\\\host\\share\\a': ('\\\\host\\share\\a', ('\\\\host\\share\\', 'a'), '\\\\host\\share', True),
        '///a/b': ('\\a\\b', ('\\', 'a', 'b'), '', False),
    }
    visited = set()
    for source, answer in expected.items():
        path = PureWindowsPath(source)
        require((str(path), path.parts, path.drive, path.is_absolute()) == answer)
        visited.add(source)
    require(visited == set(expected))
    require(PureWindowsPath('C:/A') == PureWindowsPath('c:/a'))
    for prefix in ('COM', 'LPT'):
        for value in (*range(1, 10), '¹', '²', '³'):
            require(PureWindowsPath(prefix + str(value)).is_reserved())
        for value in (0, 10, 11):
            require(not PureWindowsPath(prefix + str(value)).is_reserved())
    require(PureWindowsPath('C:/a/b').relative_to('c:/A') == PureWindowsPath('b'))
    expect_raises(ValueError, lambda: PureWindowsPath('C:/a').relative_to('D:/'), 'foreign drive containment passed')


def test_relative_roots_and_parent_traversal():
    require(PurePosixPath('a/../b').parts == ('a', '..', 'b'), 'lexical parent was erased')
    require(PurePosixPath('a/../b').relative_to('a') == PurePosixPath('../b'))
    require(PurePosixPath('/a/b').relative_to('/a') == PurePosixPath('b'))
    for source, root in (('ab/file', 'a'), ('/a/b', 'a'), ('a/b', '/a'), ('a', 'a/b')):
        require(not PurePosixPath(source).is_relative_to(root))
        expect_raises(ValueError, lambda: PurePosixPath(source).relative_to(root), 'unrelated lexical root passed')
    with Workspace() as root:
        (root / 'target/child').mkdir(parents=True)
        (root / 'target/value').write_bytes(b'original')
        (root / 'link').symlink_to('target/child')
        source = root / 'link/../value'
        require(source.parts[-3:] == ('link', '..', 'value'))
        require(source.resolve() == root / 'target/value', 'symlink and parent resolution order changed')
        require(source.read_bytes() == b'original')
        (root / 'escape').symlink_to(root.parent)
        require(not (root / 'escape/outside').resolve().is_relative_to(root), 'resolved link escape remained contained')
        require(not (root / '../outside').resolve().is_relative_to(root), 'resolved parent escape remained contained')
        missing = root / 'missing/child'
        require(missing.resolve() == missing)
        expect_raises(FileNotFoundError, lambda: missing.resolve(strict=True), 'strict missing resolution passed')
        (root / 'loop').symlink_to('loop')
        expect_raises(RuntimeError, lambda: (root / 'loop').resolve(), 'symlink loop resolved')


def test_filesystem_operations_and_discovery():
    with Workspace() as root:
        folder = root / 'folder'
        folder.mkdir()
        expect_raises(FileExistsError, lambda: folder.mkdir(), 'existing directory creation passed')
        folder.mkdir(exist_ok=True)
        path = folder / 'value.toml'
        data = b'\x00\xffliteral\n'
        require(path.write_bytes(data) == len(data) and path.read_bytes() == data)
        expect_raises(TypeError, lambda: path.write_bytes('invalid'), 'text passed binary write')
        require(path.read_bytes() == data, 'invalid binary operand truncated the file')
        expect_raises(TypeError, lambda: path.write_text(data), 'bytes passed text write')
        require(path.read_bytes() == data, 'invalid text operand truncated the file')
        text = 'é\nsecond\n'
        require(path.write_text(text, encoding='utf-8', newline='') == len(text))
        require(path.read_text(encoding='utf-8') == text)
        with path.open('a', encoding='utf-8') as stream:
            stream.write('tail')
        require(path.read_text(encoding='utf-8') == text + 'tail')
        path.chmod(0o600)
        require(stat.S_IMODE(path.stat().st_mode) == 0o600)
        if os.name == 'posix' and os.geteuid() != 0:
            path.chmod(0)
            try:
                expect_raises(PermissionError, path.read_bytes, 'owner permission denial passed binary read')
            finally:
                path.chmod(0o600)
            folder.chmod(0)
            try:
                expect_raises(PermissionError, lambda: list(folder.iterdir()), 'owner permission denial passed directory iteration')
            finally:
                folder.chmod(0o700)
        require(path.is_file() and not path.is_dir() and not path.is_symlink())
        require(folder.is_dir() and not folder.is_file())
        expect_raises(NotADirectoryError, lambda: (path / 'child').stat(), 'file parent passed stat')
        expect_raises(IsADirectoryError, lambda: folder.read_bytes(), 'directory passed binary read')
        require(list(glob(root, 'folder/*.toml')) == [path])
        require(set(rglob(root, '*.toml')) == {path})
        link = root / 'file-link'
        link.symlink_to('folder/value.toml')
        require(link.is_symlink() and link.is_file() and stat.S_ISLNK(link.lstat().st_mode))
        require(link.read_bytes() == path.read_bytes())
        renamed = path.rename(folder / 'renamed.toml')
        require(renamed == folder / 'renamed.toml' and not path.exists() and renamed.is_file())
        require(link.is_symlink() and not link.exists())
        require({entry.name for entry in root.iterdir()} == {'folder', 'file-link'})
        renamed.unlink()
        expect_raises(FileNotFoundError, lambda: renamed.unlink(), 'absent unlink passed')
        renamed.unlink(missing_ok=True)
        link.unlink()
        folder.rmdir()
        require(not folder.exists() and not folder.is_file() and not folder.is_dir())


if __name__ == '__main__':
    tests = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(tests)
    executed = set()
    for name, test in sorted(tests.items()):
        test()
        executed.add(name)
    require(executed == set(tests))
    print('owned path controls: complete declared lexical, containment and filesystem population executed')
    if os.name != 'posix' or os.geteuid() == 0:
        print('skipped: owner permission denial requires a non-root POSIX process')
