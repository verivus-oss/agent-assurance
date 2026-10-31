"""POSIX Git transport for the credential history reader.

Only explicit argument vectors are executed. File descriptors and child
identity stay owned by this operation; neither a shell nor a text matcher
participates in process dispatch or stream framing.
"""

import os


def git_environment():
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_NO_LAZY_FETCH"] = "1"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return env


def git_binary():
    for directory in os.get_exec_path():
        path = os.path.abspath(os.path.join(directory, "git"))
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise RuntimeError("Git is required to bound credential history")


class GitProcess:
    def __init__(self, root, arguments):
        if os.name != "posix" or not hasattr(os, "posix_spawn"):
            raise RuntimeError("credential history requires the POSIX Git transport")
        binary = git_binary()
        descriptors = []
        self.pid = self.status = self.stdin = self.stdout = None
        try:
            read_input, write_input = os.pipe()
            descriptors.extend((read_input, write_input))
            read_output, write_output = os.pipe()
            descriptors.extend((read_output, write_output))
            with open(os.devnull, "wb") as errors:
                if min(*descriptors, errors.fileno()) < 3:
                    raise RuntimeError("credential Git transport requires open standard file descriptors")
                actions = [(os.POSIX_SPAWN_DUP2, read_input, 0),
                           (os.POSIX_SPAWN_DUP2, write_output, 1),
                           (os.POSIX_SPAWN_DUP2, errors.fileno(), 2)]
                actions.extend((os.POSIX_SPAWN_CLOSE, descriptor) for descriptor in descriptors)
                actions.append((os.POSIX_SPAWN_CLOSE, errors.fileno()))
                self.pid = os.posix_spawn(binary,
                    [binary, "--no-pager", "-C", os.fspath(root), "-c", "core.fsmonitor=false", *arguments],
                    git_environment(), file_actions=actions)
            self.stdin = os.fdopen(write_input, "wb")
            descriptors.remove(write_input)
            self.stdout = os.fdopen(read_output, "rb")
            descriptors.remove(read_output)
        except BaseException:
            self.close(failed=True)
            raise
        finally:
            for descriptor in descriptors:
                os.close(descriptor)

    def wait(self):
        if self.status is None:
            while True:
                try:
                    child, status = os.waitpid(self.pid, 0)
                    break
                except InterruptedError:  # nosec B112 # noqa: S112
                    # Retry a signal-interrupted wait for the same owned child.
                    continue
            if child != self.pid:
                raise RuntimeError("credential transport lost its Git child identity")
            self.status = os.waitstatus_to_exitcode(status)
        return self.status

    def close(self, failed=False):
        try:
            if self.stdin is not None:
                self.stdin.close()
        finally:
            try:
                if self.stdout is not None:
                    self.stdout.close()
            finally:
                if failed and self.pid is not None and self.status is None:
                    try:
                        os.kill(self.pid, 9)
                    except ProcessLookupError:
                        self.wait()
                if self.pid is not None:
                    self.wait()


def git(root, arguments):
    process = GitProcess(root, arguments)
    try:
        process.stdin.close()
        output = process.stdout.read()
        if process.wait():
            raise RuntimeError("Git could not complete credential history operation: " + arguments[0])
        return output
    finally:
        process.close(failed=True)
