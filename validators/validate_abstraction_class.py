#!/usr/bin/env python3
"""Validate `[kind.abstraction_class]` and `[kind.capability_envelope]`
declarations in `*-kind.toml` files per SPEC §13.

Both declarations are OPTIONAL at `schema_version = "0.1.0"`. When
present they MUST be structurally well-formed:

  §13.2  `[kind.abstraction_class]`
    - `id` is a non-empty string of shape `<slug>.v<integer>`.
    - `description` is a non-empty string.
    - IJB tags `ijb_primitive = "constraint"` +
      `ijb_constraint_type = "structural"` carry the IJB
      conformance rule (§13.6).

  §13.3  `[kind.capability_envelope]`
    - `spec_version` is a non-empty string.
    - IJB tags as for §13.2.
    - `[kind.capability_envelope.cpu_bounds]` and `.memory_bounds`
      are tables with non-negative integer fields.
    - Every sub-table whose name is a capability-domain name
      (filesystem | sockets | http | clocks | random | environment
      | process_spawn | ipc | crypto_keys) is structurally
      well-formed for that domain.
    - Sub-table names outside the closed domain set (loaded from
      `core/ontology.toml [[attribute_vocabularies]]
      attribute = "capability_envelope.domain"`) are rejected.
    - A domain whose sub-table is entirely omitted is treated as
      denied (fail-closed per §13.9). The validator records that
      semantic for downstream tooling but does not reject on
      omission.

The validator does NOT enforce:
- The attenuation calculus (child envelope ⊆ parent envelope) —
  that is a separate Stream F V2 deliverable.
- Runtime conformance (does the actual artefact stay inside the
  envelope) — that is the future `runtime-observation-attestation`
  kind.
- The WASM Component Model static-observability check — that is
  RUNTIME-SPEC per §13.5.

Exits 0 on pass; 1 on any structural violation.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*\.v\d+$")

REQUIRED_IJB_PRIMITIVE = "constraint"
REQUIRED_IJB_CONSTRAINT_TYPE = "structural"


def _load_domains(repo_root: pathlib.Path) -> set[str]:
    """Load the closed set of capability-domain names from the core
    ontology. Single source of truth — the validator does not
    duplicate the list."""
    ont = repo_root / "core" / "ontology.toml"
    data = tomllib.loads(ont.read_text())
    for entry in data.get("attribute_vocabularies", []):
        if entry.get("attribute") == "capability_envelope.domain":
            values = entry.get("values", [])
            return {str(v) for v in values if isinstance(v, str)}
    raise SystemExit(
        f"core ontology is missing the `capability_envelope.domain` "
        f"vocabulary (looked in {ont})"
    )


def _check_int_field(
    table: dict,
    key: str,
    location: str,
    *,
    allow_none: bool = False,
    nonneg: bool = True,
) -> list[str]:
    if key not in table:
        return [f"{location}: missing required integer field `{key}`"]
    v = table[key]
    if allow_none and v is None:
        return []
    if isinstance(v, bool) or not isinstance(v, int):
        return [
            f"{location}.{key}: must be an integer, got "
            f"{type(v).__name__}: {v!r}"
        ]
    if nonneg and v < 0:
        return [f"{location}.{key}: must be non-negative, got {v}"]
    return []


def _check_bool_field(
    table: dict, key: str, location: str
) -> list[str]:
    if key not in table:
        return [f"{location}: missing required boolean field `{key}`"]
    v = table[key]
    if not isinstance(v, bool):
        return [
            f"{location}.{key}: must be a boolean, got "
            f"{type(v).__name__}: {v!r}"
        ]
    return []


def _check_string_list(
    table: dict, key: str, location: str
) -> list[str]:
    if key not in table:
        return [f"{location}: missing required string-list field `{key}`"]
    v = table[key]
    if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
        return [
            f"{location}.{key}: must be a list of strings, got "
            f"{type(v).__name__}: {v!r}"
        ]
    return []


def _check_ijb_tags(table: dict, location: str) -> list[str]:
    errors = []
    primitive = table.get("ijb_primitive")
    if primitive != REQUIRED_IJB_PRIMITIVE:
        errors.append(
            f"{location}.ijb_primitive: must be "
            f"{REQUIRED_IJB_PRIMITIVE!r}, got {primitive!r}"
        )
    ctype = table.get("ijb_constraint_type")
    if ctype != REQUIRED_IJB_CONSTRAINT_TYPE:
        errors.append(
            f"{location}.ijb_constraint_type: must be "
            f"{REQUIRED_IJB_CONSTRAINT_TYPE!r}, got {ctype!r}"
        )
    return errors


def _check_domain_filesystem(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    errors = _check_string_list(table, "preopens", loc)
    errors.extend(_check_bool_field(table, "read_allowed", loc))
    errors.extend(_check_bool_field(table, "write_allowed", loc))
    errors.extend(_check_bool_field(table, "exec_allowed", loc))
    return errors


def _check_domain_sockets(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    errors = []
    for key in ("tcp_allowlist", "udp_allowlist"):
        if key in table and table[key] is not False:
            errors.extend(_check_string_list(table, key, loc))
    if "ip_resolve_allowed" in table:
        errors.extend(_check_bool_field(table, "ip_resolve_allowed", loc))
    return errors


def _check_domain_http(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    errors = _check_string_list(table, "outgoing_host_allowlist", loc)
    errors.extend(_check_int_field(table, "max_concurrent_requests", loc))
    return errors


def _check_domain_clocks(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    errors = _check_bool_field(table, "wall_clock_allowed", loc)
    errors.extend(_check_bool_field(table, "monotonic_clock_allowed", loc))
    if "precision_cap_ms" in table:
        errors.extend(_check_int_field(table, "precision_cap_ms", loc))
    return errors


def _check_domain_random(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    src = table.get("entropy_source")
    if src not in ("os", "deterministic_seed", "none"):
        return [
            f"{loc}.entropy_source: must be one of "
            f"['os', 'deterministic_seed', 'none'], got {src!r}"
        ]
    return []


def _check_domain_environment(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    return _check_string_list(table, "var_allowlist", loc)


def _check_domain_process_spawn(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    return _check_string_list(table, "allowed_programs", loc)


def _check_domain_ipc(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    errors = _check_bool_field(table, "shared_memory_allowed", loc)
    errors.extend(_check_bool_field(table, "fd_passing_allowed", loc))
    return errors


def _check_domain_crypto_keys(table: dict, loc: str) -> list[str]:
    if table.get("denied") is True:
        return []
    errors = []
    for key in ("read_keys", "use_keys"):
        if key in table:
            errors.extend(_check_string_list(table, key, loc))
    if "generate_allowed" in table:
        errors.extend(_check_bool_field(table, "generate_allowed", loc))
    return errors


DOMAIN_CHECKERS = {
    "filesystem": _check_domain_filesystem,
    "sockets": _check_domain_sockets,
    "http": _check_domain_http,
    "clocks": _check_domain_clocks,
    "random": _check_domain_random,
    "environment": _check_domain_environment,
    "process_spawn": _check_domain_process_spawn,
    "ipc": _check_domain_ipc,
    "crypto_keys": _check_domain_crypto_keys,
}


def validate_abstraction_class(
    block: dict, path: pathlib.Path
) -> list[str]:
    loc = f"{path}: [kind.abstraction_class]"
    errors = []
    id_val = block.get("id")
    if not isinstance(id_val, str) or not id_val:
        errors.append(f"{loc}.id: must be a non-empty string, got {id_val!r}")
    elif not ID_PATTERN.match(id_val):
        errors.append(
            f"{loc}.id: must match `<slug>.v<integer>` "
            f"(lowercase slug + `.v` + non-negative integer), "
            f"got {id_val!r}"
        )
    desc = block.get("description")
    if not isinstance(desc, str) or not desc:
        errors.append(
            f"{loc}.description: must be a non-empty string, got {desc!r}"
        )
    errors.extend(_check_ijb_tags(block, loc))
    return errors


def validate_capability_envelope(
    block: dict, path: pathlib.Path, domains: set[str]
) -> list[str]:
    loc = f"{path}: [kind.capability_envelope]"
    errors = []
    spec_version = block.get("spec_version")
    if not isinstance(spec_version, str) or not spec_version:
        errors.append(
            f"{loc}.spec_version: must be a non-empty string, "
            f"got {spec_version!r}"
        )
    errors.extend(_check_ijb_tags(block, loc))

    # cpu_bounds + memory_bounds: required tables
    cpu = block.get("cpu_bounds")
    if not isinstance(cpu, dict):
        errors.append(f"{loc}.cpu_bounds: missing required table")
    else:
        errors.extend(
            _check_int_field(cpu, "max_cpu_ms", f"{loc}.cpu_bounds")
        )
        errors.extend(
            _check_int_field(
                cpu,
                "max_cpu_percent",
                f"{loc}.cpu_bounds",
                allow_none=True,
            )
        )

    mem = block.get("memory_bounds")
    if not isinstance(mem, dict):
        errors.append(f"{loc}.memory_bounds: missing required table")
    else:
        errors.extend(
            _check_int_field(mem, "max_bytes", f"{loc}.memory_bounds")
        )

    # Domain sub-tables: closed set; unknown names are rejected.
    known_subtable_keys = {"cpu_bounds", "memory_bounds", "spec_version",
                            "ijb_primitive", "ijb_constraint_type"}
    for key, val in block.items():
        if key in known_subtable_keys:
            continue
        if not isinstance(val, dict):
            errors.append(
                f"{loc}.{key}: top-level value must be a sub-table, "
                f"got {type(val).__name__}"
            )
            continue
        if key not in domains:
            errors.append(
                f"{loc}.{key}: not a capability domain. Closed set: "
                f"{sorted(domains)}. Adding a new domain requires a SPEC "
                f"amendment (§13.3)."
            )
            continue
        checker = DOMAIN_CHECKERS.get(key)
        if checker:
            errors.extend(checker(val, f"{loc}.{key}"))
    return errors


def validate(path: pathlib.Path, domains: set[str]) -> list[str]:
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"{path}: cannot parse TOML ({exc})"]

    kind = data.get("kind", {})
    if not isinstance(kind, dict):
        return []  # not a kind descriptor; silently skip

    errors: list[str] = []
    ac = kind.get("abstraction_class")
    if isinstance(ac, dict):
        errors.extend(validate_abstraction_class(ac, path))

    ce = kind.get("capability_envelope")
    if isinstance(ce, dict):
        errors.extend(
            validate_capability_envelope(ce, path, domains)
        )

    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate `[kind.abstraction_class]` and "
            "`[kind.capability_envelope]` declarations in `*-kind.toml` "
            "files per SPEC §13."
        )
    )
    parser.add_argument(
        "paths", nargs="+", help="TOML kind-descriptor file(s) to validate."
    )
    parser.add_argument(
        "--repo-root", default=".",
        help=(
            "Repository root containing `core/ontology.toml` "
            "(used to load the closed capability-domain set). "
            "Defaults to current directory."
        ),
    )
    args = parser.parse_args(argv)

    repo = pathlib.Path(args.repo_root).resolve()
    domains = _load_domains(repo)

    failures: list[str] = []
    checked = 0
    declared = 0
    for raw in args.paths:
        p = pathlib.Path(raw)
        if not p.exists():
            failures.append(f"{p}: does not exist")
            continue
        checked += 1
        errs = validate(p, domains)
        # Detect whether any §13 block was actually declared so the
        # summary line at the bottom is accurate.
        try:
            data = tomllib.loads(p.read_text())
            kind = data.get("kind", {})
            if isinstance(kind, dict) and (
                "abstraction_class" in kind or "capability_envelope" in kind
            ):
                declared += 1
        # Per-file kind-check failures are intentionally swallowed; the
        # same defect is already counted in `failures` above, so re-raising
        # would double-count.
        except Exception:  # nosec B110  # noqa: S110
            pass
        failures.extend(errs)

    if failures:
        for f in failures:
            print(f"FAIL {f}", file=sys.stderr)
        print(
            f"\nABSTRACTION-CLASS VALIDATION FAILED: {len(failures)} "
            f"error(s) across {checked} file(s).",
            file=sys.stderr,
        )
        return 1

    print(
        f"ABSTRACTION-CLASS VALIDATION PASSED ({checked} file(s) checked; "
        f"{declared} declared a §13 block)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
