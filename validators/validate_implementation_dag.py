#!/usr/bin/env python3
"""Validate implementation DAG TOML files used in this repository."""

from __future__ import annotations

import argparse
import pathlib
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py
from collections import Counter, defaultdict

import networkx as nx


VALID_STATUS = {"pending", "in_progress", "done", "blocked", "deferred"}
VALID_TIER = {1, 2, 3}
REQUIRED_UNIT_FIELDS = (
    "name",
    "summary",
    "layer",
    "tier",
    "status",
    "depends_on",
    "blocks",
    "estimated_loc",
)
ARTIFACT_PREFIXES = ("ART:", "OUT:")
PLACEHOLDER_MARKERS = ("<", ">")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an implementation DAG TOML file.")
    parser.add_argument("dag_file", help="Path to the TOML file to validate.")
    parser.add_argument(
        "--repo-root",
        help="Repository root used for optional files_modify path existence checks.",
    )
    parser.add_argument(
        "--check-paths-exist",
        action="store_true",
        help="Verify files_modify paths exist relative to --repo-root.",
    )
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow placeholder strings like <files-from-triage> in file paths.",
    )
    return parser.parse_args()


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def has_placeholder(value: str) -> bool:
    return any(marker in value for marker in PLACEHOLDER_MARKERS)


def validate_units(doc: dict) -> tuple[list[str], dict[str, dict]]:
    errors: list[str] = []
    units = doc.get("units", {})
    if not units:
        errors.append("no `units` table found")
        return errors, units
    for uid, unit in units.items():
        for field in REQUIRED_UNIT_FIELDS:
            if field not in unit:
                errors.append(f"{uid}: missing required field `{field}`")
        status = unit.get("status")
        if status is not None and status not in VALID_STATUS:
            errors.append(
                f"{uid}: invalid status `{status}` (must be one of {sorted(VALID_STATUS)})"
            )
        tier = unit.get("tier")
        if tier is not None and tier not in VALID_TIER:
            errors.append(f"{uid}: invalid tier `{tier}` (must be 1, 2, or 3)")
        layer = unit.get("layer")
        if layer is not None and (not isinstance(layer, int) or layer < 0):
            errors.append(f"{uid}: layer must be a non-negative integer")
        loc = unit.get("estimated_loc")
        if loc is not None and (not isinstance(loc, int) or loc < 0):
            errors.append(f"{uid}: estimated_loc must be a non-negative integer")
    return errors, units


def validate_edges(units: dict[str, dict]) -> tuple[list[str], dict[str, set[str]], dict[str, set[str]]]:
    """Enforce the inverse invariant between `depends_on` and `blocks`."""
    errors: list[str] = []
    uids = set(units)
    dep_lists = {u: list(units[u].get("depends_on", [])) for u in units}
    blk_lists = {u: list(units[u].get("blocks", [])) for u in units}

    for u, refs in dep_lists.items():
        for r in refs:
            if r == u:
                errors.append(f"{u}: depends_on includes self")
            elif r not in uids:
                errors.append(f"{u}: depends_on references unknown unit `{r}`")
        for r, count in Counter(refs).items():
            if count > 1:
                errors.append(f"{u}: depends_on has duplicate entry `{r}`")
    for u, refs in blk_lists.items():
        for r in refs:
            if r == u:
                errors.append(f"{u}: blocks includes self")
            elif r not in uids:
                errors.append(f"{u}: blocks references unknown unit `{r}`")
        for r, count in Counter(refs).items():
            if count > 1:
                errors.append(f"{u}: blocks has duplicate entry `{r}`")

    dep_sets = {u: set(refs) for u, refs in dep_lists.items()}
    blk_sets = {u: set(refs) for u, refs in blk_lists.items()}
    for a, bs in blk_sets.items():
        for b in bs:
            if b in uids and a not in dep_sets.get(b, set()):
                errors.append(
                    f"inverse mismatch: {a}.blocks contains `{b}` but {b}.depends_on is missing `{a}`"
                )
    for b, deps in dep_sets.items():
        for a in deps:
            if a in uids and b not in blk_sets.get(a, set()):
                errors.append(
                    f"inverse mismatch: {b}.depends_on contains `{a}` but {a}.blocks is missing `{b}`"
                )
    return errors, dep_sets, blk_sets


