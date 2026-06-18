#!/usr/bin/env python3
"""Validate traceability code symbols with sqry.

This validator is intentionally narrower than `validate_traceability.py`.
It checks that concrete `[[code]]` entries in a traceability TOML file
resolve to AST symbols in source files for the language set where sqry is
the intended reference engine: Rust, Go, TypeScript, and Java.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py
from dataclasses import dataclass


SUPPORTED_LANGUAGES = {"rust", "go", "typescript", "java"}
LANGUAGE_ALIASES = {
    "golang": "go",
    "ts": "typescript",
}
EXTENSION_LANGUAGE = {
    ".rs": "rust",
    ".go": "go",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
}


@dataclass(frozen=True)
class SymbolRef:
    entity_id: str
    path: str
    symbol: str
    language: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that traceability [[code]] symbols exist in Rust, Go, "
            "TypeScript, or Java source files using sqry."
        )
    )
    parser.add_argument("traceability_file", help="Path to traceability.toml.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve [[code]].path values.",
    )
    parser.add_argument(
        "--languages",
        default="rust,go,typescript,java",
        help="Comma-separated language allow-list. Aliases: golang=go, ts=typescript.",
    )
    parser.add_argument(
        "--sqry-bin",
        default="sqry",
        help="sqry executable to invoke.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Also validate symbols declared on [[tests]] entries.",
    )
    parser.add_argument(
        "--strict-language-set",
        action="store_true",
        help="Fail when a symbol-bearing entry uses a language outside --languages.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report.",
    )
    return parser.parse_args()


def normalize_language(value: str) -> str:
    value = value.strip().lower()
    return LANGUAGE_ALIASES.get(value, value)


def parse_language_set(raw: str) -> set[str]:
    languages = {normalize_language(part) for part in raw.split(",") if part.strip()}
    unknown = sorted(languages - SUPPORTED_LANGUAGES)
    if unknown:
        raise ValueError(f"unsupported language(s): {', '.join(unknown)}")
    return languages


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def coerce_symbols(entry: dict) -> list[str]:
    symbols: list[str] = []
    raw_symbol = entry.get("symbol")
    raw_symbols = entry.get("symbols")
    if isinstance(raw_symbol, str):
        symbols.append(raw_symbol)
    elif raw_symbol is not None:
        symbols.append(str(raw_symbol))
    if isinstance(raw_symbols, list):
        symbols.extend(str(item) for item in raw_symbols)
    elif isinstance(raw_symbols, str):
        symbols.append(raw_symbols)
    return [symbol for symbol in symbols if symbol.strip()]


def infer_language(entry: dict, relpath: str) -> str | None:
    declared = entry.get("language") or entry.get("lang")
    if isinstance(declared, str) and declared.strip():
        return normalize_language(declared)
    return EXTENSION_LANGUAGE.get(pathlib.Path(relpath).suffix.lower())


def collect_symbol_refs(
    doc: dict,
    languages: set[str],
    include_tests: bool,
    strict_language_set: bool,
) -> tuple[list[SymbolRef], list[str], list[str]]:
    refs: list[SymbolRef] = []
    errors: list[str] = []
    skipped: list[str] = []
    sections = ["code"] + (["tests"] if include_tests else [])
    for section in sections:
        for entry in doc.get(section, []):
            entity_id = str(entry.get("id", f"{section}:<missing-id>"))
            relpath = entry.get("path")
            symbols = coerce_symbols(entry)
            if not symbols:
                continue
            if not isinstance(relpath, str) or not relpath.strip():
                errors.append(f"{entity_id}: symbol-bearing entry is missing `path`")
                continue
            language = infer_language(entry, relpath)
            if language is None:
                skipped.append(f"{entity_id}: skipped; cannot infer language from {relpath}")
                continue
            if language not in SUPPORTED_LANGUAGES:
                message = f"{entity_id}: unsupported language `{language}` for {relpath}"
                if strict_language_set:
                    errors.append(message)
                else:
                    skipped.append(message)
                continue
            if language not in languages:
                message = f"{entity_id}: language `{language}` excluded by --languages"
                if strict_language_set:
                    errors.append(message)
                else:
                    skipped.append(message)
                continue
            for symbol in symbols:
                refs.append(SymbolRef(entity_id, relpath, symbol, language))
    return refs, errors, skipped


def sqry_search(
    sqry_bin: str,
    repo_root: pathlib.Path,
    ref: SymbolRef,
) -> tuple[list[dict], str | None]:
    cmd = [
        sqry_bin,
        "--json",
        "--exact",
        "--lang",
        ref.language,
        "search",
        ref.symbol,
        str(repo_root),
    ]
    # Safe: cmd is built from validated TOML config; subprocess invoked
    # with an explicit argv list, never a shell string; no user input.
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)  # nosec B603  # noqa: S603
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        return [], detail
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return [], f"sqry returned invalid JSON: {exc}"
    wanted = (repo_root / ref.path).resolve()
    results = []
    for item in payload.get("results", []):
        raw_path = item.get("file_path") or item.get("metadata", {}).get("__raw_file_path")
        if not raw_path:
            continue
        try:
            candidate = pathlib.Path(raw_path).resolve()
        except OSError:
            continue
        if candidate == wanted:
            results.append(item)
    return results, None


def result_summary(ref: SymbolRef, matches: list[dict]) -> dict:
    return {
        "id": ref.entity_id,
        "path": ref.path,
        "symbol": ref.symbol,
        "language": ref.language,
        "matches": [
            {
                "qualified_name": match.get("qualified_name"),
                "kind": match.get("kind"),
                "line": match.get("start_line"),
            }
            for match in matches
        ],
    }


def main() -> int:
    args = parse_args()
    try:
        languages = parse_language_set(args.languages)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    traceability_path = pathlib.Path(args.traceability_file).resolve()
    repo_root = pathlib.Path(args.repo_root).resolve()
    sqry_bin = shutil.which(args.sqry_bin)
    if sqry_bin is None:
        print(f"error: sqry executable not found: {args.sqry_bin}", file=sys.stderr)
        return 2

    try:
        doc = load_toml(traceability_path)
    except FileNotFoundError:
        print(f"error: file not found: {traceability_path}", file=sys.stderr)
        return 2
    except tomllib.TOMLDecodeError as exc:
        print(f"error: invalid TOML: {exc}", file=sys.stderr)
        return 2

    refs, errors, skipped = collect_symbol_refs(
        doc,
        languages,
        include_tests=args.include_tests,
        strict_language_set=args.strict_language_set,
    )

    found: list[dict] = []
    missing: list[dict] = []
    for ref in refs:
        path = repo_root / ref.path
        if not path.exists():
            missing.append({**result_summary(ref, []), "error": "path does not exist"})
            continue
        matches, sqry_error = sqry_search(sqry_bin, repo_root, ref)
        if sqry_error is not None:
            missing.append({**result_summary(ref, []), "error": sqry_error})
        elif matches:
            found.append(result_summary(ref, matches))
        else:
            missing.append({**result_summary(ref, []), "error": "symbol not found in path"})

    report = {
        "traceability_file": str(traceability_path),
        "repo_root": str(repo_root),
        "languages": sorted(languages),
        "checked": len(refs),
        "found": found,
        "missing": missing,
        "skipped": skipped,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        if errors or missing:
            print("CODE SYMBOL VALIDATION FAILED")
        else:
            print("CODE SYMBOL VALIDATION PASSED")
        print(f"- traceability_file: {traceability_path}")
        print(f"- repo_root: {repo_root}")
        print(f"- languages: {', '.join(sorted(languages))}")
        print(f"- checked symbols: {len(refs)}")
        print(f"- matched symbols: {len(found)}")
        if skipped:
            print(f"- skipped entries: {len(skipped)}")
        for error in errors:
            print(f"- ERROR: {error}")
        for item in missing:
            print(
                f"- MISSING: {item['id']} `{item['symbol']}` "
                f"in {item['path']} ({item['language']}): {item['error']}"
            )
    return 1 if errors or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
