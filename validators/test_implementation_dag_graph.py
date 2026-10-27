#!/usr/bin/env python3
"""Hand-derived graph examples for the implementation DAG validator."""

import unittest
import sys
import time
from contextlib import redirect_stderr
from io import StringIO

from validate_implementation_dag import detect_cycles, load_toml, longest_path_loc, main, parse_args
from pathlib import Path
from tempfile import TemporaryDirectory


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

    def test_cycle_unblocks_waiting_predecessors(self) -> None:
        edges = {"Z": {"D", "Z"}, "D": {"Z", "U10", "D", "B"},
                 "U10": {"Z", "U10", "D", "B"}, "B": {"U10"}}
        self.assertIn(
            "cycle in depends_on: B -> U10 -> Z -> D -> B",
            detect_cycles(edges),
        )

    def test_deep_chain_uses_explicit_stacks(self) -> None:
        length = 2000
        units = {f"U{i}": {"estimated_loc": 1} for i in range(length)}
        edges = {f"U{i}": {f"U{i + 1}"} for i in range(length - 1)}
        edges[f"U{length - 1}"] = set()
        self.assertEqual(detect_cycles(edges), [])
        self.assertEqual(longest_path_loc(units, edges), length)

    def test_branching_ladder_has_bounded_cycle_search(self) -> None:
        edges: dict[str, set[str]] = {"A0000": set()}
        previous = "A0000"
        for index in range(1, 25):
            left = f"N{index:04d}a"
            right = f"N{index:04d}b"
            join = f"C{index:04d}"
            return_node = f"R{index:04d}"
            edges[previous].update((left, right))
            edges[left] = {join}
            edges[right] = {join}
            edges[join] = {return_node}
            edges[return_node] = {previous}
            previous = join
        started = time.perf_counter()
        cycles = detect_cycles(edges)
        self.assertEqual(len(cycles), 48)
        self.assertLess(time.perf_counter() - started, 10)

    def test_large_single_ring_does_not_rescan_each_node(self) -> None:
        size = 8000
        nodes = [f"U{index:05d}" for index in range(size)]
        edges = {nodes[index]: {nodes[(index + 1) % size]} for index in range(size)}
        started = time.perf_counter()
        cycles = detect_cycles(edges)
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0].count(" -> "), size)
        self.assertLess(time.perf_counter() - started, 5)

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
            sys.argv = ["validator", "--repo-root=", "file.toml"]
            with self.assertRaises(SystemExit) as error:
                parse_args()
            self.assertEqual(error.exception.code, 2)
            sys.argv = ["validator", "--repo-root", "", "file.toml"]
            with self.assertRaises(SystemExit) as error:
                parse_args()
            self.assertEqual(error.exception.code, 2)
        finally:
            sys.argv = original

    def test_invalid_utf8_has_stable_byte_evidence(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.toml"
            path.write_bytes(b'name = "caf\xff"\n')
            with self.assertRaises(ValueError) as error:
                load_toml(path)
            self.assertIn("invalid UTF-8", str(error.exception))
            self.assertIn("bytes 11:12", str(error.exception))
            original = sys.argv
            error_output = StringIO()
            try:
                sys.argv = ["validator", str(path)]
                with redirect_stderr(error_output):
                    self.assertEqual(main(), 2)
            finally:
                sys.argv = original
            self.assertIn("invalid UTF-8", error_output.getvalue())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GraphTests)
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        raise SystemExit(1)
