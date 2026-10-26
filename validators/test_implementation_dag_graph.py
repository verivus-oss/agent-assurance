#!/usr/bin/env python3
"""Hand-derived graph examples for the implementation DAG validator."""

import unittest

from validate_implementation_dag import detect_cycles, longest_path_loc


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


if __name__ == "__main__":
    unittest.main()
