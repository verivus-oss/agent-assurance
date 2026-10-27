# TOML 1.1 parser source

This directory is based on the pure Python source distribution of Tomli
2.5.0. Its upstream license is in `LICENSE`, and the source files retain
their SPDX notices. The upstream `_re.py` module is omitted. `_scan.py`
replaces its number, date, and time matching with explicit character scans;
`_parser.py` imports those scanners. The package is exposed to the reference
validators through `validators/_toml11.py`.

At commit `6f58c814158c3b1ba46eb49a9b0dec544140ae26`, changes from
upstream are the scanner replacement, its import and call sites in
`_parser.py`, removal of the upstream lazy regex module declaration and the
upstream `doc` and `pos` exception attributes, an
explicit bound in `skip_chars`, binary `load()` conversion of invalid UTF-8
to `TOMLDecodeError`, and remapping of `loads()` CRLF offsets to original byte
spans. The error carries the original source digest and byte span without
line or column coordinates. Keep the parser's TOML 1.1 behavior checked
against the project
fixtures and the Rust and Go primaries. When updating the vendored source,
compare the new upstream source distribution with this directory, carry each
local change forward deliberately, and run the full TOML 1.1 conformance suite.
