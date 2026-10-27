"""Malformed profile descriptors must not vanish from discovery checks."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys

import _toml11 as tomllib
from _test_require import expect_raises, require
from validate_closure_root import (
    _loaded_profile_names,
    discover_conforming,
    duplicate_profile_names,
    load_pinned_records,
    main as closure_main,
    spec_reserved_kinds,
)
from validate_ijb_conformance import discover_profile_descriptors, validate_meta_posture
from validate_profile_descriptor import discover_descriptors, main as profile_main, validate_one


def test_discovery_rejects_malformed_profile() -> None:
    repository = Path(__file__).resolve().parent.parent
    require(not duplicate_profile_names(repository))
    require("agent-assurance" in discover_profile_descriptors(repository))
    require("agent-assurance" in discover_descriptors(repository))

    with TemporaryDirectory(prefix="profile-discovery-control-") as directory:
        root = Path(directory)
        candidate = root / "profiles/broken/PROFILE.toml"
        candidate.parent.mkdir(parents=True)
        candidate.write_text("[meta\n")
        for action in (
            lambda: duplicate_profile_names(root),
            lambda: load_pinned_records(root),
            lambda: _loaded_profile_names(root),
            lambda: discover_profile_descriptors(root),
            lambda: discover_descriptors(root),
        ):
            expect_raises(tomllib.TOMLDecodeError, action,
                          "malformed profile descriptor was ignored")

        errors = validate_meta_posture({"meta": {"framework_profile": "broken"}},
                                       str(candidate), root)
        require(any("cannot inspect profile descriptors" in error for error in errors))

        diagnostic = StringIO()
        with redirect_stderr(diagnostic):
            require(closure_main(["--repo-root", str(root), str(candidate)]) == 1)
        require("profile descriptor discovery" in diagnostic.getvalue())

        output = StringIO()
        with patch.object(sys, "argv", ["validate_profile_descriptor.py", "--repo-root", str(root), str(candidate)]), redirect_stdout(output):
            require(profile_main() == 1)
        require("cannot inspect descriptors" in output.getvalue())

        candidate.unlink()
        candidate.symlink_to("missing-profile.toml")
        for action in (
            lambda: duplicate_profile_names(root),
            lambda: load_pinned_records(root),
            lambda: _loaded_profile_names(root),
            lambda: discover_profile_descriptors(root),
            lambda: discover_descriptors(root),
        ):
            expect_raises(OSError, action, "dangling profile descriptor was ignored")
        candidate.unlink()
        (root / "profiles/README.md").write_text("notes\n")
        ghost = root / "profiles/ghost"
        ghost.symlink_to("missing-directory")
        for action in (
            lambda: duplicate_profile_names(root),
            lambda: load_pinned_records(root),
            lambda: _loaded_profile_names(root),
            lambda: discover_profile_descriptors(root),
            lambda: discover_descriptors(root),
        ):
            expect_raises(OSError, action, "dangling profile directory was ignored")
        ghost.unlink()

        candidate.write_text(
            '[meta]\ntemplate_kind = "profile-descriptor"\n'
            '[profile]\nname = "broken"\nnamespace = "broken"\n'
            'owner = "test"\nlicense = "MIT"\n'
            'extends = []\nontology = "core/ontology.toml"\n'
            'contained_kinds = ["widget"]\n'
        )
        kind = candidate.parent / "widget-kind.toml"
        kind.write_text("[meta\n")
        document = tomllib.loads_bytes(candidate.read_bytes())
        errors = validate_one(candidate, root, {"broken": (candidate, document)})
        require(any("cannot parse kind descriptor" in error for error in errors))
        kind.unlink()
        kind.symlink_to("missing-kind.toml")
        errors = validate_one(candidate, root, {"broken": (candidate, document)})
        require(any("dangling discovery candidate" in error for error in errors))

        (root / "profiles/README.md").unlink()
        (root / "profiles/broken").rename(root / "retired-profile")
        (root / "profiles").rmdir()
        (root / "profiles").write_text("not a directory")
        for action in (
            lambda: duplicate_profile_names(root),
            lambda: load_pinned_records(root),
            lambda: _loaded_profile_names(root),
            lambda: discover_profile_descriptors(root),
            lambda: discover_descriptors(root),
        ):
            expect_raises(OSError, action, "file used as profile root was ignored")
        (root / "profiles").unlink()
        for action in (
            lambda: duplicate_profile_names(root),
            lambda: load_pinned_records(root),
            lambda: _loaded_profile_names(root),
            lambda: discover_profile_descriptors(root),
            lambda: discover_descriptors(root),
        ):
            expect_raises(OSError, action, "missing profile root was ignored")


def test_closure_discovery_rejects_malformed_candidates() -> None:
    with TemporaryDirectory(prefix="closure-discovery-control-") as directory:
        root = Path(directory)
        descriptor = root / "core/widget-kind.toml"
        descriptor.parent.mkdir()
        (root / "profiles").mkdir()
        descriptor.write_text('[kind]\nname = "widget"\n')
        kinds = spec_reserved_kinds(root)
        require("widget" in kinds)

        examples = root / "examples"
        examples.mkdir()
        good = examples / "good.toml"
        bad = examples / "bad.toml"
        good.write_text('[meta]\ntemplate_kind = "widget"\n')
        bad.write_text("[meta\n")
        require(discover_conforming([examples], kinds, lambda path: path == bad) == [good])
        expect_raises(OSError, lambda: discover_conforming([examples, root / "missing"], kinds,
                                                            lambda path: path == bad),
                      "missing explicit closure root was ignored")
        bridge = root / "bridge"
        bridge.symlink_to("missing-directory")
        expect_raises(OSError, lambda: discover_conforming([examples, bridge / "subdir"], kinds,
                                                            lambda path: path == bad),
                      "dangling ancestor silently removed an explicit closure root")
        failure = expect_raises(ValueError, lambda: discover_conforming([examples], kinds),
                                "malformed closure candidate was ignored")
        require("cannot inspect TOML candidate" in str(failure))

        diagnostic = StringIO()
        with redirect_stderr(diagnostic):
            require(closure_main(["--repo-root", str(root), "--discover", str(examples)]) == 1)
        require("FAIL closure discovery" in diagnostic.getvalue())

        descriptor.write_text("[kind\n")
        failure = expect_raises(ValueError, lambda: spec_reserved_kinds(root),
                                "malformed kind descriptor was ignored")
        require("cannot inspect kind descriptor" in str(failure))
        descriptor.unlink()
        descriptor.symlink_to("missing-kind.toml")
        expect_raises(OSError, lambda: spec_reserved_kinds(root),
                      "dangling kind descriptor was ignored")


def test_dangling_profile_cannot_remove_required_pin() -> None:
    with TemporaryDirectory(prefix="profile-pin-control-") as directory:
        root = Path(directory)
        profile = root / "profiles/p/PROFILE.toml"
        profile.parent.mkdir(parents=True)
        profile.write_text('[meta]\ntemplate_kind = "profile-descriptor"\n'
                           '[profile]\nname = "p"\n'
                           '[[profile.closure_records]]\ncontained_kind = "widget"\n'
                           'field = "some.digest"\npresence = "required"\n')
        value = "sha256:" + "1" * 64
        record = f"some.digest {value}\n".encode()
        root_hash = "sha256:" + hashlib.sha256(record).hexdigest()
        document = root / "doc.toml"
        document.write_text(f'closure_root = "{root_hash}"\n'
                            '[meta]\ntemplate_kind = "widget"\nframework_profile = "p"\n'
                            f'[some]\ndigest = "{value}"\n')
        with redirect_stderr(StringIO()), redirect_stdout(StringIO()):
            require(closure_main(["--repo-root", str(root), str(document)]) == 0)

        document.write_text('closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"\n'
                            '[meta]\ntemplate_kind = "widget"\nframework_profile = "p"\n')
        valid_error = StringIO()
        with redirect_stderr(valid_error):
            require(closure_main(["--repo-root", str(root), str(document)]) == 1)
        require("pinned closure record" in valid_error.getvalue())

        profile.unlink()
        profile.symlink_to("missing-profile.toml")
        dangling_error = StringIO()
        with redirect_stderr(dangling_error):
            require(closure_main(["--repo-root", str(root), str(document)]) == 1)
        require("dangling discovery candidate" in dangling_error.getvalue())


if __name__ == "__main__":
    test_discovery_rejects_malformed_profile()
    test_closure_discovery_rejects_malformed_candidates()
    test_dangling_profile_cannot_remove_required_pin()
    print("profile discovery: accepted and rejected source cases passed")
