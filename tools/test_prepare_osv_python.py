#!/usr/bin/env python3
"""Accepted and rejected boundaries for Python lockfile scan coverage."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from prepare_osv_python import canonical_name, cleanup, pins, stage, verify


class OsvPythonTests(unittest.TestCase):
    def test_name_and_compact_marker(self) -> None:
        self.assertEqual(canonical_name("Foo_.BAR"), "foo-bar")
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "requirements.txt"
            lock.write_text('Foo_.BAR==1.0;python_version<"3.13"\n')
            self.assertEqual(pins(lock), {("foo-bar", "1.0")})
            lock.write_text('Foo==;python_version<"3.13"\n')
            with self.assertRaises(SystemExit):
                pins(lock)

    def test_coverage_and_cleanup_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "requirements").mkdir()
            lock = root / "requirements" / "sample.txt"
            lock.write_text("Foo_.BAR==1.0\n")
            git = shutil.which("git")
            self.assertIsNotNone(git)
            # Resolved executable and fixed arguments; no shell or user input.
            subprocess.run([git, "init", "-q"], cwd=root, check=True)  # noqa: S603  # nosec B603
            subprocess.run([git, "add", "requirements/sample.txt"], cwd=root, check=True)  # noqa: S603  # nosec B603
            stage(root)
            alias = root / "osv-python-lockfiles" / "sample" / "requirements.txt"
            self.assertEqual(alias.read_bytes(), lock.read_bytes())
            result = root / "osv-scan-results.json"
            entry = {
                "source": {"path": str(alias), "type": "lockfile"},
                "packages": [{"package": {"name": "foo-bar", "version": "1.0", "ecosystem": "PyPI"}}],
            }
            result.write_text(json.dumps({"results": [entry]}))
            verify(root, result)
            entry["packages"] = []
            result.write_text(json.dumps({"results": [entry]}))
            with self.assertRaises(SystemExit):
                verify(root, result)
            cleanup(root)
            self.assertFalse(alias.exists())
            self.assertFalse(result.exists())
            (root / "osv-python-lockfiles").symlink_to(lock)
            with self.assertRaises(SystemExit):
                cleanup(root)
            self.assertTrue((root / "osv-python-lockfiles").is_symlink())
            (root / "osv-python-lockfiles").unlink()
            (root / "requirements" / "link.txt").symlink_to(lock)
            subprocess.run([git, "add", "requirements/link.txt"], cwd=root, check=True)  # noqa: S603  # nosec B603
            with self.assertRaises(SystemExit):
                stage(root)


if __name__ == "__main__":
    unittest.main()
