# Shared JSON codec

The codec replaces the guarded standard JSON wrapper present at project commit
`16d7d85f31a3071d56f4f8c34d99d1800ad5ce73`. Current entry points include
database metadata projection and integrity checks, ingest/replay reports,
OSV result verification, symbol reports and validation receipts. The database
shim re-exports the same `loads`, `dumps` and `dump` functions.

`loads` first normalizes text/byte subclasses to their built-in source buffers.
An explicit container state machine then validates the complete value,
including object keys and separators, arrays, quoted escapes and ASCII number
syntax. Only that validated interval reaches CPython's native `_json` scanner.
This avoids the scanner's malformed-input path, which imports the standard
decoder. A different native consumption interval is an instrument failure.
No Python parser fallback is selected.

Malformed syntax and UTF-8 use the original source SHA256 and byte span.
Parser line and column coordinates are not returned. A zero-width span can
identify a missing operand at the end of the source. Source bytes decode as
UTF-8; byte order marks do not add an alternate input encoding.

The decoder retains the configured integer, decimal, constant, object and
object-pair hooks. Duplicate keys keep the native default last-value behavior;
metadata integrity supplies its own duplicate-key rejection hook. The exact
native nonfinite constants remain accepted by default, while metadata supplies
its existing rejection hook. Native depth and numeric conversion failures
propagate. Hook functions are trusted program configuration, not expressions
read from JSON input.

`dumps` and `dump` use the compiled native encoder and native string escaping.
An explicit quote/escape/depth walker renders indentation from compact native
output, including on Python 3.11. Current output options are `ensure_ascii`,
`check_circular`, `allow_nan`, `sort_keys`, `skipkeys`, `indent`, `separators`
and `default`. Custom encoder classes and unknown options are unsupported.
Circular-reference, unsupported-value and output-stream failures propagate.
`dump` finishes encoding before writing to its stream.

Native scanner, encoder and string-encoder substitutions fail rather than
choosing a fallback. Fresh `-S` controls exercise the complete declared JSON
component population in normal and optimized Python. They reject standard
JSON and regex imports, and observe Python matcher calls. A separate source
control derives every tracked Python file and checks direct import structure;
it is not a claim about arbitrary dynamic imports or other dependencies.

Independent controls cover declared values, grammar failures, Unicode and
escapes, original byte identities, hooks, source subclasses, output formatting,
circular references and unavailable primitives. Prior-engine comparison data
is separate from those expected answers. Its agreement does not prove grammar
equivalence for arbitrary inputs. Native C internals, external hooks and other
reference-store imports are outside the cold-process instrument's scope.
The remaining reference-store and verification-tool dependency audits still
block a cumulative policy approval.
