## 1. Measure definition

I recommend **(B)**: `[counts].attribute_values` should mean the total number of listed values in `[[attribute_vocabularies]]` blocks where `extensible = false`, counted as `(attribute, value)` entries with no cross-vocabulary de-duplication. This matches the enforceable ontology constraint: current validators accept unseen values for extensible vocabularies but reject unseen values only for closed vocabularies, e.g. [validators/validate_disclosure.py](/srv/repos/external/verivus-oss/agent-assurance/validators/validate_disclosure.py:98) and [tools/dagtoml-validate-rs/src/main.rs](/srv/repos/external/verivus-oss/agent-assurance/tools/dagtoml-validate-rs/src/main.rs:537).

The consumer is the ontology-drift contract behind [reference/database/MANIFEST.toml](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:32), not any one engine’s `attribute_value_allowed` row count. Seed files are not a stable source of truth for this field because engines mirror values differently, including enum-backed closed values and text-table values.

## 2. Data acquisition method

Read these ontology files:

- [core/ontology.toml](/srv/repos/external/verivus-oss/agent-assurance/core/ontology.toml:529)
- [profiles/agent-assurance/ontology.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/ontology.toml:111)
- [profiles/disclosure/ontology.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/ontology.toml:74)
- [profiles/cost/ontology.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/cost/ontology.toml:57)

Mechanical recipe:

1. Parse each file as TOML.
2. Inspect the top-level `[[attribute_vocabularies]]` array of tables.
3. For each entry, read `extensible` and `values`.
4. Include the entry only when `extensible == false`.
5. Add `len(values)` to the total.
6. Do not de-duplicate identical string values across different attributes; `status = "pass"` and `smoke.decision = "pass"` are two vocabulary entries.
7. Treat missing/non-boolean `extensible` or missing/non-array `values` as ontology errors, not as countable defaults.

Profile composition should match the manifest drift policy already used by [validators/check_manifest_drift.sh](/srv/repos/external/verivus-oss/agent-assurance/validators/check_manifest_drift.sh:18): canonical repo count = `core/ontology.toml` plus every checked-in `profiles/*/ontology.toml`, sorted by path. A downstream distribution with extra private profiles should maintain its own manifest and re-run the same recipe over its own canonical profile set.

## 3. Validation tooling

I recommend **(ii)**: add a small Python validator and invoke it from `validators/check_manifest_drift.sh`. Shell/awk is already adequate for block counts, but TOML arrays span multiple lines and contain punctuation-heavy values, so using `tomllib` avoids fragile parsing while adding no third-party dependency on Python 3.11+.

Proposed `validators/check_attribute_values.py`:

```python
#!/usr/bin/env python3
from pathlib import Path
import sys
import tomllib

def load_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)

def ontology_paths(root: Path) -> list[Path]:
    return [root / "core" / "ontology.toml", *sorted((root / "profiles").glob("*/ontology.toml"))]

def closed_value_count(path: Path) -> int:
    doc = load_toml(path)
    total = 0
    for index, vocab in enumerate(doc.get("attribute_vocabularies", []), start=1):
        if not isinstance(vocab.get("extensible"), bool):
            raise SystemExit(f"{path}: attribute_vocabularies[{index}] missing boolean extensible")
        values = vocab.get("values")
        if not isinstance(values, list):
            raise SystemExit(f"{path}: attribute_vocabularies[{index}] missing values array")
        if vocab["extensible"] is False:
            total += len(values)
    return total

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    manifest_path = root / "reference" / "database" / "MANIFEST.toml"
    claimed = load_toml(manifest_path)["counts"]["attribute_values"]

    total = 0
    print("attribute-values drift check (closed ontology values vs reference/database/MANIFEST.toml)")
    for path in ontology_paths(root):
        count = closed_value_count(path)
        total += count
        print(f"  {path.relative_to(root)}: {count}")

    if claimed != total:
        print(f"  attribute_values {claimed} != {total}   <-- DRIFT")
        return 1

    print(f"  attribute_values {claimed} == {total}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

Invoke it from `validators/check_manifest_drift.sh` after the existing manifest count comparison:

```bash
python3 "$REPO_ROOT/validators/check_attribute_values.py" "$REPO_ROOT"
```

## 4. Independent computation under your protocol

Command:

```bash
git rev-parse HEAD
```

Verbatim output:

```text
99e18dba38ec3b4c6234b77bac7a87b0f2e6cdfc
```

Command:

```bash
python3 - <<'PY'
from pathlib import Path
import tomllib

files = [
    Path('core/ontology.toml'),
    *sorted(Path('profiles').glob('*/ontology.toml')),
]
closed_total = 0
all_total = 0
for path in files:
    doc = tomllib.loads(path.read_text())
    closed = 0
    all_values = 0
    for vocab in doc.get('attribute_vocabularies', []):
        values = vocab.get('values') or []
        all_values += len(values)
        if vocab.get('extensible') is False:
            closed += len(values)
    closed_total += closed
    all_total += all_values
    print(f'{path}: closed_attribute_values={closed} all_attribute_values={all_values}')
manifest = tomllib.loads(Path('reference/database/MANIFEST.toml').read_text())
claimed = manifest['counts']['attribute_values']
print(f'total_closed_attribute_values={closed_total}')
print(f'total_all_attribute_values={all_total}')
print(f'manifest_attribute_values={claimed}')
print(f'matches_closed={claimed == closed_total}')
PY
```

Verbatim output:

```text
core/ontology.toml: closed_attribute_values=22 all_attribute_values=39
profiles/agent-assurance/ontology.toml: closed_attribute_values=51 all_attribute_values=91
profiles/cost/ontology.toml: closed_attribute_values=22 all_attribute_values=22
profiles/disclosure/ontology.toml: closed_attribute_values=4 all_attribute_values=18
total_closed_attribute_values=99
total_all_attribute_values=170
manifest_attribute_values=170
matches_closed=False
```

Number under this protocol: **99**.

At HEAD, [reference/database/MANIFEST.toml](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:37) claims `attribute_values = 170`, so it **does not match** this protocol.

## 5. Other-reviewer reconciliation

The most defensible rejected interpretation is **(A)**, because it exactly counts every `values` array entry and matches the current manifest value `170`. I reject it because extensible vocabulary lists are starter/catalog entries, not the full allowed domain; the validator behavior at [validators/validate_disclosure.py](/srv/repos/external/verivus-oss/agent-assurance/validators/validate_disclosure.py:98) makes that distinction concrete.

I would switch to (A) if the spec maintainer declares that `attribute_values` is intended to be a finite catalog-size metric for all shipped starter values, not an enforceable-constraint metric. I would switch to (D) if an existing downstream consumer is found that reads `[counts].attribute_values` as an engine-specific `attribute_value_allowed` seed row count, because the current engines intentionally diverge there.

The spec maintainer still needs to decide whether to rename the field to `closed_attribute_values` or keep `attribute_values` with a sharper comment. They should also update `[ontology_source]`, because it currently names only the agent-assurance profile at [reference/database/MANIFEST.toml](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:23) while the actual count policy includes disclosure and cost profiles too.