def _build_dep_graph(dep_sets: dict[str, set[str]]) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_nodes_from(dep_sets)
    for u, deps in dep_sets.items():
        for v in deps:
            G.add_edge(u, v)
    return G


def detect_cycles(dep_sets: dict[str, set[str]]) -> list[str]:
    G = _build_dep_graph(dep_sets)
    errors: list[str] = []
    seen: set[tuple[str, ...]] = set()
    for cycle in nx.simple_cycles(G):
        # nx.simple_cycles yields each cycle as a list of nodes (no repeat of
        # the first node at the end). Normalise to the canonical rotation so
        # the same cycle reported from a different entry point dedupes, and
        # close the loop in the printed form to match the historical output.
        rot = min(range(len(cycle)), key=lambda i: cycle[i:] + cycle[:i])
        canonical = tuple(cycle[rot:] + cycle[:rot])
        if canonical in seen:
            continue
        seen.add(canonical)
        path = list(canonical) + [canonical[0]]
        errors.append(f"cycle in depends_on: {' -> '.join(path)}")
    return errors


def validate_artifacts(units: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    producers: dict[str, list[str]] = defaultdict(list)
    for uid, unit in units.items():
        for art in unit.get("produces", []):
            producers[art].append(uid)
    for art, ps in producers.items():
        if not art.startswith(ARTIFACT_PREFIXES):
            errors.append(
                f"{ps[0]}: produces `{art}` has unrecognized prefix (expected ART: or OUT:)"
            )
        if len(ps) > 1:
            errors.append(f"artifact `{art}` has multiple producers: {sorted(ps)}")
    produced = set(producers)
    for uid, unit in units.items():
        for art in unit.get("consumes", []):
            if not art.startswith(ARTIFACT_PREFIXES):
                errors.append(
                    f"{uid}: consumes `{art}` has unrecognized prefix (expected ART: or OUT:)"
                )
                continue
            if art not in produced:
                errors.append(
                    f"{uid}: consumes `{art}` which is not produced by any unit in the DAG"
                )
    return errors


def validate_layer_ordering(
    units: dict[str, dict], dep_sets: dict[str, set[str]]
) -> list[str]:
    errors: list[str] = []
    for u, deps in dep_sets.items():
        ul = units[u].get("layer")
        if not isinstance(ul, int):
            continue
        for d in deps:
            if d not in units:
                continue
            dl = units[d].get("layer")
            if not isinstance(dl, int):
                continue
            if ul <= dl:
                errors.append(
                    f"layer ordering: {u} (layer={ul}) depends_on {d} (layer={dl}) — "
                    f"a depender must be in a strictly higher layer"
                )
    return errors


def validate_meta(meta: dict, units: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    if "total_units" in meta and meta["total_units"] != len(units):
        errors.append(
            f"meta.total_units={meta['total_units']} but units table has {len(units)} entries"
        )
    by_tier: dict[int, set[str]] = defaultdict(set)
    for uid, unit in units.items():
        tier = unit.get("tier")
        if tier in VALID_TIER:
            by_tier[tier].add(uid)
    for tier in (1, 2, 3):
        key = f"tier{tier}_units"
        if key not in meta:
            continue
        declared = set(meta[key])
        actual = by_tier[tier]
        for extra in sorted(declared - actual):
            errors.append(
                f"meta.{key} lists `{extra}` but that unit does not have tier={tier}"
            )
        for missing in sorted(actual - declared):
            errors.append(f"meta.{key} is missing `{missing}` (unit has tier={tier})")
    return errors


def longest_path_loc(units: dict[str, dict], blk_sets: dict[str, set[str]]) -> int | None:
    """DAG longest path by `estimated_loc` (node-weighted). Returns None on cycle.

    The score for a path n0 -> n1 -> ... -> nk is the sum of each node's
    `estimated_loc`; the result is the maximum such score across all paths
    (a single node counts as a length-1 path).
    """
    if not units:
        return 0
    G = nx.DiGraph()
    G.add_nodes_from(units)
    for u, blocked in blk_sets.items():
        for v in blocked:
            if v in units:
                G.add_edge(u, v)
    if not nx.is_directed_acyclic_graph(G):
        return None
    best: dict[str, int] = {u: units[u].get("estimated_loc", 0) for u in G.nodes}
    for u in nx.topological_sort(G):
        for v in G.successors(u):
            cand = best[u] + units[v].get("estimated_loc", 0)
            if cand > best[v]:
                best[v] = cand
    return max(best.values())


def validate_computed(
    doc: dict,
    units: dict[str, dict],
    dep_sets: dict[str, set[str]],
    blk_sets: dict[str, set[str]],
    allow_placeholders: bool,
) -> list[str]:
    errors: list[str] = []
    computed = doc.get("computed", {})

    actual_entry = {u for u in units if not dep_sets.get(u)}
    actual_leaf = {u for u in units if not blk_sets.get(u)}
    if "entry_points" in computed:
        declared = set(computed["entry_points"])
        for extra in sorted(declared - actual_entry):
            errors.append(
                f"computed.entry_points lists `{extra}` but its depends_on is non-empty"
            )
        for missing in sorted(actual_entry - declared):
            errors.append(
                f"computed.entry_points is missing `{missing}` (has empty depends_on)"
            )
    if "leaf_nodes" in computed:
        declared = set(computed["leaf_nodes"])
        for extra in sorted(declared - actual_leaf):
            errors.append(
                f"computed.leaf_nodes lists `{extra}` but its blocks is non-empty"
            )
        for missing in sorted(actual_leaf - declared):
            errors.append(
                f"computed.leaf_nodes is missing `{missing}` (has empty blocks)"
            )

    actual_layers = Counter(units[u].get("layer") for u in units if isinstance(units[u].get("layer"), int))
    mp = computed.get("max_parallel", {})
    for layer, count in actual_layers.items():
        key = f"layer{layer}"
        if key not in mp:
            errors.append(
                f"computed.max_parallel is missing `{key}` (actual count={count})"
            )
        elif mp[key] != count:
            errors.append(
                f"computed.max_parallel.{key}={mp[key]} but {count} unit(s) actually in layer {layer}"
            )
    for key, value in mp.items():
        if not key.startswith("layer"):
            continue
        try:
            layer = int(key[5:])
        except ValueError:
            errors.append(f"computed.max_parallel has malformed key `{key}`")
            continue
        if layer not in actual_layers:
            errors.append(
                f"computed.max_parallel.{key}={value} but no units are in layer {layer}"
            )

    loc = computed.get("loc_totals", {})
    actual_all = sum(units[u].get("estimated_loc", 0) for u in units)
    actual_by_tier: dict[int, int] = defaultdict(int)
    for uid, unit in units.items():
        tier = unit.get("tier")
        if tier in VALID_TIER:
            actual_by_tier[tier] += unit.get("estimated_loc", 0)
    if "all" in loc and loc["all"] != actual_all:
        errors.append(
            f"computed.loc_totals.all={loc['all']} but sum of estimated_loc={actual_all}"
        )
    for tier in (1, 2, 3):
        key = f"tier{tier}"
        if key in loc and loc[key] != actual_by_tier[tier]:
            errors.append(
                f"computed.loc_totals.{key}={loc[key]} but actual sum for tier-{tier} units={actual_by_tier[tier]}"
            )

    cp = computed.get("critical_path", [])
    cp_loc = computed.get("critical_path_loc")
    if cp:
        bad_ref = False
        for i, u in enumerate(cp):
            if u not in units:
                errors.append(
                    f"computed.critical_path[{i}]=`{u}` references unknown unit"
                )
                bad_ref = True
        if not bad_ref:
            for a, b in zip(cp, cp[1:]):
                if b not in blk_sets.get(a, set()):
                    errors.append(
                        f"computed.critical_path: {a} -> {b} is not a direct dependency edge"
                    )
            if dep_sets.get(cp[0]):
                errors.append(
                    f"computed.critical_path starts at `{cp[0]}` which is not an entry point"
                )
            if blk_sets.get(cp[-1]):
                errors.append(
                    f"computed.critical_path ends at `{cp[-1]}` which is not a leaf"
                )
            cp_actual = sum(units[u].get("estimated_loc", 0) for u in cp)
            if cp_loc is not None and cp_loc != cp_actual:
                errors.append(
                    f"computed.critical_path_loc={cp_loc} but sum along path={cp_actual}"
                )
            longest = longest_path_loc(units, blk_sets)
            if longest is not None and cp_actual < longest:
                errors.append(
                    f"computed.critical_path LOC={cp_actual} but a longer path exists with LOC={longest}"
                )
    elif cp_loc is not None:
        errors.append(
            f"computed.critical_path_loc={cp_loc} but critical_path is empty or missing"
        )

    for i, cg in enumerate(computed.get("conflict_groups", [])):
        cg_units = cg.get("units", [])
        for u in cg_units:
            if u not in units:
                errors.append(
                    f"computed.conflict_groups[{i}].units references unknown unit `{u}`"
                )
        for f in cg.get("files", []):
            if has_placeholder(f) and not allow_placeholders:
                errors.append(
                    f"computed.conflict_groups[{i}].files: placeholder not allowed: `{f}`"
                )
                continue
            if has_placeholder(f):
                continue
            for u in cg_units:
                if u not in units:
                    continue
                u_files = set(units[u].get("files_create", [])) | set(
                    units[u].get("files_modify", [])
                )
                if f not in u_files:
                    errors.append(
                        f"computed.conflict_groups[{i}]: unit `{u}` does not list `{f}` "
                        f"in files_create/files_modify"
                    )
    return errors


def validate_paths(
    units: dict[str, dict],
    repo_root: pathlib.Path | None,
    check_exists: bool,
    allow_placeholders: bool,
) -> list[str]:
    errors: list[str] = []
    for uid, unit in units.items():
        for field in ("files_create", "files_modify"):
            for path in unit.get(field, []):
                if has_placeholder(path):
                    if not allow_placeholders:
                        errors.append(
                            f"{uid}.{field}: placeholder not allowed: `{path}`"
                        )
                    continue
                if check_exists and field == "files_modify":
                    if repo_root is None:
                        errors.append("--check-paths-exist requires --repo-root")
                        return errors
                    if not (repo_root / path).exists():
                        errors.append(
                            f"{uid}.files_modify: path does not exist under repo root: `{path}`"
                        )
    return errors


def main() -> int:
    args = parse_args()
    dag_path = pathlib.Path(args.dag_file).resolve()
    repo_root = pathlib.Path(args.repo_root).resolve() if args.repo_root else None

    try:
        doc = load_toml(dag_path)
    except FileNotFoundError:
        print(f"error: file not found: {dag_path}", file=sys.stderr)
        return 2
    except tomllib.TOMLDecodeError as exc:
        print(f"error: invalid TOML: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    unit_errors, units = validate_units(doc)
    errors.extend(unit_errors)
    if units:
        edge_errors, dep_sets, blk_sets = validate_edges(units)
        errors.extend(edge_errors)
        errors.extend(detect_cycles(dep_sets))
        errors.extend(validate_artifacts(units))
        errors.extend(validate_layer_ordering(units, dep_sets))
        errors.extend(validate_meta(doc.get("meta", {}), units))
        errors.extend(
            validate_computed(doc, units, dep_sets, blk_sets, args.allow_placeholders)
        )
        errors.extend(
            validate_paths(units, repo_root, args.check_paths_exist, args.allow_placeholders)
        )

    if errors:
        print("IMPLEMENTATION DAG VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("IMPLEMENTATION DAG VALIDATION PASSED")
    print(f"- file: {dag_path}")
    print(f"- units: {len(units)}")
    layers = Counter(u.get("layer") for u in units.values())
    print(f"- layers: {dict(sorted(layers.items()))}")
    cp_loc = doc.get("computed", {}).get("critical_path_loc")
    if cp_loc is not None:
        print(f"- critical_path_loc: {cp_loc}")
    if args.check_paths_exist:
        print(f"- repo_root: {repo_root}")
        print("- path existence checks: enabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
