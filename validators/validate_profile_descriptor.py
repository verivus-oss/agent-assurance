#!/usr/bin/env python3
"""Validate a DAG-TOML profile-descriptor file.

A profile-descriptor is a TOML document whose `[meta].template_kind`
is `"profile-descriptor"`. It documents a profile per spec.md §6.1
and is the only artifact that declares profile inheritance
(`[profile].extends`) and namespacing posture
(`[profile].namespace`) in machine-readable form.

This validator enforces the hard invariants INV01..INV05 listed in
`core/profile-descriptor-kind.toml`:

  INV01 — namespace partition consistency:
          namespace == "spec.reserved"   iff   name matches ^[a-z][a-z0-9-]*$
          (unprefixed kebab-case)
          otherwise namespace MUST be a strict reverse-DNS prefix of name
          (matches ^[a-z][a-z0-9-]*(\\.[a-z][a-z0-9-]*)+$).
  INV02 — `extends` is acyclic.
  INV03 — every entry of `extends` resolves to a loaded profile-descriptor.
  INV04 — `ontology` points at an existing file with
          `[meta].template_kind = "ontology"`.
  INV05 — every entry of `contained_kinds` resolves to a `*-kind.toml`
          under repo root whose `[meta].describes_kind` matches the entry.

The validator loads every profile-descriptor it finds under
`profiles/*/PROFILE.toml` (plus any path passed on the command line)
so the `extends` resolution can succeed across spec-reserved and
locally-shipped non-spec-reserved profiles.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import tomllib


UNPREFIXED_RE = re.compile(r"^[a-z][a-z0-9-]*$")
REVERSE_DNS_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+$")

REQUIRED_PROFILE_FIELDS = (
    "name",
    "namespace",
    "owner",
    "license",
    "extends",
    "ontology",
    "contained_kinds",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a DAG-TOML profile-descriptor file.",
    )
    parser.add_argument("files", nargs="+", help="profile descriptor TOML files")
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Repository root (used to resolve ontology + contained-kinds paths).",
    )
    return parser.parse_args()


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def discover_descriptors(repo_root: pathlib.Path) -> dict[str, tuple[pathlib.Path, dict]]:
    """Discover every profile-descriptor under `profiles/*/PROFILE.toml`."""
    found: dict[str, tuple[pathlib.Path, dict]] = {}
    profiles_dir = repo_root / "profiles"
    if not profiles_dir.is_dir():
        return found
    for entry in sorted(profiles_dir.iterdir()):
        candidate = entry / "PROFILE.toml"
        if not candidate.is_file():
            continue
        try:
            doc = load_toml(candidate)
        except tomllib.TOMLDecodeError:
            continue
        meta = doc.get("meta") or {}
        if meta.get("template_kind") != "profile-descriptor":
            continue
        profile = doc.get("profile") or {}
        name = profile.get("name")
        if isinstance(name, str):
            found[name] = (candidate, doc)
    return found


def check_namespace_partition(name: str, namespace: str) -> list[str]:
    errors: list[str] = []
    is_unprefixed = bool(UNPREFIXED_RE.match(name))
    is_reverse_dns = bool(REVERSE_DNS_RE.match(name))
    if not (is_unprefixed or is_reverse_dns):
        errors.append(
            f"[profile].name `{name}` does not match the SPEC §2.5 namespacing "
            f"partition (must be unprefixed kebab-case for spec-reserved profiles, "
            f"or a reverse-DNS name for non-spec-reserved profiles)"
        )
        return errors
    if is_unprefixed:
        if namespace != "spec.reserved":
            errors.append(
                f"[profile].namespace `{namespace}` is inconsistent with "
                f"unprefixed name `{name}` (SPEC §2.5: unprefixed names are "
                f"reserved for spec-reserved profiles, which MUST declare "
                f"`namespace = \"spec.reserved\"`)"
            )
    else:
        # reverse-DNS
        if namespace == "spec.reserved":
            errors.append(
                f"[profile].namespace = \"spec.reserved\" is not permitted for "
                f"reverse-DNS name `{name}` (SPEC §2.5: `spec.reserved` is for "
                f"spec-reserved unprefixed profiles)"
            )
        elif not name.startswith(namespace + "."):
            errors.append(
                f"[profile].namespace `{namespace}` is not a strict reverse-DNS "
                f"prefix of name `{name}` (SPEC §2.5)"
            )
    return errors


def check_extends_acyclic(
    name: str,
    descriptors: dict[str, tuple[pathlib.Path, dict]],
) -> list[str]:
    """Walk the extends graph from `name` looking for a cycle."""
    errors: list[str] = []
    visiting: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in path:
            cycle = " -> ".join(path[path.index(node):] + [node])
            errors.append(f"`extends` graph contains a cycle: {cycle}")
            return
        if node in visiting:
            return
        visiting.add(node)
        if node not in descriptors:
            return  # INV03 handled separately
        _, doc = descriptors[node]
        profile = doc.get("profile") or {}
        for child in profile.get("extends", []) or []:
            if isinstance(child, str):
                visit(child, path + [node])

    visit(name, [])
    return errors


def validate_one(
    descriptor_path: pathlib.Path,
    repo_root: pathlib.Path,
    descriptors: dict[str, tuple[pathlib.Path, dict]],
) -> list[str]:
    errors: list[str] = []
    try:
        doc = load_toml(descriptor_path)
    except FileNotFoundError:
        return [f"{descriptor_path}: file not found"]
    except tomllib.TOMLDecodeError as exc:
        return [f"{descriptor_path}: invalid TOML: {exc}"]

    meta = doc.get("meta")
    if not isinstance(meta, dict):
        return [f"{descriptor_path}: missing required `[meta]` table"]
    if meta.get("template_kind") != "profile-descriptor":
        return [
            f"{descriptor_path}: meta.template_kind must equal "
            f"`\"profile-descriptor\"` (got {meta.get('template_kind')!r})"
        ]

    profile = doc.get("profile")
    if not isinstance(profile, dict):
        return [f"{descriptor_path}: missing required `[profile]` table"]

    for field in REQUIRED_PROFILE_FIELDS:
        if field not in profile:
            errors.append(f"{descriptor_path}: [profile].{field} is required")

    if errors:
        return errors

    name = profile["name"]
    namespace = profile["namespace"]
    extends = profile["extends"]
    ontology = profile["ontology"]
    contained_kinds = profile["contained_kinds"]

    if not isinstance(name, str) or not name:
        errors.append(f"{descriptor_path}: [profile].name must be a non-empty string")
    if not isinstance(namespace, str) or not namespace:
        errors.append(
            f"{descriptor_path}: [profile].namespace must be a non-empty string"
        )
    if not isinstance(extends, list):
        errors.append(f"{descriptor_path}: [profile].extends must be an array")
    if not isinstance(ontology, str) or not ontology:
        errors.append(
            f"{descriptor_path}: [profile].ontology must be a non-empty string"
        )
    if not isinstance(contained_kinds, list):
        errors.append(
            f"{descriptor_path}: [profile].contained_kinds must be an array"
        )
    if errors:
        return errors

    # INV01 — namespace partition consistency
    errors.extend(check_namespace_partition(name, namespace))

    # INV02 — extends is acyclic
    errors.extend(check_extends_acyclic(name, descriptors))

    # INV03 — every extends entry resolves to a loaded descriptor
    for entry in extends:
        if not isinstance(entry, str):
            errors.append(
                f"{descriptor_path}: [profile].extends entries must be strings"
            )
            continue
        if entry not in descriptors:
            errors.append(
                f"{descriptor_path}: [profile].extends entry `{entry}` does not "
                f"resolve to a loaded profile-descriptor (looked under "
                f"`profiles/*/PROFILE.toml` and the explicit --files set)"
            )

    # INV04 — ontology path exists and is an ontology
    ontology_path = (repo_root / ontology).resolve()
    if not ontology_path.exists() or not ontology_path.is_file():
        errors.append(
            f"{descriptor_path}: [profile].ontology path does not resolve to a "
            f"file ({ontology_path})"
        )
    else:
        try:
            ontology_doc = load_toml(ontology_path)
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"{descriptor_path}: ontology parse failure: {exc}")
        else:
            ont_meta = ontology_doc.get("meta") or {}
            if ont_meta.get("template_kind") != "ontology":
                errors.append(
                    f"{descriptor_path}: [profile].ontology ({ontology}) does "
                    f"not declare `template_kind = \"ontology\"`"
                )

    # INV05 — every contained_kinds entry resolves to a *-kind.toml
    for slug in contained_kinds:
        if not isinstance(slug, str) or not slug:
            errors.append(
                f"{descriptor_path}: [profile].contained_kinds entries must be "
                f"non-empty strings"
            )
            continue
        candidates = _kind_descriptor_candidates(repo_root, slug, profile_name=name)
        matched = None
        for candidate in candidates:
            if not candidate.exists():
                continue
            try:
                kd_doc = load_toml(candidate)
            except tomllib.TOMLDecodeError:
                continue
            kd_meta = kd_doc.get("meta") or {}
            if (
                kd_meta.get("template_kind") == "kind-descriptor"
                and kd_meta.get("describes_kind") == slug
            ):
                matched = candidate
                break
        if matched is None:
            errors.append(
                f"{descriptor_path}: [profile].contained_kinds entry `{slug}` "
                f"does not resolve to a `*-kind.toml` whose "
                f"`[meta].describes_kind` matches the entry "
                f"(searched: {[str(c) for c in candidates]})"
            )

    return errors


def _kind_descriptor_candidates(
    repo_root: pathlib.Path, slug: str, profile_name: str
) -> list[pathlib.Path]:
    """Return the conventional locations a kind-descriptor for `slug`
    may live under. Searches profile dir, core/, and any other profile
    dirs as a fallback."""
    candidates = [
        repo_root / "profiles" / profile_name / f"{slug}-kind.toml",
        repo_root / "core" / f"{slug}-kind.toml",
    ]
    profiles_dir = repo_root / "profiles"
    if profiles_dir.is_dir():
        for entry in sorted(profiles_dir.iterdir()):
            if not entry.is_dir():
                continue
            candidates.append(entry / f"{slug}-kind.toml")
    # dedupe while preserving order
    seen: set[pathlib.Path] = set()
    deduped: list[pathlib.Path] = []
    for c in candidates:
        rc = c.resolve()
        if rc in seen:
            continue
        seen.add(rc)
        deduped.append(c)
    return deduped


def main() -> int:
    args = parse_args()
    repo_root = pathlib.Path(args.repo_root).resolve()
    descriptors = discover_descriptors(repo_root)

    # Make sure any descriptor passed explicitly on the CLI is also in
    # the discovered set, so `extends` referencing it resolves even if
    # the file lives outside `profiles/*/PROFILE.toml`.
    for raw in args.files:
        path = pathlib.Path(raw).resolve()
        try:
            doc = load_toml(path)
        except (FileNotFoundError, tomllib.TOMLDecodeError):
            continue
        meta = doc.get("meta") or {}
        if meta.get("template_kind") != "profile-descriptor":
            continue
        profile = doc.get("profile") or {}
        name = profile.get("name")
        if isinstance(name, str) and name not in descriptors:
            descriptors[name] = (path, doc)

    all_errors: list[str] = []
    for raw in args.files:
        path = pathlib.Path(raw).resolve()
        errs = validate_one(path, repo_root, descriptors)
        if errs:
            all_errors.append(f"--- {path} ---")
            all_errors.extend(errs)

    if all_errors:
        print("PROFILE DESCRIPTOR VALIDATION FAILED")
        for line in all_errors:
            print(f"- {line}")
        return 1

    print("PROFILE DESCRIPTOR VALIDATION PASSED")
    print(f"- files validated: {len(args.files)}")
    print(f"- profiles in resolution set: {len(descriptors)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
