# Maintained DuckDB binding build

At project baseline `12cb56dd0a6ce892d51930554080e2411ec35521`, the reference
connector uses the installed native Python binding. Its broader Python import
and packaging dependencies remain inside issue #141's repair scope.

This builder maintains that existing native binding rather than introducing
another FFI implementation. New orchestration is safe Go. It compiles the
prepared supplier's complete binding C++ source population directly against
a core built from the matching pinned amalgamated source. It does not execute
Python packaging, CMake or supplier generators. C++ changes maintain the
existing scanner and ABI inside that dependency; Go owns preparation and build
orchestration.

The input declarations pin SDK archives, published native core source archives and
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

The source-core replacement follows the isolated experiment against project
commit `59889665f89c2a8283b448ab33c56d64d19069e5`. That experiment compared
all 236 enumerated tracked SQL and lexical/operator inputs with the prior
parser, with no differences after repairs. It separately exercised the current
303 independently expected SQL constraint probes plus metadata, initialization,
storage, protocol and replay checks. Its temporary adapter skipped product
artifact admission, the external writer process, connection-boundary tests,
other versions/ABIs and final review. Those observations do not replace the
required current-artifact lanes.

The core recipe preprocesses the pinned source with an explicit environment,
then reads C++ literals, comments and balanced namespace structure. It removes
the complete matcher implementation regions and the generated SQL scanner
namespace. The retained matcher ABI refuses pattern operations before parsing
or execution. SQL matching functions, regular-expression column selectors,
SIMILAR TO and matching-dependent optional HTTP helpers are outside this
reference variant. Ordinary SQL predicates, parameter separation and the
reference catalog/storage contract remain required. Unsupported Unicode escape
conversion remains refused; ordinary UTF-8 literals stay supported.

An explicit byte-state scanner handles comments, identifiers, keywords, strings,
dollar quoting, parameters, numbers and operators. The build compiles the whole
prepared core with the required core-functions and JSON extension source sets,
without generating a scanner. Both pinned sources' compile-time
`DUCKDB_DISABLE_EXTENSION_LOAD` boundary removes external extension loading and
installation while preserving those static extensions. SQL and binding methods
must refuse external loads before opening or downloading extension code. The
floor build at project commit `5c32a84befa67d3828b428f5257a974a7af7dd8a`
exposed an unguarded HTTP implementation after its declarations were disabled.
Source preparation removes the complete HTTP class and response helper and
retains its existing factory with an explicit refusal before a request. The
maintained source already guards that implementation. Both cases are derived
from the full current token population and checked for partial retirement.
The source archive's complete third-party notice
block is retained beside the exact prepared source and static extension hook.
Protocol version two binds those populations, the complete derived core target
set and the built shared library into the native module identity. The connector
refuses missing, altered, linked or extra prepared core source/notice files and
linked artifact parents.

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
The compiler environment also sets `SOURCE_DATE_EPOCH=0`. Both pinned core
archives contain one use each of `__DATE__` and `__TIME__`; the builder rejects
a preprocessed core unless they expand to the fixed epoch values. At candidate
`aa0b471702dd55f26e3d1b4128361ee01086d492`, separate CI jobs for the
maintained engine and both loaders produced three different prepared core
identities because those macros expanded to each job's wall clock. Their
artifact paths collided when the full matrix was assembled, so the aggregate
receipt gate correctly rejected the mixed build. The fixed epoch keeps the
prepared core identity and embedded binding identity consistent across jobs.
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

The compiler, system headers and other verification dependencies retain their
separate audit requirements. Full native matrix validation and cumulative fresh
review of the core and scanner replacements remain required.
Successful binding execution does not establish estate no-regex compliance.
