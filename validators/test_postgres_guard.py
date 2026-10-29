"""Current guard installation and swallowed-attempt controls without regex execution."""

import sys
import threading

import _literal_ast as ast
from _literal_path import Path
from _postgres_guard import Boundary, BoundaryError, FORBIDDEN, expected_proof
from _test_require import expect_raises, require


def test_guard_contract_matches_current_reference_control():
    path = Path(__file__).with_name('test_reference_store_cold_start.py')
    tree = ast.parse(path.read_text())
    values = [node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == 'retired' for target in node.targets)]
    require(len(values) == 1 and ast.literal_eval(values[0]) == set(FORBIDDEN),
            'PostgreSQL runtime and reference cold contracts differ')


def test_clean_guard_profiles_main_and_new_threads():
    before = sys.getprofile(), threading.getprofile()
    profiles = []
    with Boundary() as boundary:
        worker = threading.Thread(target=lambda: profiles.append(sys.getprofile()))
        worker.start()
        worker.join(timeout=2)
        require(not worker.is_alive() and profiles == [boundary.profile], 'worker did not inherit the actual guard')
        require(boundary.proof() == expected_proof())
    require((sys.getprofile(), threading.getprofile()) == before, 'guard did not restore its caller profiles')


def test_swallowed_import_attempt_still_invalidates_proof():
    with Boundary() as boundary:
        error = expect_raises(BoundaryError, lambda: __import__('re'), 'forbidden import was admitted')
        require('forbidden import' in str(error) and boundary.attempted == {'re'})
        expect_raises(BoundaryError, boundary.proof, 'swallowed import attempt yielded a successful proof')
    with Boundary() as fresh:
        require(fresh.proof() == expected_proof(), 'retired audit callback damaged a fresh boundary')


def test_pattern_symbol_model_and_dropped_profiles_refuse_proof():
    class Pattern:
        pass

    class Call:
        __self__ = Pattern()
        __name__ = 'match'

    with Boundary() as boundary:
        # Model the profile event; do not compile or execute a regex.
        expect_raises(BoundaryError, lambda: boundary.profile(None, 'c_call', Call()), 'pattern symbol was ignored')
        require(boundary.patterns == {'match'})
        expect_raises(BoundaryError, boundary.proof, 'matching attempt yielded a successful proof')
    with Boundary() as boundary:
        threading.setprofile(None)
        expect_raises(BoundaryError, boundary.proof, 'dropped worker profile yielded a successful proof')


if __name__ == '__main__':
    if not sys.flags.no_site:
        from _posix_process import run
        code, output, errors = run([sys.executable, '-B', '-S', str(Path(__file__).resolve())])
        require(code == 0 and not errors, 'isolated PostgreSQL guard controls failed: ' + errors.decode())
        require(b'PostgreSQL guard:' in output, 'isolated PostgreSQL guard controls did not execute')
        print(output.decode(), end='')
        raise SystemExit(0)
    controls = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(controls)
    executed = set()
    for name, control in sorted(controls.items()):
        control()
        executed.add(name)
    require(executed == set(controls))
    print('PostgreSQL guard: current root contract, actual main/worker installation, swallowed import, modelled C-symbol and dropped-profile refusal; live lanes and native audits skipped')
