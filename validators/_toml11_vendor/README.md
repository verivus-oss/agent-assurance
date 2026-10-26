# TOML 1.1 parser source

This directory is based on the pure Python source distribution of Tomli
2.5.0. Its upstream license is in `LICENSE`, and the source files retain
their SPDX notices. The upstream `_re.py` module is omitted. `_scan.py`
replaces its number, date, and time matching with explicit character scans;
`_parser.py` imports those scanners. The package is exposed to the reference
validators through `validators/_toml11.py`.

Changes from upstream are limited to the scanner replacement, its import and
call sites in `_parser.py`, removal of the upstream lazy regex module
declaration, and a `TOMLDecodeError` that exposes a source digest and byte span
without line or column coordinates. Keep the parser's TOML 1.1 behavior
checked against the project fixtures and the Rust and Go primaries.
