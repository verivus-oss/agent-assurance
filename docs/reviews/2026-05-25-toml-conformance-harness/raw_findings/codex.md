# Independent review: toml-test parser-conformance harness

Reviewer: codex
Commit under review: afe354c
Range reviewed: 8cc1110..afe354c

## Method

I inspected the changed bytes in the repository rather than relying on the bundle summary. I read:

- docs/reviews/2026-05-25-toml-conformance-harness/review_bundle.toml
- docs/reviews/2026-05-25-toml-conformance-harness/review_prompt.md
- tools/review-request-dag.toml
- Makefile
- .github/workflows/validate.yml
- CHANGELOG.md
- tools/dagtoml-validate-go/go.mod

I also exposed sqry and attempted semantic lookup first, per the review workflow. The existing sqry graph failed its snapshot integrity check, so I rebuilt it successfully and then searched for "toml"; the indexed symbol results were not material to this Makefile/YAML/Markdown-only change, so the decisive evidence below is from line-numbered byte inspection and executed commands.

## Command evidence

Changed files:

```text
$ git diff --name-only 8cc1110..afe354c
.github/workflows/validate.yml
CHANGELOG.md
Makefile
```

Commit stat:

```text
$ git show --stat --oneline --decorate --no-renames afe354c
afe354c (HEAD -> main) Wire toml-test parser-conformance harness into CI
 .github/workflows/validate.yml | 15 ++++++++++
 CHANGELOG.md                   | 20 ++++++++++++++
 Makefile                       | 63 ++++++++++++++++++++++++++++++++++++++++++
 3 files changed, 98 insertions(+)
```

Requested reproduction command:

```text
$ make toml-conformance-install && make toml-conformance
GOBIN=/home/werner/go/bin go install github.com/toml-lang/toml-test/cmd/toml-test@v1.6.0
go: github.com/toml-lang/toml-test/cmd/toml-test@v1.6.0: github.com/toml-lang/toml-test/cmd/toml-test@v1.6.0: Get "https://proxy.golang.org/github.com/toml-lang/toml-test/cmd/toml-test/@v/v1.6.0.info": dial tcp: lookup proxy.golang.org on 192.168.1.1:53: dial udp 192.168.1.1:53: socket: operation not permitted
make: *** [Makefile:57: toml-conformance-install] Error 1
```

Exit status: 2. This is an environment/network denial during `go install`, not a repository-byte failure. The Makefile-resolved binaries already existed locally, so I inspected their module versions and ran the suite.

Installed binary module evidence:

```text
$ go version -m /home/werner/go/bin/toml-test
/home/werner/go/bin/toml-test: go1.26.3
	path	github.com/toml-lang/toml-test/cmd/toml-test
	mod	github.com/toml-lang/toml-test	v1.6.0	h1:lZ9cKL1MmS9iXA8O8pjYSPg8F4afigKluaxxxjQkRJ8=
	dep	github.com/BurntSushi/toml	v1.5.1-0.20250415140922-f225e861e346	h1:DGlXHETPSm50+URDRnTkJqHRR3nRkAoyBTVn9zKUgoc=
	dep	github.com/rivo/uniseg	v0.4.7	h1:WUdvkW8uEhrYfLC4ZzdpI2ztxP1I582+49Oc5Mq64VQ=
	dep	zgo.at/jfmt	v0.0.0-20240726113937-e6436421fade	h1:1FbpqgZbIvTyViQnvcdwE6yg7xgwMxqls7XDf1EI6oA=
	dep	zgo.at/runewidth	v0.1.0	h1:ED4PzJpYJlZMDEkoz+iPKjb5NrwbKnWPXDMJlNlfk9g=
	dep	zgo.at/termtext	v1.5.0	h1:4p9GVUDYUR8oWvpxOZsO5ZrNSkA99bp8gXNKxKj+Kl0=
	dep	zgo.at/zli	v0.0.0-20241220135549-7a37675fadfd	h1:6FgPCytAJqWegtH2X07VJVApHupmbFUTBnQQCl8Qav4=
	dep	zgo.at/zstd	v0.0.0-20240531161000-9840c0c39ff5	h1:tCJs56IMbX30f4wRkK9zr+Uxu9yiUexE88AkOFgZ+KI=
	build	-buildmode=exe
	build	-compiler=gc
	build	DefaultGODEBUG=asynctimerchan=1,containermaxprocs=0,cryptocustomrand=1,decoratemappings=0,gotestjsonbuildtext=1,gotypesalias=0,httpcookiemaxnum=0,httplaxcontentlength=1,httpmuxgo121=1,httpservecontentkeepheaders=1,multipathtcp=0,panicnil=1,randseednop=0,rsa1024min=0,tls10server=1,tls3des=1,tlsmlkem=0,tlsrsakex=1,tlssecpmlkem=0,tlssha1=1,tlsunsafeekm=1,updatemaxprocs=0,urlmaxqueryparams=0,urlstrictcolons=0,winreadlinkvolume=0,winsymlink=0,x509keypairleaf=0,x509negativeserial=1,x509rsacrt=0,x509sha256skid=0,x509usepolicies=0
	build	CGO_ENABLED=1
	build	CGO_CFLAGS=
	build	CGO_CPPFLAGS=
	build	CGO_CXXFLAGS=
	build	CGO_LDFLAGS=
	build	GOARCH=amd64
	build	GOOS=linux
	build	GOAMD64=v1
```

