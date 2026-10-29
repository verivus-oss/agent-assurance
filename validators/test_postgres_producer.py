"""Exercise the real native producer's framing and request admission."""

import os
import sys
import time

from _literal_path import Path
from _literal_json import dumps, loads
from _owned_session import Session, SessionError
from _posix_process import run
from _temporary_attribute import temporary_attribute
from _test_require import expect_raises, require

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reference/database'))
from _postgres_client import build_identity  # noqa: E402
from _postgres_client import NativeConnection, OperationalError  # noqa: E402


def prepare():
    go = next((os.path.join(directory, 'go') for directory in os.get_exec_path()
               if os.path.isabs(directory) and os.access(os.path.join(directory, 'go'), os.X_OK)), None)
    require(go, 'native producer controls require the pinned Go toolchain')
    before = os.getcwd()
    try:
        os.chdir(ROOT / 'tools/dagtoml-postgres-go')
        with temporary_attribute(os, 'environ', {**os.environ, 'GOTOOLCHAIN': 'go1.26.10'}):
            code, output, errors = run([go, 'run', './cmd/build-driver', '--output',
                                        str(ROOT / '.local/database-ci/postgres-driver/dagtoml-postgres-go')])
        require(code == 0 and not errors and b'prepared native PostgreSQL driver' in output,
                'native producer subject did not build and execute its supplier controls: ' + errors.decode())
    finally:
        os.chdir(before)
    return build_identity(ROOT)


def start(identity):
    session = Session([str(ROOT / identity['binary'])])
    try:
        welcome = loads(session.frame())
        require(welcome['protocol'] == identity['protocol'] and welcome['request_id'] == 0 and welcome['success'])
        require(welcome['source_sha256'] == identity['source_sha256']
                and welcome['dependencies_sha256'] == identity['dependencies_sha256']
                and welcome['compiled_graph_sha256'] == identity['compiled_graph_sha256']
                and welcome['go_version'] == identity['go_version'], 'native producer subject is stale')
        return session
    except BaseException:
        session.close()
        raise


