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
        for pattern in ('../secret', 'core//alpha', 'core/*x*y'):
            expect_raises(ValueError, lambda: list(glob(root, pattern)),
                          'unsafe or unsupported path pattern accepted: ' + pattern)
if __name__ == '__main__':
    test_path_shapes()
    print('literal path scanner: accepted and rejected cases passed')
