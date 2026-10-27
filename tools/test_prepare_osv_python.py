#!/usr/bin/env python3
"""Accepted and rejected boundaries for Python lockfile scan coverage."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from prepare_osv_python import canonical_name, cleanup, pins, stage, verify


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
        lock = root / "requirements" / "sample.txt"
        lock.write_text("Foo_.BAR==1.0\n")
        git = shutil.which("git")
        require(git is not None, "git executable missing")
        # Resolved executable and fixed arguments; no shell or user input.
        subprocess.run([git, "init", "-q"], cwd=root, check=True)  # noqa: S603  # nosec B603
        subprocess.run([git, "add", "requirements/sample.txt"], cwd=root, check=True)  # noqa: S603  # nosec B603
        stage(root)
        alias = root / "osv-python-lockfiles" / "sample" / "requirements.txt"
        require(alias.read_bytes() == lock.read_bytes(), "staged bytes differ")
        result = root / "osv-scan-results.json"
        entry = {
            "source": {"path": str(alias), "type": "lockfile"},
            "packages": [{"package": {"name": "foo-bar", "version": "1.0", "ecosystem": "PyPI"}}],
        }
        result.write_text(json.dumps({"results": [entry]}))
        decoder = json.JSONDecoder.decode
        def forbidden_decode(self, source):
            raise AssertionError("regex JSON whitespace matcher was used")
        json.JSONDecoder.decode = forbidden_decode
        try:
            verify(root, result)
        finally:
            json.JSONDecoder.decode = decoder
        result.write_bytes(b"{")
        error = expect_rejection(lambda: verify(root, result), "malformed scanner JSON accepted")
        require("source sha256" in str(error), "malformed JSON digest is missing")
        require("line" not in str(error) and "column" not in str(error), "JSON parser coordinates escaped")
        result.unlink()
        expect_rejection(lambda: verify(root, result), "missing scanner result accepted")
        entry["packages"] = []
        result.write_text(json.dumps({"results": [entry]}))
        expect_rejection(lambda: verify(root, result), "missing scanner package accepted")
        cleanup(root)
        require(not alias.exists() and not result.exists(), "cleanup left scan output")
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
