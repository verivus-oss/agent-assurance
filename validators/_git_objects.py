"""Framed Git object identities and an owned raw-blob reader."""

import hashlib

from _credential_git import GitProcess


def object_id(value):
    return len(value) in (40, 64) and not value.translate(None, b"0123456789abcdef")


class BlobReader:
    def __init__(self, root):
        self.process = GitProcess(root, ["cat-file", "--batch"])

    def __enter__(self):
        return self

    def __exit__(self, error_type, *_error):
        self.process.close(failed=error_type is not None)
        if error_type is None and self.process.status:
            raise RuntimeError("Git object reader did not exit successfully")

    def read(self, sha):
        if not object_id(sha):
            raise RuntimeError("invalid requested Git blob identity")
        self.process.stdin.write(sha + b"\n")
        self.process.stdin.flush()
        header = self.process.stdout.readline().removesuffix(b"\n").split(b" ")
        if len(header) != 3 or header[0] != sha or header[1] != b"blob" or not header[2].isdigit():
            raise RuntimeError("Git object reader did not return the requested blob")
        size = int(header[2])
        content = self.process.stdout.read(size)
        if len(content) != size or self.process.stdout.read(1) != b"\n":
            raise RuntimeError("Git object reader returned truncated blob bytes")
        framed = b"blob " + str(size).encode("ascii") + b"\0" + content
        digest = (hashlib.sha1(framed, usedforsecurity=False).hexdigest() if len(sha) == 40
                  else hashlib.sha256(framed).hexdigest())
        if digest.encode("ascii") != sha:
            raise RuntimeError("Git object bytes do not match the requested content identity")
        return content
