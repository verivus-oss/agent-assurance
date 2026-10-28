# Owned filesystem primitives

Current filesystem consumers from project commit
`4df544e0727fd881531b3b2fad716c36468bd996` use `_literal_path.py` for lexical
paths and native file operations. Their earlier standard Pathlib imports
loaded matcher dependencies before document loading. The current discovery
interface remains the explicit bounded `_literal_paths` enumerator.

The owned implementation is adapted from CPython 3.11.15, `Lib/pathlib.py`.
[Supplier provenance](../vendor-provenance/path-primitives.toml) records the
upstream commit, source blob and retained license identity. These belong to
the upstream repository, separately from this project's commit citations.
The supplier source SHA256 is
`3b21ac188fd9ac20bacc8ccd976fabd5d8ccf5000f8e157d3dfff005b228fb3d`.
The [CPython license](licenses/CPython-LICENSE.txt) is retained. Pattern
selectors, `glob`, `rglob`, `match`, URI APIs, deprecated context-manager
methods, the deprecated `link_to` alias and the unused `touch` method are
removed with their unused matcher, URL, caching, warning and flavour-module
imports. This is an owned primitive subset,
not a replacement for every standard-library Pathlib API.

Lexical joins preserve parent traversal segments. Explicit resolution follows
real symlinks before consuming parent segments; containment checks compare
the resolved result with the trusted root. File operations use native `os`
and `io` primitives, including their missing-file, type and permission errors.
Current standalone commands bootstrap their shared implementation through
literal `os.path` operations. No standard Pathlib module is injected or loaded
as a fallback.

POSIX lexical controls and native file controls run on the Linux validation
host. Windows pure paths retain the pinned supplier's lexical contract.
Python 3.13 interprets the malformed Windows operand `///a/b` differently;
the owned implementation deliberately follows the pinned 3.11 behavior.
Native Windows filesystem execution is outside the local instrument's scope.
Supplier agreement on declared observations is separate from independent
golden expectations and is not universal cross-version equivalence.

The cold component controls derive and execute every declared test function.
They reject standard Pathlib, regex, glob, filename-matcher and URL imports,
retain every attempted import even if its exception is caught, and observe
Python matcher calls. They cover lexical roots, parent slices,
name/suffix changes, symlink loops and escapes, strict missing resolution,
binary/text writes, file types, rename/deletion and the current explicit
discovery interface. Native OS internals and unrelated dependencies are not
instrumented by that component.

The reference-store cold control separately executes SQLite schema/seed
loading, exclusive initialization, every supported document kind,
idempotency, invalid document and SQL outcomes, and stored-document audit.
It does not replace the persistent connection-loss/concurrency suites or the
pinned PostgreSQL and DuckDB lanes.

Current random row and workspace identifiers use sixteen OS-random bytes
with explicit version-four and RFC variant bits. Only compact hexadecimal
and hyphenated text are supplied. Standard UUID parsing, platform discovery
and the broader UUID framework are retired at those authored consumers.
Every byte-fill value has independent bit-preservation controls; absent,
wrong-sized or failed entropy produces an error. The exact-option parser
also uses built-in object annotations and `collections.abc.Callable`, without
an active runtime import of the typing framework. Other dependency and
verification consumers remain inside the wider audit.
