"""Exercise live framed children, protocol refusal, deadlines and ownership."""

import os
import sys
import time

from _owned_session import Session, SessionError
from _test_require import expect_raises, require


def command(program):
    return [sys.executable, '-B', '-S', '-c', program]


def require_closed(session, descriptors):
    require(session.status is not None and not session.descriptors and not session.readers)
    for descriptor in descriptors:
        expect_raises(OSError, lambda: os.fstat(descriptor), 'owned session retained a descriptor')
    expect_raises(ChildProcessError, lambda: os.waitpid(session.pid, os.WNOHANG), 'owned session did not reap its child')


def test_fragmented_frames_and_request_reply():
    program = '''import os
def write(value):
    for byte in len(value).to_bytes(4,'big')+value: os.write(1,bytes([byte]))
def read(size):
    value=b''
    while len(value)<size:
        part=os.read(0,size-len(value))
        if not part: raise RuntimeError('truncated input')
        value+=part
    return value
write(b'first')
size=int.from_bytes(read(4),'big')
value=read(size)
if value!=b'request': raise RuntimeError('wrong request')
write(b'second')
'''
    session = Session(command(program))
    descriptors = tuple(session.descriptors)
    try:
        require(session.frame() == b'first', 'fragmented welcome was not preserved')
        require(session.frame(b'request') == b'second', 'request/reply bytes changed')
    finally:
        session.close()
    require_closed(session, descriptors)


def test_invalid_framing_refuses_success_and_reaps_child():
    session = Session(command("import os;value=b'x'*16;os.write(1,len(value).to_bytes(4,'big')+value)"), frame_limit=16)
    descriptors = tuple(session.descriptors)
    try:
        require(session.frame() == b'x' * 16, 'exact frame boundary was refused')
    finally:
        session.close()
    require_closed(session, descriptors)
    for output, witness in ((b'\0\0\0\0', 'outside its bound'), (b'\0\0\0\x11', 'outside its bound'),
                            (b'\0\0', 'complete reply'), (b'\0\0\0\x05shorter'[:6], 'complete reply')):
        session = Session(command('import os;os.write(1,' + repr(output) + ')'), frame_limit=16)
        descriptors = tuple(session.descriptors)
        try:
            error = expect_raises(SessionError, session.frame, 'invalid reply yielded a successful frame')
            require(witness in str(error), 'invalid frame failed for an unrelated reason')
        finally:
            session.close()
        require_closed(session, descriptors)


def test_deadline_and_diagnostic_overflow_are_bounded():
    for program, witness, timeout in (("import time;time.sleep(5)", 'reply deadline', 0.1),
                                      ("import os;os.write(2,b'PRIVATE_DIAGNOSTIC'*5000)", 'diagnostic output', 2)):
        session = Session(command(program), timeout=timeout)
        descriptors = tuple(session.descriptors)
        try:
            error = expect_raises(SessionError, session.frame, 'failed producer yielded a frame')
            require(witness in str(error) and 'PRIVATE_DIAGNOSTIC' not in str(error))
        finally:
            session.close()
        require_closed(session, descriptors)


def test_exited_leader_does_not_leave_a_pipe_holding_descendant():
    program = '''import os,time
child=os.fork()
if child==0:
    time.sleep(5)
    os._exit(0)
value=str(child).encode()
os.write(1,len(value).to_bytes(4,'big')+value)
os._exit(0)
'''
    session = Session(command(program), timeout=0.1)
    descriptors = tuple(session.descriptors)
    try:
        descendant = int(session.frame())
        error = expect_raises(SessionError, session.frame, 'descendant-held output yielded a reply')
        require('reply deadline' in str(error))
    finally:
        session.close()
    require_closed(session, descriptors)
    deadline = time.monotonic() + 2
    while True:
        try:
            with open('/proc/' + str(descendant) + '/stat', encoding='ascii') as stream:
                # A killed orphan may await the host's reaper; it must not run.
                state = stream.read().rpartition(')')[2].split()[0]
        except (FileNotFoundError, ProcessLookupError):
            state = 'absent'
        if state in ('absent', 'Z', 'X') or time.monotonic() >= deadline:
            break
        time.sleep(0.01)
    require(state in ('absent', 'Z', 'X'), 'owned process group left its descendant running')


def test_launch_failure_and_invalid_contracts_do_not_leak():
    before = set(os.listdir('/proc/self/fd'))
    expect_raises(FileNotFoundError, lambda: Session(['/nonexistent/dagtoml-session-control']),
                  'missing owned executable was accepted')
    require(set(os.listdir('/proc/self/fd')) == before, 'launch failure retained a descriptor')
    for values in ([], ['relative'], [1], [sys.executable, 'bad\0argument']):
        expect_raises(ValueError, lambda: Session(values), 'invalid owned argument vector was accepted')
    for limit in (0, -1, True, None, 128 * 1024 * 1024 + 1):
        expect_raises(ValueError, lambda: Session(command(''), frame_limit=limit), 'invalid frame bound was accepted')
    for timeout in (0, -1, True, None, float('inf'), float('nan'), 121):
        expect_raises(ValueError, lambda: Session(command(''), timeout=timeout), 'invalid session deadline was accepted')


if __name__ == '__main__':
    controls = {name: value for name, value in globals().items() if name.startswith('test_') and callable(value)}
    require(controls)
    executed = set()
    for name, control in sorted(controls.items()):
        control()
        executed.add(name)
    require(executed == set(controls))
    print('owned session: live fragmented/request frames; invalid frames, deadline and diagnostic refusal; leader/descendant cleanup; launch/argument controls; skipped=[]')
