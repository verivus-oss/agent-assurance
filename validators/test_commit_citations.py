#!/usr/bin/env python3
"""Accepted and rejected cases for the commit citation scanner."""

import pathlib
import sys
import unittest

from check_commit_citations import commit_tokens, governed_file, parse_args


class CitationTests(unittest.TestCase):
    def test_commit_words_and_noncommit_words(self) -> None:
        self.assertEqual(commit_tokens("opened_in_commit: 9996826"), {"9996826"})
        self.assertEqual(commit_tokens("commit `A1b2C3d`"), {"a1b2c3d"})
        self.assertEqual(commit_tokens("feedback 123456 0123456789abcdef"), {"0123456789abcdef"})
        self.assertEqual(commit_tokens("prefix_abcdef0 suffixabcdef0"), set())

    def test_uuid_segments_are_not_citations(self) -> None:
        self.assertEqual(commit_tokens("job 12345678-1234-abcd-5678-123456789abc"), set())
        self.assertEqual(
            commit_tokens("commit 9996826 beside 12345678-1234-abcd-5678-123456789abc"),
            {"9996826"},
        )
        self.assertEqual(
            commit_tokens("deadbeefcafe 12345678-1234-1234-1234-123456789abc"),
            {"deadbeefcafe"},
        )
        self.assertEqual(commit_tokens("deadbeefcafe12345678-1234-1234-1234-123456789abc"), set())
        self.assertEqual(commit_tokens("12345678-1234-1234-1234-123456789abcdeadbeefcafe"), set())

    def test_scan_population_excludes_vendor_and_unit_fixtures(self) -> None:
        root = pathlib.Path("/repo")
        self.assertTrue(governed_file(root / "docs/issues/issue.md", root))
        self.assertTrue(governed_file(root / "validators/check_commit_citations.py", root))
        self.assertTrue(governed_file(root / "validators/_toml11_vendor/README.md", root))
        self.assertFalse(governed_file(root / "validators/_toml11_vendor/_scan.py", root))
        self.assertFalse(governed_file(root / "validators/test_toml11_scanner.py", root))

    def test_cli_accepts_exact_options_and_rejects_missing_values(self) -> None:
        original = sys.argv
        try:
            sys.argv = ["checker", "--repo-root", "repo", "--baseline=record.toml"]
            args = parse_args()
            self.assertEqual((args.repo_root, args.baseline), ("repo", "record.toml"))
            sys.argv = ["checker", "--repo-root"]
            with self.assertRaises(SystemExit) as error:
                parse_args()
            self.assertEqual(error.exception.code, 2)
            for invalid in ("--repo-root=", "--baseline="):
                sys.argv = ["checker", invalid]
                with self.assertRaises(SystemExit) as error:
                    parse_args()
                self.assertEqual(error.exception.code, 2)
        finally:
            sys.argv = original


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CitationTests)
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        raise SystemExit(1)
