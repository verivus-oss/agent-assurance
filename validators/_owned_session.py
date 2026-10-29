"""One owned POSIX child with bounded, length-framed request/reply IO."""

import os
import select
import time


class SessionError(RuntimeError):
    pass


class Session:
    def __init__(self, command, *, frame_limit=32 * 1024 * 1024, timeout=35):
        if (os.name != 'posix' or type(command) not in (list, tuple) or not command
                or not all(type(value) is str and '\0' not in value for value in command)
                or not os.path.isabs(command[0])):
            raise ValueError('owned session requires an absolute POSIX argument vector')
        if type(frame_limit) is not int or not 0 < frame_limit <= 128 * 1024 * 1024:
            raise ValueError('owned session frame limit is unsupported')
        if type(timeout) not in (int, float) or not 0 < timeout <= 120:
            raise ValueError('owned session timeout is unsupported')
        self.pid = self.status = None
        self.descriptors = []
        self.pending = bytearray()
        self.errors = bytearray()
        self.frame_limit, self.timeout = frame_limit, timeout
        self.readers = set()
        try:
            child_in, self.input = os.pipe()
            self.descriptors.extend((child_in, self.input))
            self.output, child_out = os.pipe()
            self.descriptors.extend((self.output, child_out))
            self.error, child_error = os.pipe()
            self.descriptors.extend((self.error, child_error))
            if min(self.descriptors) < 3:
                raise SessionError('owned session requires open standard streams')
            actions = [(os.POSIX_SPAWN_DUP2, child_in, 0), (os.POSIX_SPAWN_DUP2, child_out, 1),
                       (os.POSIX_SPAWN_DUP2, child_error, 2)]
            actions.extend((os.POSIX_SPAWN_CLOSE, descriptor) for descriptor in self.descriptors)
            self.pid = os.posix_spawn(command[0], command, dict(os.environ), file_actions=actions, setpgroup=0)
            for descriptor in (child_in, child_out, child_error):
                os.close(descriptor)
                self.descriptors.remove(descriptor)
            for descriptor in self.descriptors:
                os.set_blocking(descriptor, False)
            self.readers = {self.output, self.error}
        except BaseException:
            self.close()
            raise

    def frame(self, data=None):
        """Read one reply, optionally after sending exactly one request."""
        if self.pid is None or self.status is not None:
            raise SessionError('owned session is closed')
        if data is not None and (type(data) is not bytes or not 0 < len(data) <= self.frame_limit):
            raise ValueError('owned request frame is outside its bound')
        outgoing = (len(data).to_bytes(4, 'big') + data) if data is not None else b''
        position = 0
        deadline = time.monotonic() + self.timeout
        try:
            while True:
                if len(self.pending) >= 4:
                    length = int.from_bytes(self.pending[:4], 'big')
                    if not 0 < length <= self.frame_limit:
                        raise SessionError('owned reply frame is outside its bound')
                    if len(self.pending) >= length + 4:
                        if position != len(outgoing):
                            raise SessionError('owned child replied before receiving its request')
                        result = bytes(self.pending[4:length + 4])
                        del self.pending[:length + 4]
                        if self.pending:
                            raise SessionError('owned child sent an unsolicited reply')
                        return result
                if self.output not in self.readers:
                    raise SessionError('owned child ended before a complete reply')
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise SessionError('owned child exceeded its reply deadline')
                readable, writable, _ = select.select(
                    sorted(self.readers), [self.input] if position < len(outgoing) else [], [], min(remaining, 0.1))
                for descriptor in readable:
                    try:
                        chunk = os.read(descriptor, 65536)
                    except BlockingIOError:  # nosec B112 # noqa: S112
                        # Readiness can race; retry this nonblocking descriptor.
                        continue
                    if not chunk:
                        self.readers.remove(descriptor)
                    elif descriptor == self.output:
                        self.pending.extend(chunk)
                        if len(self.pending) > self.frame_limit + 4:
                            raise SessionError('owned reply output exceeded its bound')
                    else:
                        self.errors.extend(chunk)
                        if len(self.errors) > 65536:
                            raise SessionError('owned diagnostic output exceeded its bound')
                if writable:
                    try:
                        position += os.write(self.input, outgoing[position:position + 65536])
                    except BlockingIOError:  # nosec B112 # noqa: S112
                        # Retry the same unconsumed request bytes after readiness.
                        continue
        except BaseException:
            self.close()
            raise

    def close(self):
        try:
            if self.pid is not None and self.status is None:
                try:
                    os.killpg(self.pid, 9)
                except ProcessLookupError:
                    # The owned group has ended; waitpid still reaps its child.
                    self.readers.clear()
                while True:
                    try:
                        child, result = os.waitpid(self.pid, 0)
                        break
                    except InterruptedError:  # nosec B112 # noqa: S112
                        # Retry a signal-interrupted wait for the same child.
                        continue
                if child != self.pid:
                    raise SessionError('owned session reaped a different child')
                self.status = os.waitstatus_to_exitcode(result)
        finally:
            while self.descriptors:
                os.close(self.descriptors.pop())
            self.readers.clear()