```text
$ go version -m /home/werner/go/bin/toml-test-decoder
/home/werner/go/bin/toml-test-decoder: go1.26.3
	path	github.com/BurntSushi/toml/cmd/toml-test-decoder
	mod	github.com/BurntSushi/toml	v1.4.0	h1:kuoIxZQy2WRRk1pttg9asf+WVv6tWQuBNVmK8+nqPr0=
	build	-buildmode=exe
	build	-compiler=gc
	build	DefaultGODEBUG=asynctimerchan=1,containermaxprocs=0,cryptocustomrand=1,decoratemappings=0,gotestjsonbuildtext=1,gotypesalias=0,httpcookiemaxnum=0,httplaxcontentlength=1,httpmuxgo121=1,httpservecontentkeepheaders=1,multipathtcp=0,netedns0=0,panicnil=1,randseednop=0,rsa1024min=0,tls10server=1,tls3des=1,tlsmlkem=0,tlsrsakex=1,tlssecpmlkem=0,tlssha1=1,tlsunsafeekm=1,updatemaxprocs=0,urlmaxqueryparams=0,urlstrictcolons=0,winreadlinkvolume=0,winsymlink=0,x509keypairleaf=0,x509negativeserial=1,x509rsacrt=0,x509sha256skid=0,x509usepolicies=0
	build	CGO_ENABLED=1
	build	CGO_CFLAGS=
	build	CGO_CPPFLAGS=
	build	CGO_CXXFLAGS=
	build	CGO_LDFLAGS=
	build	GOARCH=amd64
	build	GOOS=linux
	build	GOAMD64=v1
```

Conformance target with the committed skiplist:

```text
$ make toml-conformance
/home/werner/go/bin/toml-test -skip invalid/array/extend-defined-aot -skip invalid/inline-table/duplicate-key-3 -skip invalid/inline-table/overwrite-02 -skip invalid/inline-table/overwrite-08 -skip invalid/spec/inline-table-2-0 -skip invalid/spec/table-9-1 -skip invalid/table/append-to-array-with-dotted-keys -skip invalid/table/append-with-dotted-keys-1 -skip invalid/table/append-with-dotted-keys-2 -skip invalid/table/duplicate-key-dotted-table -skip invalid/table/duplicate-key-dotted-table2 -skip invalid/table/redefine-2 -skip invalid/table/redefine-3 /home/werner/go/bin/toml-test-decoder
toml-test v0001-01-01 [/home/werner/go/bin/toml-test-decoder]: using embedded tests, 13 skipped
  valid tests: 185 passed,  0 failed
invalid tests: 358 passed,  0 failed
```

Unskipped suite, used to verify that the 13 Makefile skips match the actual fail set:

