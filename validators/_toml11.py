"""TOML 1.1 parser surface for the Python reference validators.

The vendored Tomli 2.5.0 parser has explicit token scanners in place of its
upstream regular-expression module. It retains the TOML 1.1 behavior needed
for conformance with the Rust and Go validators.
"""

from __future__ import annotations

from _toml11_vendor import TOMLDecodeError, load, loads

__all__ = ["load", "loads", "TOMLDecodeError"]
