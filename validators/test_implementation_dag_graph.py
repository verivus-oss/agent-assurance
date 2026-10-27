#!/usr/bin/env python3
"""Hand-derived graph examples for the implementation DAG validator."""

import unittest
import sys

from validate_implementation_dag import detect_cycles, longest_path_loc, parse_args


class GraphTests(unittest.TestCase):
    def test_distinct_cycles_and_acyclic_nodes(self) -> None:
        edges = {
            "A": {"B", "C"},
            "B": {"C", "D"},
            "C": {"A"},
            "D": {"B"},
            "E": {"E"},
            "F": {"Z"},
            "G": set(),
        }
        self.assertEqual(
            detect_cycles(edges),
            [
                "cycle in depends_on: A -> B -> C -> A",
                "cycle in depends_on: A -> C -> A",
                "cycle in depends_on: B -> D -> B",
                "cycle in depends_on: E -> E",
            ],
        )
        self.assertEqual(detect_cycles({"A": {"B"}, "B": set()}), [])

    def test_longest_weighted_path_and_cycle_rejection(self) -> None:
        units = {
            "A": {"estimated_loc": 2},
            "B": {"estimated_loc": 4},
            "C": {"estimated_loc": 3},
            "D": {"estimated_loc": 10},
            "E": {"estimated_loc": 1},
        }
        edges = {"A": {"B", "C"}, "B": {"D"}, "C": {"D"}, "D": set(), "E": set()}
        self.assertEqual(longest_path_loc(units, edges), 16)
        self.assertEqual(longest_path_loc({}, {}), 0)
        edges["D"].add("A")
        self.assertIsNone(longest_path_loc(units, edges))

    def test_deep_chain_uses_explicit_stacks(self) -> None:
        length = 2000
        units = {f"U{i}": {"estimated_loc": 1} for i in range(length)}
        edges = {f"U{i}": {f"U{i + 1}"} for i in range(length - 1)}
        edges[f"U{length - 1}"] = set()
        self.assertEqual(detect_cycles(edges), [])
        self.assertEqual(longest_path_loc(units, edges), length)

    def test_cli_accepts_exact_options_and_rejects_unknown(self) -> None:
        original = sys.argv
        try:
            sys.argv = ["validator", "--repo-root", "repo", "--check-paths-exist", "file.toml"]
            parsed = parse_args()
            self.assertEqual(parsed.dag_file, "file.toml")
            self.assertEqual(parsed.repo_root, "repo")
            self.assertTrue(parsed.check_paths_exist)
            sys.argv = ["validator", "--unknown", "file.toml"]
            with self.assertRaises(SystemExit) as error:
                parse_args()
            self.assertEqual(error.exception.code, 2)
            sys.argv = ["validator", "--repo-root", "--check-paths-exist", "file.toml"]
            with self.assertRaises(SystemExit) as error:
                parse_args()
            self.assertEqual(error.exception.code, 2)
        finally:
            sys.argv = original


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GraphTests)
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        raise SystemExit(1)
