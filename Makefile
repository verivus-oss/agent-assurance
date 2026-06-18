# Developer convenience targets. CI is the source of truth — see
# .github/workflows/validate.yml for the full check matrix. Targets
# here mirror specific CI steps so contributors can reproduce them
# locally without copying shell out of the workflow.

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c

# Where `go install` puts binaries. Picks up $GOBIN if set, falls
# back to $GOPATH/bin, falls back to ~/go/bin.
GOBIN ?= $(shell go env GOBIN)
ifeq ($(GOBIN),)
GOBIN := $(shell go env GOPATH)/bin
endif

# Pinned versions. Bump deliberately; see CHANGELOG.
TOML_TEST_VERSION         := v1.6.0
# Path to the in-repo Go decoder shim. Built by `toml-conformance` from
# tools/toml-test-decode-go/. The shim runs the SAME parser stack the Go
# primary validator (tools/dagtoml-validate-go) uses: a pelletier/go-toml/v2
# strict gate in front of the BurntSushi/toml tagged-JSON emit. A green run
# here is therefore evidence about the strictness the Go validator actually
# enforces at runtime — the symmetric Go-side counterpart to the Rust shim
# (RS_DECODER_BIN). It supersedes the stock BurntSushi cmd/toml-test-decoder,
# which was permissive on the 13 dotted-key / inline-table cases (issue #38).
GO_DECODER_BIN := tools/toml-test-decode-go/toml-test-decode-go

# TOML 1.1 conformance skip list — now EMPTY (issue #38 / contract C01).
#
# Historically BurntSushi/toml v1.6.0 failed to reject 13 invalid-test
# fixtures (all dotted-key / inline-table redefinition cases) that the Rust
# (`toml` 1.1) and Python (tomli) primaries correctly reject, and they were
# tolerated here via `-skip`. That gap is now closed: the Go conformance
# target runs the in-repo tools/toml-test-decode-go shim, which gates every
# input through pelletier/go-toml/v2 (stricter than BurntSushi — it rejects
# all 13 while accepting the full 189-case TOML 1.1 valid corpus) before
# BurntSushi emits the tagged JSON. The Go primary validator
# (tools/dagtoml-validate-go) applies the same pelletier strict pre-check, so
# the conformance evidence matches the parser the validator runs.
#
# Kept (empty) so a future regression can be parked here deliberately rather
# than silently: if a parser bump starts failing a fixture, fix the parser —
# do NOT repopulate this list without a recorded rationale. Space-separated;
# the recipe turns each into a repeated `-skip` flag via $(addprefix).
TOML_CONFORMANCE_SKIPS :=

# Path to the in-repo Rust decoder shim. Built by
# `toml-conformance-rs` from tools/toml-test-decode-rs/. The shim
# uses the same `toml` 1.1 crate that tools/dagtoml-validate-rs
# depends on, so a green run here is evidence about the parser the
# Rust validator actually uses at runtime — the symmetric half of
# the BurntSushi/toml conformance check above.
RS_DECODER_BIN := tools/toml-test-decode-rs/target/release/toml-test-decode-rs

.PHONY: help toml-conformance toml-conformance-install toml-conformance-rs toml-conformance-all dagtoml-conformance

help: ## Show available targets.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[1m%-32s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

toml-conformance-install: ## Install pinned toml-test under $GOBIN.
	GOBIN=$(GOBIN) go install github.com/toml-lang/toml-test/cmd/toml-test@$(TOML_TEST_VERSION)

toml-conformance: ## Run TOML 1.1 spec-conformance suite against the strict parser stack used by tools/dagtoml-validate-go.
	@test -x "$(GOBIN)/toml-test" || { echo "missing $(GOBIN)/toml-test — run: make toml-conformance-install"; exit 2; }
	cd tools/toml-test-decode-go && go build -o toml-test-decode-go .
	# The Go decoder shim gates every input through pelletier/go-toml/v2 (the
	# same strict pre-check the Go validator now applies) before BurntSushi
	# emits the tagged JSON. It rejects all 13 formerly-tolerated dotted-key /
	# inline-table cases AND accepts the full 189-case valid corpus, so this
	# runs with ZERO skips (TOML_CONFORMANCE_SKIPS is empty).
	$(GOBIN)/toml-test -toml 1.1.0 $(addprefix -skip ,$(TOML_CONFORMANCE_SKIPS)) "$(abspath $(GO_DECODER_BIN))"

toml-conformance-rs: ## Run TOML 1.1 spec-conformance suite against the `toml` crate used by tools/dagtoml-validate-rs.
	@test -x "$(GOBIN)/toml-test" || { echo "missing $(GOBIN)/toml-test — run: make toml-conformance-install"; exit 2; }
	cargo build --release --locked --manifest-path tools/toml-test-decode-rs/Cargo.toml \
	  || cargo build --release --manifest-path tools/toml-test-decode-rs/Cargo.toml
	# Empirical: the Rust `toml` 1.1 crate passes the full TOML 1.1 suite
	# (189/189 valid + 362/362 invalid under `-toml 1.1.0`, zero skips
	# needed) — strictly stronger than the BurntSushi decoder, which still
	# tolerates the 13 dotted-key/inline-table cases skipped above. No
	# permissiveness-baseline list to maintain on the Rust side. If a future
	# crate bump starts failing tests, add a TOML_CONFORMANCE_RS_SKIPS
	# variable mirroring TOML_CONFORMANCE_SKIPS above and route it through
	# the same `-skip` flag expansion. Empty for now is intentional.
	$(GOBIN)/toml-test -toml 1.1.0 "$(abspath $(RS_DECODER_BIN))"

toml-conformance-all: toml-conformance toml-conformance-rs ## Run both Go-parser and Rust-parser conformance suites.

dagtoml-conformance: ## Run the cross-implementation DAG-TOML semantic conformance corpus (conformance/).
	cargo build --release --locked --manifest-path tools/dagtoml-validate-rs/Cargo.toml \
	  || cargo build --release --manifest-path tools/dagtoml-validate-rs/Cargo.toml
	cd tools/dagtoml-validate-go && go build -o "$(CURDIR)/dagtoml-validate-go.conformance" .
	python3 conformance/runner.py \
	  --rs tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs \
	  --go "$(CURDIR)/dagtoml-validate-go.conformance"
	rm -f "$(CURDIR)/dagtoml-validate-go.conformance"
