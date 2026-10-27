"""Accepted and rejected path discovery cases."""
from _test_require import expect_raises, require
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import shutil
import _literal_paths as paths

def test_path_shapes() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / 'core').mkdir()
        (root / 'profiles/p1').mkdir(parents=True)
        (root / 'core/alpha-kind.toml').write_text('')
        (root / 'core/not-a-kind.txt').write_text('')
        (root / 'profiles/p1/ontology.toml').write_text('')
        (root / 'profiles/p1/PROFILE.toml').write_text('')
        require(list(paths.glob(root, 'core/*-kind.toml')) == [root / 'core/alpha-kind.toml'])
        require(list(paths.glob(root, 'profiles/*/ontology.toml')) == [root / 'profiles/p1/ontology.toml'])
        require(set(paths.rglob(root, '*.toml')) == {root / 'core/alpha-kind.toml', root / 'profiles/p1/ontology.toml', root / 'profiles/p1/PROFILE.toml'})
        require(list(paths.glob(root, 'profiles/*/absent.toml')) == [])
        require(list(paths.glob(root / 'absent-root', '*.toml')) == [])
        link = root / 'core/linked-kind.toml'
        link.symlink_to('alpha-kind.toml')
        require(link in list(paths.glob(root, 'core/*-kind.toml')))
        link.unlink()
        link.symlink_to('missing-kind.toml')
        expect_raises(OSError, lambda: list(paths.glob(root, 'core/*-kind.toml')),
                      'dangling file discovery candidate was ignored')
        link.unlink()
        directory_link = root / 'profiles/p2'
        directory_link.symlink_to('p1')
        require(root / 'profiles/p2/ontology.toml' in list(paths.glob(root, 'profiles/*/ontology.toml')))
        expect_raises(OSError, lambda: list(paths.rglob(root, '*.toml')),
                      'recursive scan silently skipped a live directory link')
        directory_link.unlink()
        directory_link.symlink_to('missing-profile')
        expect_raises(OSError, lambda: list(paths.glob(root, 'profiles/*/ontology.toml')),
                      'dangling discovery directory was ignored')
        expect_raises(OSError, lambda: list(paths.rglob(root, '*.toml')),
                      'recursive scan silently skipped a dangling directory link')
        broken_root = root / 'broken-root'
        broken_root.symlink_to('missing-root')
        expect_raises(OSError, lambda: list(paths.glob(broken_root, '*.toml')),
                      'dangling discovery root was ignored')
        nested = root / 'nested'
        nested.mkdir()
        bridge = nested / 'bridge'
        bridge.symlink_to('missing-directory')
        for candidate in (bridge / 'subdir', bridge / 'subdir' / 'file.toml'):
            expect_raises(OSError, lambda candidate=candidate: paths.candidate_directory(candidate),
                          'dangling ancestor was ignored for a directory candidate')
            expect_raises(OSError, lambda candidate=candidate: paths.candidate_file(candidate),
                          'dangling ancestor was ignored for a file candidate')
        expect_raises(OSError, lambda: list(paths.glob(bridge / 'subdir', '*.toml')),
                      'dangling ancestor was ignored for a discovery root')
        bridge.unlink()
        (nested / 'real').mkdir()
        bridge.symlink_to('real')
        require(paths.candidate_directory(bridge))
        require(not paths.candidate_file(bridge / 'subdir' / 'missing.toml'))
        file_root = root / 'file-root'
        file_root.write_text('not a directory')
        expect_raises(OSError, lambda: list(paths.glob(file_root, '*.toml')),
                      'file used as discovery root was ignored')
        for pattern in ('../secret', 'core//alpha', 'core/*x*y'):
            expect_raises(ValueError, lambda: list(paths.glob(root, pattern)),
                          'unsafe or unsupported path pattern accepted: ' + pattern)


def test_observed_directory_disappearance() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        profile = root / 'profiles/p1'
        profile.mkdir(parents=True)
        (profile / 'ontology.toml').write_text('')
        (root / 'profiles/README.md').write_text('notes')
        require(list(paths.glob(root, 'profiles/*/ontology.toml')) == [profile / 'ontology.toml'])
        original = paths.candidate_directory

        def vanish(path: Path) -> bool:
            if path == profile:
                shutil.rmtree(profile)
            return original(path)

        with patch.object(paths, 'candidate_directory', side_effect=vanish):
            expect_raises(OSError, lambda: list(paths.glob(root, 'profiles/*/ontology.toml')),
                          'observed profile directory disappeared without failing the scan')


if __name__ == '__main__':
    test_path_shapes()
    test_observed_directory_disappearance()
    print('literal path scanner: accepted and rejected cases passed')
