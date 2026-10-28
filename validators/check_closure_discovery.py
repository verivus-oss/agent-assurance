#!/usr/bin/env python3
"""Assert discovery exclusions apply below each explicitly selected root."""

import _literal_json as json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from _literal_path import Path
from _random_id import random_id_hex

from validate_closure_root import (
    _loaded_profile_names,
    discover_conforming,
    duplicate_profile_names,
    load_pinned_records,
    main as closure_main,
    spec_reserved_kinds,
)
from validate_ijb_conformance import discover_profile_descriptors, validate_meta_posture
from validate_profile_descriptor import discover_descriptors
from validate_disclosure import load_vocabularies


def expect_parse_failure(operation, source):
    try:
        operation()
    except ValueError as exc:
        if str(source) not in str(exc) or "invalid UTF-8" not in str(exc):
            raise AssertionError(f"parse failure lost its source: {exc}") from exc
    else:
        raise AssertionError(f"invalid UTF-8 was silently accepted: {source}")


def expect_cli_failure(repo, root, source):
    diagnostic = StringIO()
    with redirect_stderr(diagnostic):
        result = closure_main(["--repo-root", str(repo), "--discover", str(root)])
    if result != 1 or str(source) not in diagnostic.getvalue():
        raise AssertionError(f"discovery CLI did not reject {source}: {diagnostic.getvalue()}")


