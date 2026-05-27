# Local Validation

Commands run from `/srv/repos/external/verivus-oss/agent-assurance` after applying the `spec.md`, `CHANGELOG.md`, and review-artifact changes.

## `taplo lint`

Exit code: 0.

Key output:

```text
INFO taplo:load_config: found configuration file path="/srv/repos/external/verivus-oss/agent-assurance/.taplo.toml"
INFO taplo:lint_files:collect_files: found files total=195 excluded=0
```

## `python3 validators/validate_closure_root.py --discover .`

Exit code: 0.

```text
CLOSURE-ROOT VALIDATION PASSED (75 file(s)).
```

## `bash validators/check_manifest_drift.sh`

Exit code: 0.

```text
COUNT-MIRROR OK — every surface agrees with reality.

OK — manifest matches ontology + every count-mirror surface agrees
```

## `python3 validators/validate_profile_descriptor.py --repo-root . profiles/agent-assurance/PROFILE.toml profiles/disclosure/PROFILE.toml profiles/cost/PROFILE.toml`

Exit code: 0.

```text
PROFILE DESCRIPTOR VALIDATION PASSED
- files validated: 3
- profiles in resolution set: 3
```