def test_real_producer_accepts_valid_frames_and_ordered_close(identity):
    session = start(identity)
    try:
        # The protocol accepts these Unicode scalars. With no database session,
        # execution returns a structured operation failure rather than losing
        # framing or replacing malformed input.
        for number, sql in enumerate(('Unicode ü', 'astral 😀'), 1):
            response = loads(session.frame(dumps({'request_id': number, 'operation': 'execute', 'sql': sql}).encode()))
            require(response['request_id'] == number and not response['success'] and response['closed'])
        response = loads(session.frame(b'{"request_id":3,"operation":"close"}'))
        require(response['request_id'] == 3 and response['success'] and response['closed'])
        deadline = time.monotonic() + 2
        while os.waitid(os.P_PID, session.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            require(time.monotonic() < deadline, 'successful native producer did not exit after close')
            time.sleep(0.01)
    finally:
        session.close()
    require(session.status == 0, 'successful native producer did not exit cleanly')


def test_real_producer_refuses_ambiguous_or_invalid_requests(identity):
    cases = (
        b'null', b'[]', b'{',
        b'{"request_id":1,"operation":"close","operation":"execute"}',
        b'{"request_id":1,"operation":"close","unknown":true}',
        b'{"request_id":1,"operation":"close","sql":"unused"}',
        b'{"request_id":true,"operation":"close"}',
        b'{"request_id":0,"operation":"close"}',
        b'{"request_id":2,"operation":"close"}',
        b'{"request_id":1,"Operation":"close"}',
        b'{"request_id":1,"operation":"execute"}',
        b'{"request_id":1,"operation":"execute","sql":"bad\xed\xa0\x80"}',
        b'{"request_id":1,"operation":"execute","sql":"bad\\ud800"}',
        b'{"request_id":1,"operation":"execute","sql":"bad\\udc00"}',
        b'{"request_id":1,"operation":"execute","sql":null}',
        b'{"request_id":1,"operation":"close"}true',
    )
    for data in cases:
        session = start(identity)
        try:
            error = expect_raises(SessionError, lambda: session.frame(data),
                                  'invalid native request yielded a complete response')
            require('complete reply' in str(error), 'invalid request failed for an unrelated reason')
        finally:
            session.close()
        require(session.status is not None and session.status != 0, 'invalid request yielded a successful native exit')


def test_real_producer_frame_boundary(identity):
    limit = 32 * 1024 * 1024
    session = start(identity)
    try:
        packet = b'{"request_id":1,"operation":"close"}'
        packet += b' ' * (limit - len(packet))
        require(len(packet) == limit)
        response = loads(session.frame(packet))
        require(response['success'] and response['request_id'] == 1 and response['closed'],
                'native producer refused the documented exact frame boundary')
    finally:
        session.close()
    for size in (0, limit + 1):
        session = start(identity)
        try:
            require(os.write(session.input, size.to_bytes(4, 'big')) == 4)
            error = expect_raises(SessionError, session.frame, 'invalid header yielded a native response')
            require('complete reply' in str(error), 'invalid native header did not refuse before body allocation')
        finally:
            session.close()


def test_retained_inventory_and_native_handshake_refuse_altered_proof(identity):
    path = ROOT / (identity['binary'] + '.build.json')
    original = path.read_bytes()
    try:
        record = loads(original)
        del record['compiled_packages']['context']
        path.write_text(dumps(record))
        error = expect_raises(OperationalError, lambda: build_identity(ROOT),
                              'incomplete compiled inventory was accepted')
        require('stale or incomplete' in str(error), 'inventory control failed during unrelated setup')
        record = loads(original)
        require(len(record['prepared_dependencies']) > 1, 'prepared dependency subject is absent')
        record['prepared_dependencies'] = record['prepared_dependencies'][:1]
        path.write_text(dumps(record))
        error = expect_raises(OperationalError, lambda: build_identity(ROOT),
                              'incomplete prepared dependency inventory was accepted')
        require('stale or incomplete' in str(error), 'dependency omission failed during unrelated setup')
        record = loads(original)
        record['prepared_dependencies'].append(record['prepared_dependencies'][0])
        path.write_text(dumps(record))
        error = expect_raises(OperationalError, lambda: build_identity(ROOT),
                              'duplicate prepared dependency identity was accepted')
        require('malformed or repeated' in str(error), 'duplicate dependency failed during unrelated setup')
        # Even a supplied identity claiming the original native executable
        # must agree with the executable's own hello before credentials flow.
        altered = {**identity, 'compiled_graph_sha256': '0' * 64}
        path.write_bytes(original)
        import _postgres_client
        with temporary_attribute(_postgres_client, 'build_identity', lambda _root: altered):
            error = expect_raises(OperationalError, lambda: NativeConnection('invalid destination'),
                                  'native handshake accepted an unrelated graph identity')
        require('handshake differs' in str(error), 'identity control reached destination parsing')
    finally:
        path.write_bytes(original)
    require(build_identity(ROOT) == identity, 'native proof control did not restore its subject')
    binary = ROOT / identity['binary']
    executable = binary.read_bytes()
    try:
        binary.write_bytes(b'invalid replacement')
        error = expect_raises(OperationalError, lambda: build_identity(ROOT),
                              'replaced native executable was accepted')
        require('binary differs' in str(error), 'binary control failed for an unrelated reason')
    finally:
        binary.write_bytes(executable)
    require(build_identity(ROOT) == identity, 'binary control did not restore its subject')


if __name__ == '__main__':
    identity = prepare()
    controls = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(controls)
    executed = set()
    for name, control in sorted(controls.items()):
        control(identity)
        executed.add(name)
    require(executed == set(controls))
    print('native PostgreSQL producer: current rebuilt subject and supplier controls; valid Unicode/request/close controls; malformed, duplicate, out-of-order and invalid Unicode refusal; altered inventory, handshake and executable refusal; live database lanes skipped')
