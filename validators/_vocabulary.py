"""Read the authoritative TOML vocabulary declarations, without SQL inference."""

from dataclasses import dataclass
from pathlib import Path

import _toml11 as toml


@dataclass(frozen=True)
class Vocabulary:
    attribute: str
    values: tuple[str, ...]
    extensible: bool
    source: str
    declaration: dict


def load_catalog(repo_root: Path) -> dict[str, Vocabulary]:
    """Reject malformed and duplicate declarations before constructing any set."""
    paths = [repo_root / "core/ontology.toml", *sorted(repo_root.glob("profiles/*/ontology.toml"))]
    if not (repo_root / "profiles/agent-assurance/ontology.toml").is_file():
        raise ValueError("missing agent-assurance ontology")
    catalog = {}
    for path in paths:
        doc = toml.loads(path.read_text(encoding="utf-8"))
        declarations = doc.get("attribute_vocabularies")
        if not isinstance(declarations, list) or not declarations:
            raise ValueError(f"{path}: attribute_vocabularies must be a nonempty array")
        for item in declarations:
            if not isinstance(item, dict):
                raise ValueError(f"{path}: vocabulary declaration must be a table")
            name, values, extensible = item.get("attribute"), item.get("values"), item.get("extensible")
            if not isinstance(name, str) or not name or name in catalog:
                raise ValueError(f"{path}: missing or duplicate vocabulary {name!r}")
            if (not isinstance(values, list) or any(not isinstance(v, str) for v in values)
                    or len(values) != len(set(values)) or not isinstance(extensible, bool)):
                raise ValueError(f"{path}: malformed values/extensible for vocabulary {name!r}")
            catalog[name] = Vocabulary(name, tuple(values), extensible, str(path.relative_to(repo_root)), item)
    return catalog


def canonical_profile(value: object) -> object:
    """SPEC section 2.5 identity alias, only for meta.framework_profile."""
    return "agent-assurance" if value == "AGDF" else value
