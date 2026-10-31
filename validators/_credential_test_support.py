"""Owned temporary Git fixtures without file globbing or text matching."""

import os
from _credential_git import GitProcess
from _test_require import require


def write(path, value):
    with open(path, "wb") as output:
        output.write(value)


class TemporaryTree:
    def __enter__(self):
        # Atomic owner-only creation rejects collisions, including symlinks.
        self.path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "credential-test-" + os.urandom(16).hex())  # nosec B108 # noqa: S108
        os.mkdir(self.path, 0o700)
        return self.path

    def __exit__(self, *_error):
        for root, directories, files in os.walk(self.path, topdown=False, followlinks=False):
            for name in files:
                os.unlink(os.path.join(root, name))
            for name in directories:
                path = os.path.join(root, name)
                if os.path.islink(path):
                    os.unlink(path)
                else:
                    os.rmdir(path)
        os.rmdir(self.path)


class Result:
    def __init__(self, status, output):
        self.returncode = status
        self.stdout = output


def command(root, *arguments, allowed=(0,)):
    process = GitProcess(root, list(arguments))
    try:
        process.stdin.close()
        output = process.stdout.read()
        status = process.wait()
        require(status in allowed, "Git fixture operation failed: " + arguments[0])
        return Result(status, output)
    finally:
        process.close(failed=True)


def initialize(root, object_format="sha1"):
    command(root, "init", "-q", "--object-format=" + object_format, "-b", "main")
    command(root, "config", "user.name", "Credential Control")
    command(root, "config", "user.email", "control@example.invalid")


def commit(root, message):
    command(root, "add", "--all")
    command(root, "commit", "-qm", message)
    return command(root, "rev-parse", "HEAD").stdout.strip().decode("ascii")
