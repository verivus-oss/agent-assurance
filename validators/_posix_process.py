"""Owned bounded child processes for POSIX verification commands.

The transport retains the stream and cleanup implementation measured in
`test_cold_guard_integrity.run` at project commit
`a867058bc03a98c9b1a478543b690f046fe25a7d`.
"""

import os
import select
import time

from _test_require import require


def run(command, *, output_limit=16 * 1024 * 1024, timeout=120):
    """Own the child and both streams without a pattern-importing wrapper."""
    require(os.name == 'posix' and hasattr(os, 'posix_spawn'), 'process transport requires POSIX child controls')
    require(type(output_limit) is int and output_limit > 0, 'process output bound must be a positive integer')
    require(type(timeout) in (int, float) and 0 < timeout <= 120, 'process deadline must be positive and at most 120 seconds')
    descriptors = []
    pid = status = None
    streams = {}
    try:
        out_read, out_write = os.pipe()
        descriptors.extend((out_read, out_write))
        err_read, err_write = os.pipe()
        descriptors.extend((err_read, err_write))
        empty = os.open(os.devnull, os.O_RDONLY)
        descriptors.append(empty)
        require(min(descriptors) >= 3)
        actions = [(os.POSIX_SPAWN_DUP2, empty, 0), (os.POSIX_SPAWN_DUP2, out_write, 1),
                   (os.POSIX_SPAWN_DUP2, err_write, 2)]
        actions.extend((os.POSIX_SPAWN_CLOSE, descriptor) for descriptor in descriptors)
        pid = os.posix_spawn(command[0], command, dict(os.environ), file_actions=actions)
        for descriptor in (out_write, err_write, empty):
            os.close(descriptor)
            descriptors.remove(descriptor)
        pending = {out_read, err_read}
        streams = {out_read: bytearray(), err_read: bytearray()}
        deadline = time.monotonic() + timeout
        while pending or status is None:
            require(time.monotonic() < deadline, 'child did not complete before its deadline')
            ready, _, _ = select.select(sorted(pending), [], [], 0.1)
            for descriptor in ready:
                chunk = os.read(descriptor, 65536)
                if chunk:
                    streams[descriptor].extend(chunk)
                    require(len(streams[descriptor]) <= output_limit, 'child output exceeded its declared bound')
                else:
                    pending.remove(descriptor)
            if status is None:
                child, result = os.waitpid(pid, os.WNOHANG)
                if child:
                    require(child == pid)
                    status = result
        return os.waitstatus_to_exitcode(status), bytes(streams[out_read]), bytes(streams[err_read])
    finally:
        try:
            if pid is not None and status is None:
                try:
                    os.kill(pid, 9)
                except ProcessLookupError:
                    child, status = os.waitpid(pid, 0)
                    require(child == pid, 'process cleanup lost its owned child')
                if status is None:
                    child, status = os.waitpid(pid, 0)
                    require(child == pid, 'process cleanup reaped the wrong child')
        finally:
            for descriptor in descriptors:
                os.close(descriptor)