def main():
    work = Path(".local/closure-discovery") / random_id_hex()
    (work / "profiles").mkdir(parents=True)
    (work / "core").mkdir()
    root = work / "source"
    accepted = {"visible.toml", "nested/visible.toml"}
    excluded = {".hidden.toml", ".hidden/visible.toml", "target/visible.toml",
                "node_modules/visible.toml", "__pycache__/visible.toml"}
    for name in accepted | excluded:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('[meta]\ntemplate_kind = "implementation-dag"\n')
    (root / "unrelated.toml").write_text('[meta]\ntemplate_kind = "process-note"\n')
    kinds = frozenset({"implementation-dag"})
    observations = []
    for name, selected in (("relative", root), ("absolute", root.resolve())):
        actual = {path.relative_to(selected).as_posix() for path in discover_conforming([selected], kinds)}
        if actual != accepted:
            raise AssertionError(f"{name} root: expected {sorted(accepted)}, observed {sorted(actual)}")
        observations.append({"root_form": name, "accepted": sorted(actual), "excluded": sorted(excluded | {"unrelated.toml"})})
    # Explicit file selection remains supported, including hidden files.
    selected = root / ".hidden.toml"
    if discover_conforming([selected], kinds) != [selected]:
        raise AssertionError("explicit conforming file selection was excluded")
    malformed = root / "malformed.toml"
    malformed.write_bytes(b'[meta]\ntemplate_kind = "implementation-dag"\n\xff')
    expect_parse_failure(lambda: discover_conforming([root], kinds), malformed)
    expect_cli_failure(work, root, malformed)
    malformed.unlink()
    wrong_type = root / "wrong-type.toml"
    for value in ("1", "true", "[\"implementation-dag\"]"):
        wrong_type.write_text(f"[meta]\ntemplate_kind = {value}\n")
        try:
            discover_conforming([root], kinds)
        except ValueError as exc:
            if str(wrong_type) not in str(exc) or "not a string" not in str(exc):
                raise AssertionError(f"wrong-type kind lost its source: {exc}") from exc
        else:
            raise AssertionError(f"wrong-type kind was silently skipped: {value}")
        expect_cli_failure(work, root, wrong_type)
    wrong_type.unlink()

    sweep = work / "sweep"
    sweep.mkdir()
    (sweep / "accepted.toml").write_text(
        'closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"\n'
        '[meta]\ntemplate_kind = "kind-descriptor"\n'
    )
    rejected = sweep / "negative" / "malformed.toml"
    rejected.parent.mkdir()
    rejected.write_bytes(b"[meta]\n\xff")
    output = StringIO()
    with redirect_stdout(output):
        result = closure_main([
            "--repo-root", str(work), "--discover", str(sweep),
            "--exclude", str(rejected.parent),
        ])
    if result != 0 or str(rejected) not in output.getvalue():
        raise AssertionError("asserted-negative malformed TOML was not excluded before parsing")

    repo = work / "repo"
    profile = repo / "profiles" / "broken" / "PROFILE.toml"
    profile.parent.mkdir(parents=True)
    profile.write_bytes(b'[meta]\ntemplate_kind = "profile-descriptor"\n\xff')
    expect_cli_failure(repo, root, profile)
    profile_operations = (
        lambda: duplicate_profile_names(repo),
        lambda: load_pinned_records(repo),
        lambda: _loaded_profile_names(repo),
        lambda: discover_profile_descriptors(repo),
        lambda: discover_descriptors(repo),
    )
    for operation in profile_operations:
        expect_parse_failure(operation, profile)
    posture_errors = validate_meta_posture(
        {"meta": {"framework_profile": "broken"}}, "captured", repo
    )
    if not any(str(profile) in error for error in posture_errors):
        raise AssertionError("invalid profile did not reject IJB posture validation")
    profile.unlink()
    profile.symlink_to("missing-profile.toml")
    for operation in profile_operations:
        try:
            operation()
        except (OSError, ValueError) as exc:
            if str(profile) not in str(exc):
                raise AssertionError(f"missing profile source in error: {exc}") from exc
        else:
            raise AssertionError("dangling profile link was silently skipped")
    profile.unlink()
    profile.write_text('[meta]\ntemplate_kind = "profile-descriptor"\n[profile]\nname = "valid"\n')
    if _loaded_profile_names(repo) != frozenset({"valid"}):
        raise AssertionError("valid profile was not discovered")
    if "valid" not in discover_descriptors(repo):
        raise AssertionError("valid profile was not discovered by descriptor validator")
    for bad_declaration in (
        '[meta]\ntemplate_kind = "profile-descriptor"\n[profile]\nname = 42\n',
        '[meta]\ntemplate_kind = "profile-descriptor"\n[profile]\nname = ""\n',
        '[meta]\ntemplate_kind = "profile-descriptor"\n[profile]\n',
        '[meta]\ntemplate_kind = "implementation-dag"\n[profile]\nname = "wrong-kind"\n',
    ):
        profile.write_text(bad_declaration)
        for operation in profile_operations:
            try:
                operation()
            except ValueError as exc:
                if str(profile) not in str(exc):
                    raise AssertionError(f"invalid declaration lost its source: {exc}") from exc
            else:
                raise AssertionError(f"invalid profile was silently skipped: {profile}")
        expect_cli_failure(repo, root, profile)
    profile.write_text('[meta]\ntemplate_kind = "profile-descriptor"\n[profile]\nname = "valid"\n')

    descriptor = repo / "core" / "broken-kind.toml"
    descriptor.parent.mkdir(parents=True)
    descriptor.write_bytes(b'[kind]\nname = "broken"\n\xff')
    expect_parse_failure(lambda: spec_reserved_kinds(repo), descriptor)
    expect_cli_failure(repo, root, descriptor)
    descriptor.unlink()
    descriptor.write_text('[meta]\ntemplate_kind = "kind-descriptor"\ndescribes_kind = "valid-kind"\n'
                          '[kind]\nname = "valid-kind"\n')
    if "valid-kind" not in spec_reserved_kinds(repo):
        raise AssertionError("valid kind descriptor was not discovered")
    for bad_declaration in (
        '[meta]\ntemplate_kind = "kind-descriptor"\n[kind]\nname = "bad"\n',
        '[meta]\ntemplate_kind = "kind-descriptor"\ndescribes_kind = "different"\n'
        '[kind]\nname = "bad"\n',
        '[meta]\ntemplate_kind = "implementation-dag"\n[kind]\nname = "bad"\n',
    ):
        descriptor.write_text(bad_declaration)
        try:
            spec_reserved_kinds(repo)
        except ValueError as exc:
            if str(descriptor) not in str(exc):
                raise AssertionError(f"invalid kind lost its source: {exc}") from exc
        else:
            raise AssertionError(f"invalid kind was silently skipped: {descriptor}")
        expect_cli_failure(repo, root, descriptor)
    descriptor.write_text('[meta]\ntemplate_kind = "kind-descriptor"\ndescribes_kind = "valid-kind"\n'
                          '[kind]\nname = "valid-kind"\n')

    ontology = repo / "profiles" / "disclosure" / "ontology.toml"
    ontology.parent.mkdir(parents=True)
    ontology.write_bytes(b"[meta]\n\xff")
    expect_parse_failure(lambda: load_vocabularies(repo), ontology)
    ontology.write_text("[meta]\ntemplate_kind = 'ontology'\n")
    if load_vocabularies(repo) != {}:
        raise AssertionError("valid empty disclosure vocabulary was not accepted")
    ontology.unlink()
    try:
        load_vocabularies(repo)
    except ValueError as exc:
        if str(ontology) not in str(exc):
            raise AssertionError(f"missing ontology source in error: {exc}") from exc
    else:
        raise AssertionError("missing disclosure ontology was silently accepted")
    (work / "receipt.json").write_text(json.dumps({"status": "passed", "observations": observations,
                                                "explicit_hidden_file": "accepted"}, indent=2) + "\n")
    print("PASS: relative and absolute discovery, valid declarations, and invalid UTF-8 "
          "failure controls; skipped=[]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
