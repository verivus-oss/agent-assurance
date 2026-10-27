"""TOML 1.1 parser surface for the Python reference validators.

The vendored Tomli 2.5.0 parser has explicit token scanners in place of its
upstream regular-expression module. It retains the TOML 1.1 behavior needed
for conformance with the Rust and Go validators.
"""

from __future__ import annotations

import io

from _toml11_vendor import TOMLDecodeError, load, loads


def loads_bytes(source: bytes) -> dict:
    """Parse original bytes with the same diagnostic path as binary load."""
    return load(io.BytesIO(source))


__all__ = ["load", "loads", "loads_bytes", "TOMLDecodeError"]