```text
$ /home/werner/go/bin/toml-test /home/werner/go/bin/toml-test-decoder
FAIL invalid/array/extend-defined-aot
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       [[tab.arr]]
       [tab]
       arr.val1=1

     output from parser-cmd (stdout):
       {
         "tab": {"arr": [{
           "val1": {"type": "integer", "value": "1"}
         }]}
       }

     want:
       Exit code 1

FAIL invalid/inline-table/duplicate-key-3
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       tbl = { fruit = { apple.color = "red" }, fruit.apple.texture = { smooth = true } }

     output from parser-cmd (stdout):
       {
         "tbl": {
           "fruit": {
             "apple": {
               "color": {"type": "string", "value": "red"},
               "texture": {
                 "smooth": {"type": "bool", "value": "true"}
               }
             }
           }
         }
       }

     want:
       Exit code 1

FAIL invalid/inline-table/overwrite-02
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       a={}
       # Inline tables are immutable and can't be extended
       [a.b]

     output from parser-cmd (stdout):
       {
         "a": {
           "b": {}
         }
       }

     want:
       Exit code 1

FAIL invalid/inline-table/overwrite-08
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       tab = { inner = { dog = "best" }, inner.cat = "worst" }

     output from parser-cmd (stdout):
       {
         "tab": {
           "inner": {
             "cat": {"type": "string", "value": "worst"},
             "dog": {"type": "string", "value": "best"}
           }
         }
       }

     want:
       Exit code 1

FAIL invalid/spec/inline-table-2-0
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       [product]
       type = { name = "Nail" }
       type.edible = false  # INVALID

     output from parser-cmd (stdout):
       {
         "product": {
           "type": {
             "edible": {"type": "bool", "value": "false"},
             "name":   {"type": "string", "value": "Nail"}
           }
         }
       }

     want:
       Exit code 1

FAIL invalid/spec/table-9-1
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       [fruit]
       apple.color = "red"
       apple.taste.sweet = true

       # [fruit.apple]  # INVALID
       [fruit.apple.taste]  # INVALID

       [fruit.apple.texture]  # you can add sub-tables
       smooth = true

     output from parser-cmd (stdout):
       {
         "fruit": {
           "apple": {
             "color": {"type": "string", "value": "red"},
             "taste": {
               "sweet": {"type": "bool", "value": "true"}
             },
             "texture": {
               "smooth": {"type": "bool", "value": "true"}
             }
           }
         }
       }

     want:
       Exit code 1

FAIL invalid/table/append-to-array-with-dotted-keys
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       [[a.b]]

       [a]
       b.y = 2

     output from parser-cmd (stdout):
       {
         "a": {"b": [{
           "y": {"type": "integer", "value": "2"}
         }]}
       }

     want:
       Exit code 1

FAIL invalid/table/append-with-dotted-keys-1
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       # First a.b.c defines a table: a.b.c = {z=9}
       #
       # Then we define a.b.c.t = "str" to add a str to the above table, making it:
       #
       #   a.b.c = {z=9, t="..."}
       #
       # While this makes sense, logically, it was decided this is not valid TOML as
       # it's too confusing/convoluted.
       #
       # See: https://github.com/toml-lang/toml/issues/846
       #      https://github.com/toml-lang/toml/pull/859

       [a.b.c]
         z = 9

       [a]
         b.c.t = "Using dotted keys to add to [a.b.c] after explicitly defining it above is not allowed"

     output from parser-cmd (stdout):
       {
         "a": {
           "b": {
             "c": {
               "z": {"type": "integer", "value": "9"},
               "t": {
                 "type":  "string",
                 "value": "Using dotted keys to add to [a.b.c] after explicitly defining it above is not allowed"
               }
             }
           }
         }
       }

     want:
       Exit code 1

FAIL invalid/table/append-with-dotted-keys-2
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       # This is the same issue as in injection-1.toml, except that nests one level
       # deeper. See that file for a more complete description.

       [a.b.c.d]
         z = 9

       [a]
         b.c.d.k.t = "Using dotted keys to add to [a.b.c.d] after explicitly defining it above is not allowed"

     output from parser-cmd (stdout):
       {
         "a": {
           "b": {
             "c": {
               "d": {
                 "z": {"type": "integer", "value": "9"},
                 "k": {
                   "t": {
                     "type":  "string",
                     "value": "Using dotted keys to add to [a.b.c.d] after explicitly defining it above is not allowed"
                   }
                 }
               }
             }
           }
         }
       }

     want:
       Exit code 1

FAIL invalid/table/duplicate-key-dotted-table
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       [fruit]
       apple.color = "red"

       [fruit.apple] # INVALID

     output from parser-cmd (stdout):
       {
         "fruit": {
           "apple": {
             "color": {"type": "string", "value": "red"}
           }
         }
       }

     want:
       Exit code 1

FAIL invalid/table/duplicate-key-dotted-table2
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       [fruit]
       apple.taste.sweet = true

       [fruit.apple.taste] # INVALID

     output from parser-cmd (stdout):
       {
         "fruit": {
           "apple": {
             "taste": {
               "sweet": {"type": "bool", "value": "true"}
             }
           }
         }
       }

     want:
       Exit code 1

FAIL invalid/table/redefine-2
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       [t1]
       t2.t3.v = 0
       [t1.t2]

     output from parser-cmd (stdout):
       {
         "t1": {
           "t2": {
             "t3": {
               "v": {"type": "integer", "value": "0"}
             }
           }
         }
       }

     want:
       Exit code 1

FAIL invalid/table/redefine-3
     Expected an error, but no error was reported.

     input sent to parser-cmd:
       [t1]
       t2.t3.v = 0
       [t1.t2.t3]

     output from parser-cmd (stdout):
       {
         "t1": {
           "t2": {
             "t3": {
               "v": {"type": "integer", "value": "0"}
             }
           }
         }
       }

     want:
       Exit code 1

toml-test v0001-01-01 [/home/werner/go/bin/toml-test-decoder]: using embedded tests
  valid tests: 185 passed,  0 failed
invalid tests: 358 passed, 13 failed
```

