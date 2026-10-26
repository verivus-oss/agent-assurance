#!/usr/bin/env python3
"""Select link checker inputs with exact file and host exceptions."""

from pathlib import Path
import shutil
import subprocess
import sys

import _literal_args as argparse


SKIP_DIRECTORIES = frozenset({
    "docs/reviews", "docs/research", "docs/claim_analysis",
    ".local", "reference/database/rdf", "site",
})
SKIP_HOSTS = frozenset({"toml.io", "www.fco-im.nl"})


def included_source(source: str, tracked: set[str]) -> bool:
    if not source.startswith("./"):
        raise ValueError("link extractor returned a source outside the checkout")
    path = source[2:]
    if path not in tracked:
        raise ValueError("link extractor returned an untracked source: " + path)
    return eligible_path(path)


def eligible_path(path: str) -> bool:
    if any(segment.startswith(".") for segment in path.split("/")):
        return False
    return not any(path == directory or path.startswith(directory + "/")
                   for directory in SKIP_DIRECTORIES)


def split_record(row: str) -> tuple[str, str]:
    if row.endswith(" [excluded]"):
        row = row.removesuffix(" [excluded]")
    target, marker, source = row.rpartition(" (")
    if not marker or not source.endswith(")") or not target:
        raise ValueError("link extractor returned a malformed record")
    return target, source[:-1]


def host_of(url: str) -> str:
    _, marker, rest = url.partition("://")
    if not marker:
        raise ValueError("link has no scheme delimiter")
    authority = rest.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if not authority or "@" in authority or "[" in authority or "]" in authority:
        raise ValueError("link authority requires manual review")
    host, _, port = authority.partition(":")
    if port and not port.isdecimal():
        raise ValueError("link port is invalid")
    return host.casefold()


def select_links(rows: list[str], tracked: set[str]) -> tuple[list[str], set[str]]:
    candidates: set[str] = set()
    exceptions: set[str] = set()
    scoped_http = 0
    for row in rows:
        target, source = split_record(row)
        if not included_source(source, tracked):
            continue
        if target.startswith(("file://", "mailto:")):
            continue
        if not target.startswith(("http://", "https://")):
            raise ValueError("link extractor returned an unexpected scheme")
        scoped_http += 1
        if host_of(target) in SKIP_HOSTS:
            exceptions.add(target)
        else:
            candidates.add(target)
    if scoped_http < 20 or len(candidates) < 10:
        raise ValueError("link population is unexpectedly small")
    if {host_of(url) for url in exceptions} != SKIP_HOSTS:
        raise ValueError("the exact external-link exceptions changed")
    return sorted(candidates), exceptions


def tracked_files() -> set[str]:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git is required to bound the link source population")
    result = subprocess.run(  # nosec B603  # noqa: S603
        [git, "ls-files", "-z"], capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError("cannot enumerate tracked link sources")
    tracked = set(result.stdout.decode().strip("\0").split("\0"))
    if len(tracked) < 100:
        raise RuntimeError("tracked source population is unexpectedly small")
    return tracked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    tracked = tracked_files()
    rows = Path(args.dump).read_text().splitlines()
    if not rows:
        raise RuntimeError("link extractor returned no links")
    candidates, exceptions = select_links(rows, tracked)
    output = Path(args.output)
    output.write_text("".join(url + "\n" for url in candidates))
    if len(output.read_text().splitlines()) != len(candidates):
        raise RuntimeError("prepared link input population differs from selected URLs")
    print(f"link scan prepared {len(candidates)} distinct URLs; "
          f"{len(exceptions)} exact unstable URLs recorded")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
