# Native PostgreSQL reference sessions

The reference connector at project baseline
`7d871361d4275860dab54b628894a54d20d977e6` loads Psycopg's broader Python
stack. This replacement uses a safe Go PostgreSQL protocol client and an
owned, buffered Python bridge. It is a reference-store interface, not a
general DB-API implementation or a runtime.

Build from this directory with Go 1.26.10:

```sh
go run ./cmd/build-driver --output "$PWD/../../.local/database-ci/postgres-driver/dagtoml-postgres-go"
```

The builder copies the complete source population to a private temporary
directory, verifies pinned modules, and prepares their runtime sources. It
replaces the connection-error redactor with a fixed diagnostic. The password
file parser uses explicit escaped fields, preserves whitespace and literal
escaped wildcard characters, and refuses insecure files. Supplier licenses
remain in the prepared dependency population. The source preparation is a
maintained fork for this binary, not a replacement published under an upstream
package identity.

The builder parses every prepared Go source and checks the complete compiled
package population. Both the driver and builder must exclude `regexp` from
that graph. The build record retains every owned source hash, prepared
dependency hash, package identity and executable digest. The Python bridge
checks the current source, executable and native handshake before sending
connection parameters, then rechecks source and executable identity during
the session. Executed receipts retain that driver identity; the receipt gate
requires the retained native executable and build record.

Connection parameters travel over standard input, never command arguments.
Query values use PostgreSQL's separate parameter protocol. The server's
ReadyForQuery state supplies transaction state. Error results retain SQLSTATE
and the primary message; statement positions, native context and rendered
connection strings are omitted. Close, timeout, malformed framing and partial
replies abandon the owned process group and reap its direct child.

The bridge supports the reference store's text, boolean, integer, floating,
decimal, date, timestamp, binary, JSON and array values. A query has a
30-second server-operation deadline and a 35-second bridge reply deadline.
Frames are limited to 32 MiB, with at most 100,000 buffered rows and a 4 MiB
cell-byte budget including per-cell overhead before JSON escaping. Exceeding
a limit refuses the operation; it does not return partial rows. These limits
are part of this bounded reference interface. Generic driver objects and
implicit DB-API transactions are retired from the PostgreSQL bridge.

The source and dependency checks here cover the prepared client and builder
packages. The Go command's own implementation, the PostgreSQL server,
other drivers and scanners still require their separate estate audits.
Neither a database result nor this component's build record establishes
whole-repository no-regex compliance. Final cumulative validation and fresh
review remain required.