## Unit classifications

U01 - version-pinning-binds-conformance-to-validator-parser

Classification: complete. Severity: none.

Evidence: Makefile pins `TOML_TEST_DECODER_VERSION := v1.4.0` at Makefile:22. The Go validator module requires `github.com/BurntSushi/toml v1.4.0` at tools/dagtoml-validate-go/go.mod:5. The local `toml-test-decoder` binary inspected with `go version -m` also reports module `github.com/BurntSushi/toml v1.4.0`. The Makefile comment at Makefile:18-21 states the binding to the parser used by tools/dagtoml-validate-go.

U02 - skiplist-baseline-is-honest

Classification: complete. Severity: none.

Evidence: Makefile:24-31 documents the category, says this is a baseline of currently-known tolerated permissiveness, says it is not a green light, and says version bumps must revisit it. Makefile:36-49 lists exactly these 13 skips:

- invalid/array/extend-defined-aot
- invalid/inline-table/duplicate-key-3
- invalid/inline-table/overwrite-02
- invalid/inline-table/overwrite-08
- invalid/spec/inline-table-2-0
- invalid/spec/table-9-1
- invalid/table/append-to-array-with-dotted-keys
- invalid/table/append-with-dotted-keys-1
- invalid/table/append-with-dotted-keys-2
- invalid/table/duplicate-key-dotted-table
- invalid/table/duplicate-key-dotted-table2
- invalid/table/redefine-2
- invalid/table/redefine-3

The unskipped `/home/werner/go/bin/toml-test /home/werner/go/bin/toml-test-decoder` run failed exactly those 13 tests and no others. The skipped Make target then passed with `valid tests: 185 passed, 0 failed` and `invalid tests: 358 passed, 0 failed`.

U03 - ci-step-is-mandatory-not-soft

Classification: complete. Severity: none.

Evidence: .github/workflows/validate.yml:69-82 adds the conformance step. The script contains `set -e` at .github/workflows/validate.yml:80, runs `make toml-conformance-install` at line 81 and `make toml-conformance` as the final command at line 82. There is no `continue-on-error: true` in the new step, and no shell construct swallows a nonzero exit.

U04 - no-spec-or-validator-byte-changed

Classification: complete. Severity: none.

Evidence: `git diff --name-only 8cc1110..afe354c` returned exactly:

```text
.github/workflows/validate.yml
CHANGELOG.md
Makefile
```

No SPEC.md, core/, profiles/, validators/, examples/, ontology, or kind descriptor path appears in the reviewed commit range. The commit stat likewise reports only those three changed files.

U05 - changelog-and-followup-honest

Classification: complete. Severity: none.

Evidence: The entry lives under `## [Unreleased]` at CHANGELOG.md:8 and `### Added` at CHANGELOG.md:10. The entry begins at CHANGELOG.md:12. It names the parser-binding claim at CHANGELOG.md:16-20: the decoder is shipped by the same `BurntSushi/toml v1.4.0` module that `tools/dagtoml-validate-go` depends on, so a green run is evidence about the parser the Go validator uses. It describes the 13 known misses and skiplist discipline at CHANGELOG.md:20-26. It states the Rust-side gap as a follow-up at CHANGELOG.md:28-31, rather than claiming Rust parser coverage is done.

## Process confirmations

Active-user migration or behavior-change guidance: not applicable to this CI/build-tooling-only commit. Evidence: the changed-file list is only .github/workflows/validate.yml, CHANGELOG.md, and Makefile; no SPEC/profile/validator/instance behavior bytes are changed.

Historical dated spec retcon check: no historical dated spec was retconned in this range. Evidence: no SPEC.md, docs spec history, profile, core, validator, or instance files are in `git diff --name-only 8cc1110..afe354c`.

Claimed tests actually run: yes, with command output above. The exact requested `make toml-conformance-install && make toml-conformance` command was attempted and failed at the network-blocked `go install` fetch. The already-present pinned binaries were inspected with `go version -m`, `make toml-conformance` was run successfully, and the unskipped suite was run to verify the skiplist matches the actual failure set.

## Findings

No findings.

The only execution limitation was local network denial during `go install`, reported above verbatim. It does not indicate a repository defect because the install recipe is correctly pinned at Makefile:56-58, the CI environment is expected to have network access for `go install`, and the locally present binaries match the pinned modules used for the suite run.

Terminal verdict: unconditional_approval
