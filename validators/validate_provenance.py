#!/usr/bin/env python3
"""Validate optional `[provenance]` tables in DAG-TOML instance files.

Implements spec.md §11. For every TOML file passed in:

  * If the file has no `[provenance]` root table, exit silently (PASS).
  * If a `[provenance]` table is present, it MUST carry
    `source_path` (string), `source_sha256` (string of the form
    `sha256:<hex>`), and `source_bytes` (integer). The validator
    recomputes the SHA-256 of the file at `source_path` (resolved
    against --repo-root) and confirms it equals `source_sha256`,
    and confirms the byte length equals `source_bytes`. Any
    divergence is a hard failure.

The validator deliberately does NOT enforce the SHOULD-level fields
(`captured_at`, `extraction_method`, `source_description`); those
are advisory.

Usage:
    python3 validators/validate_provenance.py <file.toml> [<file.toml> ...] \
        --repo-root .
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py


HEX_PREFIX = "sha256:"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the optional [provenance] table in DAG-TOML files."
    )
    parser.add_argument("files", nargs="+", help="TOML files to inspect.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve `source_path` values.",
    )
    return parser.parse_args()


def sha256_of(path: pathlib.Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def validate_one(toml_path: pathlib.Path, repo_root: pathlib.Path) -> list[str]:
    try:
        with toml_path.open("rb") as handle:
            doc = tomllib.load(handle)
    except FileNotFoundError:
        return [f"{toml_path}: file not found"]
    except tomllib.TOMLDecodeError as exc:
        return [f"{toml_path}: invalid TOML: {exc}"]

    provenance = doc.get("provenance")
    if provenance is None:
        return []  # silently PASS
    if not isinstance(provenance, dict):
        return [f"{toml_path}: [provenance] must be a table, got {type(provenance).__name__}"]

    errors: list[str] = []

    source_path = provenance.get("source_path")
    source_sha256 = provenance.get("source_sha256")
    source_bytes = provenance.get("source_bytes")

    if not isinstance(source_path, str) or not source_path.strip():
        errors.append(f"{toml_path}: [provenance].source_path is required (string)")
    if not isinstance(source_sha256, str) or not source_sha256.startswith(HEX_PREFIX):
        errors.append(
            f"{toml_path}: [provenance].source_sha256 is required and must start with `{HEX_PREFIX}`"
        )
    if not isinstance(source_bytes, int):
        errors.append(f"{toml_path}: [provenance].source_bytes is required (integer)")

    if errors:
        return errors

    expected_digest = source_sha256[len(HEX_PREFIX):].strip().lower()
    if len(expected_digest) != 64 or any(c not in "0123456789abcdef" for c in expected_digest):
        return [f"{toml_path}: [provenance].source_sha256 hex digest is not 64 lowercase hex chars"]

    if pathlib.PurePath(source_path).is_absolute():
        return [
            f"{toml_path}: [provenance].source_path must be relative to repo root, "
            f"got absolute path {source_path!r}"
        ]
    resolved = (repo_root / source_path).resolve()
    repo_root_resolved = repo_root.resolve()
    try:
        resolved.relative_to(repo_root_resolved)
    except ValueError:
        return [
            f"{toml_path}: [provenance].source_path {source_path!r} resolves outside "
            f"repo root ({resolved} not under {repo_root_resolved}); "
            f"SPEC §11 requires source_path to point to a file under repo root"
        ]
    if not resolved.exists() or not resolved.is_file():
        return [f"{toml_path}: [provenance].source_path does not resolve to a file ({resolved})"]

    actual_digest, actual_bytes = sha256_of(resolved)
    if actual_digest != expected_digest:
        errors.append(
            f"{toml_path}: SHA-256 mismatch for {source_path}: "
            f"declared {expected_digest} vs actual {actual_digest}"
        )
    if actual_bytes != source_bytes:
        errors.append(
            f"{toml_path}: byte-length mismatch for {source_path}: "
            f"declared {source_bytes} vs actual {actual_bytes}"
        )
    return errors


def main() -> int:
    args = parse_args()
    repo_root = pathlib.Path(args.repo_root).resolve()

    all_errors: list[str] = []
    checked = 0
    with_provenance = 0
    for raw in args.files:
        path = pathlib.Path(raw).resolve()
        checked += 1
        try:
            with path.open("rb") as handle:
                doc = tomllib.load(handle)
        except (FileNotFoundError, tomllib.TOMLDecodeError) as exc:
            all_errors.append(f"{path}: {exc}")
            continue
        if isinstance(doc.get("provenance"), dict):
            with_provenance += 1
        all_errors.extend(validate_one(path, repo_root))

    if all_errors:
        print("PROVENANCE VALIDATION FAILED")
        print(f"- files inspected: {checked}")
        print(f"- files with [provenance]: {with_provenance}")
        for err in all_errors:
            print(f"- ERROR: {err}")
        return 1

    print("PROVENANCE VALIDATION PASSED")
    print(f"- files inspected: {checked}")
    print(f"- files with [provenance]: {with_provenance}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
