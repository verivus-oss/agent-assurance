# Local validation log — com.verivus.runtime / api-snapshot

FINAL run. Reviewer iterations: Grok r1 (approved), Codex r1 (2 blockers), Codex r2 (approved after fix). Bad-closure marked out of conformance scope via unblessed template_kind so bare `--discover .` passes. RS=release Rust primary; GO=fresh Go build; Python=system python3 (tomli 2.4.1).

```
## ACCEPTANCE — POSITIVES (expect exit 0)

$ python3 validators/validate_kind_descriptor.py profiles/com.verivus.runtime/api-snapshot-kind.toml --repo-root . --check-references-exist
KIND DESCRIPTOR VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/api-snapshot-kind.toml
exit=0

$ python3 validators/validate_ijb_conformance.py profiles/com.verivus.runtime/ontology.toml
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/ontology.toml
exit=0

$ python3 validators/validate_ijb_conformance.py profiles/com.verivus.runtime/api-snapshot-kind.toml
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/api-snapshot-kind.toml
exit=0

$ python3 validators/validate_ijb_conformance.py examples/minimal-api-snapshot.toml --repo-root .
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/examples/minimal-api-snapshot.toml
exit=0

$ python3 validators/validate_closure_root.py examples/minimal-api-snapshot.toml profiles/com.verivus.runtime/api-snapshot-kind.toml profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/PROFILE.toml
CLOSURE-ROOT VALIDATION PASSED (4 file(s)).
exit=0

$ python3 validators/validate_closure_root.py --discover .
CLOSURE-ROOT VALIDATION PASSED (100 file(s)).
exit=0

$ python3 validators/validate_abstraction_class.py profiles/com.verivus.runtime/api-snapshot-kind.toml --repo-root .
ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).
exit=0

$ python3 validators/validate_profile_descriptor.py --repo-root . profiles/com.verivus.runtime/PROFILE.toml
PROFILE DESCRIPTOR VALIDATION PASSED
- files validated: 1
exit=0

$ python3 validators/validate_provenance.py examples/minimal-api-snapshot.toml --repo-root .
PROVENANCE VALIDATION PASSED
- files inspected: 1
exit=0

$ python3 validators/validate_api_snapshot.py --repo-root . examples/minimal-api-snapshot.toml
API-SNAPSHOT VALIDATION PASSED
- files inspected: 1
exit=0

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode provenance examples/minimal-api-snapshot.toml profiles/com.verivus.runtime/api-snapshot-kind.toml profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/PROFILE.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 4
exit=0

$ /tmp/dagtoml-validate-go -repo-root . -mode provenance examples/minimal-api-snapshot.toml profiles/com.verivus.runtime/api-snapshot-kind.toml profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/PROFILE.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 4
exit=0

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode ijb profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/api-snapshot-kind.toml examples/minimal-api-snapshot.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 3
exit=0

$ /tmp/dagtoml-validate-go -repo-root . -mode ijb profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/api-snapshot-kind.toml examples/minimal-api-snapshot.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 3
exit=0

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode kind-descriptor profiles/com.verivus.runtime/api-snapshot-kind.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 1
exit=0

$ /tmp/dagtoml-validate-go -repo-root . -mode kind-descriptor profiles/com.verivus.runtime/api-snapshot-kind.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 1
exit=0

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode abstraction-class profiles/com.verivus.runtime/api-snapshot-kind.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 1
exit=0

$ /tmp/dagtoml-validate-go -repo-root . -mode abstraction-class profiles/com.verivus.runtime/api-snapshot-kind.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 1
exit=0

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode profile profiles/com.verivus.runtime/PROFILE.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 1
exit=0

$ /tmp/dagtoml-validate-go -repo-root . -mode profile profiles/com.verivus.runtime/PROFILE.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 1
exit=0

$ taplo lint profiles/com.verivus.runtime/api-snapshot-kind.toml profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/PROFILE.toml examples/minimal-api-snapshot.toml
 INFO taplo:load_config: found configuration file path="/srv/repos/external/verivus-oss/agent-assurance/.taplo.toml"
 INFO taplo:lint_files:collect_files: found files total=4 excluded=0 files=["/srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/api-snapshot-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/ontology.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/PROFILE.toml", "/srv/repos/external/verivus-oss/agent-assurance/examples/minimal-api-snapshot.toml"] cwd="/srv/repos/external/verivus-oss/agent-assurance"
exit=0

## ACCEPTANCE — NEGATIVES (expect exit 1, rejected by all listed impls)

$ python3 validators/validate_closure_root.py examples/negative/api-snapshot-bad-closure.toml
FAIL examples/negative/api-snapshot-bad-closure.toml: `closure_root` does not match SPEC §12.8 source-hash closure. Expected `sha256:f251f64bc6170cb32a4b3c0bcc10d520247c41e7bbf22587d206108e6d19098c` from 1 canonical source-hash input(s), got `sha256:013f3d34bab26a1b9d9fd77ff03aae76a3b07ee112c4995dc5ef448b2d1796db`.

exit=1

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode provenance examples/negative/api-snapshot-bad-closure.toml
DAGTOML VALIDATION FAILED (rust primary)
- --- examples/negative/api-snapshot-bad-closure.toml ---
exit=1

$ /tmp/dagtoml-validate-go -repo-root . -mode provenance examples/negative/api-snapshot-bad-closure.toml
DAGTOML VALIDATION FAILED (go primary)
- --- examples/negative/api-snapshot-bad-closure.toml ---
exit=1

$ python3 validators/validate_provenance.py examples/negative/api-snapshot-bad-closure.toml --repo-root .
PROVENANCE VALIDATION FAILED
- files inspected: 1
exit=1

$ python3 validators/validate_ijb_conformance.py examples/negative/com.verivus.runtime-ontology-bad-ijb.toml
IJB CONFORMANCE VALIDATION FAILED
- file: /srv/repos/external/verivus-oss/agent-assurance/examples/negative/com.verivus.runtime-ontology-bad-ijb.toml
exit=1

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode ijb examples/negative/com.verivus.runtime-ontology-bad-ijb.toml
DAGTOML VALIDATION FAILED (rust primary)
- --- examples/negative/com.verivus.runtime-ontology-bad-ijb.toml ---
exit=1

$ /tmp/dagtoml-validate-go -repo-root . -mode ijb examples/negative/com.verivus.runtime-ontology-bad-ijb.toml
DAGTOML VALIDATION FAILED (go primary)
- --- examples/negative/com.verivus.runtime-ontology-bad-ijb.toml ---
exit=1

$ python3 validators/validate_api_snapshot.py --repo-root . examples/negative/api-snapshot-inlined-secret.toml
API-SNAPSHOT VALIDATION FAILED
- files inspected: 1
exit=1

$ python3 validators/validate_api_snapshot.py --repo-root . examples/negative/api-snapshot-raw-header.toml
API-SNAPSHOT VALIDATION FAILED
- files inspected: 1
exit=1

$ python3 validators/validate_api_snapshot.py --repo-root . examples/negative/api-snapshot-witness-incomplete.toml
API-SNAPSHOT VALIDATION FAILED
- files inspected: 1
exit=1

$ python3 validators/validate_api_snapshot.py --repo-root . examples/negative/api-snapshot-bad-subpart-digest.toml
API-SNAPSHOT VALIDATION FAILED
- files inspected: 1
exit=1

```
