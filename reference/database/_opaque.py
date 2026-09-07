"""Opaque SQL artifact identity. This API never returns source text or bytes."""

import hashlib


def opaque_sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()
