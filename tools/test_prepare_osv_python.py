#!/usr/bin/env python3
"""Accepted and rejected boundaries for Python lockfile scan coverage."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from prepare_osv_python import canonical_name, cleanup, pins, stage, staged_path, tracked_sources, verify
from _literal_json import dumps as dumps_json


def require(condition: object, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_rejection(action, message: str) -> SystemExit:
    try:
        action()
    except SystemExit as error:
        require(str(error), f"{message}: missing diagnostic")
        return error
    raise AssertionError(message)


def test_name_and_compact_marker() -> None:
    require(canonical_name("Foo_.BAR") == "foo-bar", "package name was not canonicalized")
    with tempfile.TemporaryDirectory() as directory:
        lock = Path(directory) / "requirements.txt"
        lock.write_text('Foo_.BAR==1.0;python_version<"3.13"\n')
        require(pins(lock) == {("foo-bar", "1.0")}, "compact marker was not parsed")
        lock.write_text('Foo==;python_version<"3.13"\n')
        expect_rejection(lambda: pins(lock), "empty pinned version accepted")
        lock.write_bytes(b"Foo==1.0\xff\n")
        error = expect_rejection(lambda: pins(lock), "invalid UTF-8 lock accepted")
        require("bytes 8:9" in str(error), "invalid lock byte span is missing")


def test_coverage_and_cleanup_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "requirements").mkdir()
        root_lock = root / "requirements.txt"
        root_lock.write_text("RootPkg==2.0 --hash=sha256:abc\n")
        lock = root / "requirements" / "sample.txt"
        lock.write_text("Foo_.BAR==1.0\n")
        git = shutil.which("git")
        require(git is not None, "git executable missing")
        # Resolved executable and fixed arguments; no shell or user input.
        subprocess.run([git, "init", "-q"], cwd=root, check=True)  # noqa: S603  # nosec B603
        subprocess.run([git, "add", "requirements.txt", "requirements/sample.txt"], cwd=root, check=True)  # noqa: S603  # nosec B603
        require(set(tracked_sources(root)) == {root_lock, lock}, "tracked lock population omitted an installer entry point")
        stage(root)
        alias = staged_path(root, lock)
        root_alias = staged_path(root, root_lock)
        require(alias.read_bytes() == lock.read_bytes(), "staged bytes differ")
        require(root_alias.read_bytes() == root_lock.read_bytes(), "root installer entry point was not staged")
        result = root / "osv-scan-results.json"
        entry = {
            "source": {"path": str(alias), "type": "lockfile"},
            "packages": [{"package": {"name": "foo-bar", "version": "1.0", "ecosystem": "PyPI"}}],
        }
        root_entry = {
            "source": {"path": str(root_alias), "type": "lockfile"},
            "packages": [{"package": {"name": "rootpkg", "version": "2.0", "ecosystem": "PyPI"}}],
        }
        result.write_text(dumps_json({"results": [entry, root_entry]}))
        decoder = json.JSONDecoder.decode
        def forbidden_decode(self, source):
            raise AssertionError("regex JSON whitespace matcher was used")
        json.JSONDecoder.decode = forbidden_decode
        try:
            verify(root, result)
        finally:
            json.JSONDecoder.decode = decoder
        unknown = {
            "source": {"path": str(root / "osv-python-lockfiles" / "unknown" / "requirements.txt"),
                       "type": "lockfile"},
            "packages": [],
        }
        result.write_text(dumps_json({"results": [entry, root_entry, unknown]}))
        expect_rejection(lambda: verify(root, result), "unknown scanner alias accepted")
        result.write_text(dumps_json({"results": [entry]}))
        expect_rejection(lambda: verify(root, result), "missing root package scan accepted")
        result.write_bytes(b"{")
        error = expect_rejection(lambda: verify(root, result), "malformed scanner JSON accepted")
        require("source sha256" in str(error), "malformed JSON digest is missing")
        require("line" not in str(error) and "column" not in str(error), "JSON parser coordinates escaped")
        result.unlink()
        expect_rejection(lambda: verify(root, result), "missing scanner result accepted")
        entry["packages"] = []
        result.write_text(dumps_json({"results": [entry, root_entry]}))
        expect_rejection(lambda: verify(root, result), "missing scanner package accepted")
        entry["packages"] = [{"package": {"name": "foo-bar", "version": "1.0", "ecosystem": "PyPI"}}]
        root_lock.write_text("# no root runtime package\n")
        root_alias.write_bytes(root_lock.read_bytes())
        result.write_text(dumps_json({"results": [entry]}))
        verify(root, result)
        root_entry["packages"] = []
        result.write_text(dumps_json({"results": [entry, root_entry]}))
        verify(root, result)
        cleanup(root)
        require(not alias.exists() and not root_alias.exists() and not result.exists(), "cleanup left scan output")
        staging = root / "osv-python-lockfiles"
        staging.symlink_to(lock)
        expect_rejection(lambda: cleanup(root), "symlink cleanup accepted")
        require(staging.is_symlink(), "cleanup followed staging symlink")
        staging.unlink()
        (root / "requirements" / "link.txt").symlink_to(lock)
        subprocess.run([git, "add", "requirements/link.txt"], cwd=root, check=True)  # noqa: S603  # nosec B603
        expect_rejection(lambda: stage(root), "symlinked tracked lock accepted")


if __name__ == "__main__":
    test_name_and_compact_marker()
    test_coverage_and_cleanup_fail_closed()
    print("OSV Python lockfile boundary tests: 2 groups passed")
