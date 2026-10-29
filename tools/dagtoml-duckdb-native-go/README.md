# Maintained DuckDB binding build

At project baseline `12cb56dd0a6ce892d51930554080e2411ec35521`, the reference
connector uses the installed native Python binding. Its broader Python import
and packaging dependencies remain inside issue #141's repair scope.

This builder maintains that existing native binding rather than introducing
another FFI implementation. New orchestration is safe Go. It compiles the
prepared supplier's complete binding C++ source population directly against
the matching pinned native core. It does not execute Python packaging,
CMake, supplier generators, or a new implementation of DuckDB's SQL engine.

The input declarations pin SDK archives, published native core archives and
the Pybind11 header wheel. Source preparation applies the captured full-file
before/after identities and literal edits, and retires three unused generated
Python import-cache headers. UUID results use canonical engine text and
timestamp-with-time-zone results use aware UTC values. General Python UUID
objects and named-zone presentation are outside this reference variant.
The value classifier admits native primitive and container values before
standard date/decimal types. Pandas, NumPy and custom DuckDB value lookups
are retired from that conversion path. The reference connector must reject
unsupported Python objects before invoking it. Native exception translation
uses the primary message instead of rendered query-coordinate context.
Supplier license and notice files accompany the published native artifacts.

Build from this module with the selected ordinary CPython installation and
its development headers:

```sh
GOTOOLCHAIN=go1.26.10 go run . --version 1.5.3 \
  --python /absolute/path/to/python \
  --cache /absolute/path/to/archive-cache \
  --output /absolute/path/to/native-client
```

Current targets are Linux amd64 and CPython 3.11 through 3.13. Other platforms
and ABI variants fail before compilation. The output must be outside this
module. A C++ compiler is required for the existing native dependency.

The native module carries the prepared input identity. Retained records
include owned recipe hashes, prepared SDK and Python/Pybind11 header hashes,
compiler and native core identities, and the derived compiled source set.
Header and core populations are compared again after compilation. Commands use
an explicit minimal environment, so caller include/library/import overrides do
not change the declared build. The process control observes that environment
in an actual child while a hostile compiler include path is set in its caller.
Compiler processes have bounded streams and deadlines. Cleanup abandons their
owned process group before reaping the direct child. Failed command records
retain exact arguments, directory and raw base64 output; their diagnostic
coordinates stay tool transcripts.

Completion requires both closed streams and a terminal direct process, observed
without reaping its reserved PID. The supervisor at baseline
`48fbde757f63bf4e6aa7c889cee54b67e3e25c26` stopped a finite producer that
closed its output descriptors before a final write. The current real-child
control requires that write and a successful exit, alongside deadline and
descendant cleanup refusals. These Linux builders require the kernel's process
state interface under `/proc`.

The reference connector requires this build's embedded identity, complete input
populations, supplier notices and exact loaded native core. It buffers results
within the existing reference cursor surface and rejects unsupported objects
before native conversion. Database lane receipts require both the artifact
identity and an intact cold import guard, including new worker threads.

Run `go run . --self-check` under the pinned toolchain for the current archive
and process controls. Archive refusals must carry their intended reason; a
setup error does not count as rejection evidence. Actual binding execution and
complete database lanes run separately and remain required before approval.

The native core, generated SQL scanner, compiler, system headers and
other verification dependencies retain their separate audit requirements.
Successful binding execution does not establish estate no-regex compliance.
