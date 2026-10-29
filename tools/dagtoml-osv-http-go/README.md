# Bounded advisory archive transport

At baseline `8e64e6851b6ca8230b325c5b83414414d66bc0de`, the native advisory
evaluator delegates archive retrieval to curl. This producer replaces that
transport dependency with a standard-library Go HTTPS client. It retrieves
data; advisory matching remains in the typed Rust evaluator.

The producer admits exactly the three declared complete ecosystem archive
objects. It converts the selected object to a closed identifier before
constructing a request. Redirects, non-HTTPS addresses, user information and
fragments are refused. TLS requires certificate verification and version 1.2
or later. Compression is disabled so evidence identifies the transferred ZIP
bytes. Streams, response headers and metadata have explicit bounds; incomplete
or oversized bodies fail before output. Header values retain duplicates and
must be UTF-8 before JSON encoding. The Rust consumer retains its independent
media, byte-count, generation, entity, freshness and clock checks.
The ten-second connection budget includes pool wait, DNS, TCP, proxies and
TLS. The ninety-second request budget continues after connection; a separate
ten-second response-header limit bounds a connected but silent peer.

The stdout envelope is the archive followed by the existing fixed metadata
footer and a JSON record. A failed command cannot provide an advisory verdict.
`--identity` returns the compiled producer/builder/source-graph identities and
the actual Go version. The consumer must require those identities, the full
current source populations and the executable digest before retrieval, and
check them again before returning its assessment.

Build from the existing native builder module, reusing its owned command
supervisor instead of adding another process implementation:

```sh
GOTOOLCHAIN=go1.26.10 go run ./cmd/build-driver \
  --capsule-source /absolute/repository/tools/dagtoml-osv-http-go \
  --output /absolute/repository/.local/osv-https/dagtoml-osv-http-go
```

The standard-library build mode refuses external module requirements, native
source inputs, unsafe/regex imports and incomplete compiled-package graphs.
It binds complete producer and builder source populations to the executable.
The pinned Go command/compiler remain separate estate audit subjects.

`go run . --self-check` under the pinned toolchain exercises exact byte/header
answers, declared objects, actual local TLS trust, status/redirect/length and
encoding/range refusal, duplicate evidence, invalid header encoding, and real
header/body deadlines. A stalled actual TLS handshake must exhaust the shared
connection budget; an established response may finish after that budget under
the request deadline. It does not claim live advisory evaluation, complete
transport equivalence, dependency compliance or pull-request approval.

CI builds this artifact before scanner execution and explicitly runs the Rust
artifact controls. Complete live archive comparisons, dependency audits and
fresh cumulative review remain required for final signoff.
