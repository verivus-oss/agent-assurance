#!/usr/bin/env python3
"""Assert discovery exclusions apply below each explicitly selected root."""

import json
from pathlib import Path
import uuid

from validate_closure_root import discover_conforming


def main():
    work = Path(".local/closure-discovery") / uuid.uuid4().hex
    root = work / "source"
    accepted = {"visible.toml", "nested/visible.toml"}
    excluded = {".hidden.toml", ".hidden/visible.toml", "target/visible.toml",
                "node_modules/visible.toml", "__pycache__/visible.toml"}
    for name in accepted | excluded:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('[meta]\ntemplate_kind = "implementation-dag"\n')
    (root / "unrelated.toml").write_text('[meta]\ntemplate_kind = "process-note"\n')
    kinds = frozenset({"implementation-dag"})
    observations = []
    for name, selected in (("relative", root), ("absolute", root.resolve())):
        actual = {path.relative_to(selected).as_posix() for path in discover_conforming([selected], kinds)}
        if actual != accepted:
            raise AssertionError(f"{name} root: expected {sorted(accepted)}, observed {sorted(actual)}")
        observations.append({"root_form": name, "accepted": sorted(actual), "excluded": sorted(excluded | {"unrelated.toml"})})
    # Explicit file selection remains supported, including hidden files.
    selected = root / ".hidden.toml"
    if discover_conforming([selected], kinds) != [selected]:
        raise AssertionError("explicit conforming file selection was excluded")
    (work / "receipt.json").write_text(json.dumps({"status": "passed", "observations": observations,
                                                "explicit_hidden_file": "accepted"}, indent=2) + "\n")
    print("PASS: absolute and relative roots select exactly the two conforming visible files; "
          "six excluded files stay excluded; explicit file selection stays accepted; skipped=[]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
