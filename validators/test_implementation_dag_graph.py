"""Hand-derived graph examples for the implementation DAG validator."""
from _test_require import require
from contextlib import redirect_stderr
from io import StringIO
from _literal_path import Path
from tempfile import TemporaryDirectory
import sys
import time
from validate_implementation_dag import detect_cycles, load_toml, longest_path_loc, main, parse_args

def test_distinct_cycles_and_acyclic_nodes() -> None:
    edges = {'A': {'B', 'C'}, 'B': {'C', 'D'}, 'C': {'A'}, 'D': {'B'}, 'E': {'E'}, 'F': {'Z'}, 'G': set()}
    require(detect_cycles(edges) == ['cycle in depends_on: A -> B -> C -> A', 'cycle in depends_on: A -> C -> A', 'cycle in depends_on: B -> D -> B', 'cycle in depends_on: E -> E'])
    require(detect_cycles({'A': {'B'}, 'B': set()}) == [])

def test_longest_weighted_path_and_cycle_rejection() -> None:
    units = {'A': {'estimated_loc': 2}, 'B': {'estimated_loc': 4}, 'C': {'estimated_loc': 3}, 'D': {'estimated_loc': 10}, 'E': {'estimated_loc': 1}}
    edges = {'A': {'B', 'C'}, 'B': {'D'}, 'C': {'D'}, 'D': set(), 'E': set()}
    require(longest_path_loc(units, edges) == 16)
    require(longest_path_loc({}, {}) == 0)
    edges['D'].add('A')
    require(longest_path_loc(units, edges) is None)

def test_cycle_unblocks_waiting_predecessors() -> None:
    edges = {'Z': {'D', 'Z'}, 'D': {'Z', 'U10', 'D', 'B'},
             'U10': {'Z', 'U10', 'D', 'B'}, 'B': {'U10'}}
    require('cycle in depends_on: B -> U10 -> Z -> D -> B' in detect_cycles(edges))

def test_deep_chain_uses_explicit_stacks() -> None:
    length = 2000
    units = {f'U{i}': {'estimated_loc': 1} for i in range(length)}
    edges = {f'U{i}': {f'U{i + 1}'} for i in range(length - 1)}
    edges[f'U{length - 1}'] = set()
    require(detect_cycles(edges) == [])
    require(longest_path_loc(units, edges) == length)

def test_branching_ladder_has_bounded_cycle_search() -> None:
    edges: dict[str, set[str]] = {'A0000': set()}
    previous = 'A0000'
    for index in range(1, 25):
        left = f'N{index:04d}a'
        right = f'N{index:04d}b'
        join = f'C{index:04d}'
        return_node = f'R{index:04d}'
        edges[previous].update((left, right))
        edges[left] = {join}
        edges[right] = {join}
        edges[join] = {return_node}
        edges[return_node] = {previous}
        previous = join
    started = time.perf_counter()
    cycles = detect_cycles(edges)
    require(len(cycles) == 48)
    require(time.perf_counter() - started < 10)

def test_large_single_ring_does_not_rescan_each_node() -> None:
    size = 8000
    nodes = [f'U{index:05d}' for index in range(size)]
    edges = {nodes[index]: {nodes[(index + 1) % size]} for index in range(size)}
    started = time.perf_counter()
    cycles = detect_cycles(edges)
    require(len(cycles) == 1)
    require(cycles[0].count(' -> ') == size)
    require(time.perf_counter() - started < 5)

def test_cli_accepts_exact_options_and_rejects_unknown() -> None:
    original = sys.argv
    try:
        sys.argv = ['validator', '--repo-root', 'repo', '--check-paths-exist', 'file.toml']
        parsed = parse_args()
        require(parsed.dag_file == 'file.toml')
        require(parsed.repo_root == 'repo')
        require(parsed.check_paths_exist)
        for rejected in (['validator', '--unknown', 'file.toml'], ['validator', '--repo-root', '--check-paths-exist', 'file.toml'], ['validator', '--repo-root=', 'file.toml'], ['validator', '--repo-root', '', 'file.toml']):
            sys.argv = rejected
            try:
                parse_args()
            except SystemExit as exc:
                require(exc.code == 2)
            else:
                raise AssertionError('invalid CLI arguments accepted')
    finally:
        sys.argv = original

def test_invalid_utf8_has_stable_byte_evidence() -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / 'invalid.toml'
        path.write_bytes(b'name = "valid\xff"\n')
        try:
            load_toml(path)
        except ValueError as error:
            require('invalid UTF-8' in str(error))
            require('bytes 13:14' in str(error))
        else:
            raise AssertionError('invalid UTF-8 was accepted')
        original = sys.argv
        output = StringIO()
        try:
            sys.argv = ['validator', str(path)]
            with redirect_stderr(output):
                require(main() == 2)
        finally:
            sys.argv = original
        require('invalid UTF-8' in output.getvalue())

if __name__ == '__main__':
    test_distinct_cycles_and_acyclic_nodes()
    test_longest_weighted_path_and_cycle_rejection()
    test_cycle_unblocks_waiting_predecessors()
    test_deep_chain_uses_explicit_stacks()
    test_branching_ladder_has_bounded_cycle_search()
    test_large_single_ring_does_not_rescan_each_node()
    test_cli_accepts_exact_options_and_rejects_unknown()
    test_invalid_utf8_has_stable_byte_evidence()
    print('implementation DAG graph: 8 test groups passed')
