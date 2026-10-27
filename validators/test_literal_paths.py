"""Accepted and rejected path discovery cases."""
from _test_require import expect_raises, require
from pathlib import Path
from tempfile import TemporaryDirectory
from _literal_paths import glob, rglob

def test_path_shapes() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / 'core').mkdir()
        (root / 'profiles/p1').mkdir(parents=True)
        (root / 'core/alpha-kind.toml').write_text('')
        (root / 'core/not-a-kind.txt').write_text('')
        (root / 'profiles/p1/ontology.toml').write_text('')
        (root / 'profiles/p1/PROFILE.toml').write_text('')
        require(list(glob(root, 'core/*-kind.toml')) == [root / 'core/alpha-kind.toml'])
        require(list(glob(root, 'profiles/*/ontology.toml')) == [root / 'profiles/p1/ontology.toml'])
        require(set(rglob(root, '*.toml')) == {root / 'core/alpha-kind.toml', root / 'profiles/p1/ontology.toml', root / 'profiles/p1/PROFILE.toml'})
        require(list(glob(root, 'profiles/*/absent.toml')) == [])
        link = root / 'core/linked-kind.toml'
        link.symlink_to('alpha-kind.toml')
        require(link in list(glob(root, 'core/*-kind.toml')))
        link.unlink()
        link.symlink_to('missing-kind.toml')
        expect_raises(OSError, lambda: list(glob(root, 'core/*-kind.toml')),
                      'dangling file discovery candidate was ignored')
        link.unlink()
        directory_link = root / 'profiles/p2'
        directory_link.symlink_to('p1')
        require(root / 'profiles/p2/ontology.toml' in list(glob(root, 'profiles/*/ontology.toml')))
        directory_link.unlink()
        directory_link.symlink_to('missing-profile')
        expect_raises(OSError, lambda: list(glob(root, 'profiles/*/ontology.toml')),
                      'dangling discovery directory was ignored')
        broken_root = root / 'broken-root'
        broken_root.symlink_to('missing-root')
        expect_raises(OSError, lambda: list(glob(broken_root, '*.toml')),
                      'dangling discovery root was ignored')
        file_root = root / 'file-root'
        file_root.write_text('not a directory')
        expect_raises(OSError, lambda: list(glob(file_root, '*.toml')),
                      'file used as discovery root was ignored')
        for pattern in ('../secret', 'core//alpha', 'core/*x*y'):
            expect_raises(ValueError, lambda: list(glob(root, pattern)),
                          'unsafe or unsupported path pattern accepted: ' + pattern)
if __name__ == '__main__':
    test_path_shapes()
    print('literal path scanner: accepted and rejected cases passed')
