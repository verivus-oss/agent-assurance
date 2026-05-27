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
# This decoder is shipped by the same BurntSushi/toml module the Go
# validator (tools/dagtoml-validate-go) depends on. Conformance of
# this decoder is therefore evidence about the parser the Go
# validator actually uses at runtime.
TOML_TEST_DECODER_VERSION := v1.4.0

# The 13 invalid-test names BurntSushi/toml v1.4.0 fails to reject.
# All are edge cases around dotted-key / inline-table redefinition
# and TOML 1.1-spec-tightening fixtures that the parser pre-dates.
# This is a baseline of *currently-known-tolerated-permissiveness*,
# NOT a green light — each entry should be revisited when bumping
# TOML_TEST_DECODER_VERSION. If a bump newly passes one of these,
# remove it. If a bump newly fails something not listed, treat that
# as a regression and fix the bump rather than extend the list.
#
# Space-separated; the recipe turns each into a repeated `-skip`
# flag via $(addprefix). Don't comma-join: make line-continuation
# would inject spaces and toml-test would parse only the first.
TOML_CONFORMANCE_SKIPS := \
  invalid/array/extend-defined-aot \
  invalid/inline-table/duplicate-key-3 \
  invalid/inline-table/overwrite-02 \
  invalid/inline-table/overwrite-08 \
  invalid/spec/inline-table-2-0 \
  invalid/spec/table-9-1 \
  invalid/table/append-to-array-with-dotted-keys \
  invalid/table/append-with-dotted-keys-1 \
  invalid/table/append-with-dotted-keys-2 \
  invalid/table/duplicate-key-dotted-table \
  invalid/table/duplicate-key-dotted-table2 \
  invalid/table/redefine-2 \
  invalid/table/redefine-3

# Path to the in-repo Rust decoder shim. Built by
# `toml-conformance-rs` from tools/toml-test-decode-rs/. The shim
# uses the same `toml` 0.8 crate that tools/dagtoml-validate-rs
# depends on, so a green run here is evidence about the parser the
# Rust validator actually uses at runtime — the symmetric half of
# the BurntSushi/toml conformance check above.
RS_DECODER_BIN := tools/toml-test-decode-rs/target/release/toml-test-decode-rs

.PHONY: help toml-conformance toml-conformance-install toml-conformance-rs toml-conformance-all

help: ## Show available targets.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[1m%-32s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

toml-conformance-install: ## Install pinned toml-test + BurntSushi decoder under $GOBIN.
	GOBIN=$(GOBIN) go install github.com/toml-lang/toml-test/cmd/toml-test@$(TOML_TEST_VERSION)
	GOBIN=$(GOBIN) go install github.com/BurntSushi/toml/cmd/toml-test-decoder@$(TOML_TEST_DECODER_VERSION)

toml-conformance: ## Run TOML 1.0 spec-conformance suite against the BurntSushi parser used by tools/dagtoml-validate-go.
	@test -x "$(GOBIN)/toml-test"          || { echo "missing $(GOBIN)/toml-test — run: make toml-conformance-install"; exit 2; }
	@test -x "$(GOBIN)/toml-test-decoder"  || { echo "missing $(GOBIN)/toml-test-decoder — run: make toml-conformance-install"; exit 2; }
	$(GOBIN)/toml-test $(addprefix -skip ,$(TOML_CONFORMANCE_SKIPS)) $(GOBIN)/toml-test-decoder

toml-conformance-rs: ## Run TOML 1.0 spec-conformance suite against the `toml` crate used by tools/dagtoml-validate-rs.
	@test -x "$(GOBIN)/toml-test" || { echo "missing $(GOBIN)/toml-test — run: make toml-conformance-install"; exit 2; }
	cargo build --release --locked --manifest-path tools/toml-test-decode-rs/Cargo.toml \
	  || cargo build --release --manifest-path tools/toml-test-decode-rs/Cargo.toml
	# Empirical: the Rust `toml` 0.8 crate currently passes the full suite
	# (185/185 valid + 371/371 invalid, zero skips needed). No
	# permissiveness-baseline list to maintain. If a future crate bump
	# starts failing tests, add a TOML_CONFORMANCE_RS_SKIPS variable
	# mirroring TOML_CONFORMANCE_SKIPS above and route it through the
	# same `-skip` flag expansion. Empty for now is intentional.
	$(GOBIN)/toml-test "$(abspath $(RS_DECODER_BIN))"

toml-conformance-all: toml-conformance toml-conformance-rs ## Run both Go-parser and Rust-parser conformance suites.
