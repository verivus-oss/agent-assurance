# DAG-TOML Validators

DAG-TOML is validated by independent Rust, Go, and Python implementations.

## Primary Validators

- Rust: `tools/dagtoml-validate-rs/`
- Go: `tools/dagtoml-validate-go/`

## Reference Validators

- Python: `validators/*.py`

## Local Commands

```sh
cargo build --release --manifest-path tools/dagtoml-validate-rs/Cargo.toml
go build -o /tmp/dagtoml-validate-go ./tools/dagtoml-validate-go
./tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . examples/minimal-implementation-dag.toml
/tmp/dagtoml-validate-go --repo-root . examples/minimal-implementation-dag.toml
```
