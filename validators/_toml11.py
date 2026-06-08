"""TOML 1.1 parser for the Python reference validators and the conformance
runner.

The Python reference MUST parse TOML 1.1 to stay byte-for-byte in lockstep
with the Rust (`toml` 1.1) and Go (BurntSushi/toml v1.6.0) primaries — the
cross-implementation parity invariant (SPEC; contract C01). stdlib `tomllib`
is TOML 1.0 only, so the reference uses `tomli` >= 2.4.0, the 1.1-capable
upstream of `tomllib` (PEP 680, same author; see requirements/toml.txt).

This module exposes the `tomllib`-compatible surface (`load`, `loads`,
`TOMLDecodeError`) so call sites read `import _toml11 as tomllib`. It does NOT
fall back to stdlib `tomllib` if `tomli` is missing, and it FAILS LOUD if the
installed `tomli` predates 1.1 support: a silent fall back to TOML 1.0 would
reintroduce exactly the cross-implementation divergence this migration
removes (the project's "invalidations must propagate visibly" posture).
"""

from __future__ import annotations

from importlib import metadata

try:
    import tomli as _tomli
except ModuleNotFoundError as exc:  # no silent stdlib (TOML 1.0) fallback
    raise ModuleNotFoundError(
        "the TOML 1.1 Python reference requires `tomli` >= 2.4.0 "
        "(`pip install --no-binary tomli -r requirements/toml.txt`); "
        "stdlib tomllib is TOML 1.0 only and would break cross-implementation "
        "parity"
    ) from exc

_RAW_VERSION = metadata.version("tomli")
_VERSION = tuple(int(part) for part in _RAW_VERSION.split(".")[:2])
if _VERSION < (2, 4):
    raise ImportError(
        f"tomli >= 2.4.0 required for TOML 1.1 parsing; found {_RAW_VERSION}. "
        "tomli < 2.4.0 is TOML 1.0 only and would silently diverge from the "
        "Rust/Go primaries — see requirements/toml.txt"
    )

# `tomllib`-compatible surface.
load = _tomli.load
loads = _tomli.loads
TOMLDecodeError = _tomli.TOMLDecodeError

__all__ = ["load", "loads", "TOMLDecodeError"]
