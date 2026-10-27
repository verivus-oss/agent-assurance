"""Malformed profile descriptors must not vanish from discovery checks."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
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

        candidate.write_text(
            '[meta]\ntemplate_kind = "profile-descriptor"\n'
            '[profile]\nname = "broken"\nnamespace = "broken"\n'
            'owner = "test"\nlicense = "MIT"\n'
            'extends = []\nontology = "core/ontology.toml"\n'
            'contained_kinds = ["widget"]\n'
        )
        kind = candidate.parent / "widget-kind.toml"
        kind.write_text("[meta\n")
        document = tomllib.loads(candidate.read_text())
        errors = validate_one(candidate, root, {"broken": (candidate, document)})
        require(any("cannot parse kind descriptor" in error for error in errors))


def test_closure_discovery_rejects_malformed_candidates() -> None:
    with TemporaryDirectory(prefix="closure-discovery-control-") as directory:
        root = Path(directory)
        descriptor = root / "core/widget-kind.toml"
        descriptor.parent.mkdir()
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


if __name__ == "__main__":
    test_discovery_rejects_malformed_profile()
    test_closure_discovery_rejects_malformed_candidates()
    print("profile discovery: accepted and rejected source cases passed")
