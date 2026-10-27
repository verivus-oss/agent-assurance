#!/usr/bin/env python3
"""Fail on a commit citation that a reader cannot resolve.

The repository's standing rule is that a claim naming a commit must name one
that can be resolved and checked. Prose under `docs/issues/` and messages in
`validators/` cite commits as evidence, and nothing verified that those
citations point at anything.

This scans issue prose and authored validator text for commit-shaped tokens.
Vendored parser source and unit fixtures are excluded because their numeric
literals are input data, not commit claims. Each detected token is checked for
reachability
from HEAD, and fails on any that is not unless
`validators/unresolvable-commit-citations.toml` records it with a reason.
See `resolves` for why the test is reachability and not object existence.

USAGE
    python3 validators/check_commit_citations.py [--repo-root .]
                                                 [--baseline <path>]

Exit 0 when every citation resolves or is recorded, 1 on an unrecorded
unresolvable citation or a stale baseline entry, 2 on an infrastructure error.

TOKEN RULE, and why it is what it is
------------------------------------
A candidate is 7 to 40 ASCII hex characters bounded by non-word
characters. Two details are load-bearing and were both found by measurement,
not by reasoning:

  * The boundary is a WORD boundary, not a hex boundary. The English word
    "feedback" opens with seven hex characters followed by a non-hex one, so a
    hex-only boundary matches that prefix and reports a phantom citation in
    every file containing the word. The bare prefix is deliberately not
    written out here: this file is inside the scanned tree and would otherwise
    cite itself.

  * Pure-digit tokens are NOT skipped. `9996826` is a real abbreviated SHA in
    this repository's prose and is also a valid decimal number. A rule that
    drops decimal-looking tokens misses the single most-cited unresolvable
    commit here.

  * Matching is case-insensitive and tokens are lowercased before they are
    resolved or looked up. git resolves a SHA case-insensitively, so an
    uppercase or GUI-pasted citation is a citation a reader can follow, and a
    lowercase-only rule lets it through. The cost is that an English word of
    seven or more letters drawn entirely from the hex alphabet becomes a
    candidate. None occurs in the scanned trees today, and `not_a_commit` is
    where one would be recorded if it ever did. Examples are deliberately not
    written out: this file is inside the scanned tree, and naming them is how
    the first draft of this rule broke.

UUIDs are excluded, and this is a PRECONDITION rather than a nicety. A UUID
is hyphen-separated hex and a hyphen is a non-word character, so every one of
its five segments satisfies the rule above on its own: the 8, 12 and any
letter-bearing 4-character group all match. A single gateway job id pasted
into a scanned file would therefore report two or three phantom citations.
The scanned trees contain no UUID today, but that is a fact about their
current contents, not a guarantee, so the rule excludes any match falling
inside a UUID rather than relying on the population staying clean. This is
also what would have to hold before `docs/reviews/` could be scanned: it
carries several hundred gateway job ids, and most of what a naive run flags
there is a UUID segment rather than a citation.
The exclusion cannot create a new word boundary. Hex text joined directly
to a UUID is one word in the original source, not a separate commit citation.

A recorded entry permits a SHA only at the sites its `cited` list names. The
same SHA appearing anywhere else is a NEW unresolvable citation and fails,
which is the property the gate exists to enforce. That also makes `cited`
load-bearing rather than annotation.

Within the governed source population, tokens that match the shape but are
not citations (a hex alphabet literal, for instance) are recorded in the
baseline's `not_a_commit` table with a reason. Vendored parser source and the
two scanner unit fixtures are outside that population because their literals
are test data.
"""

from __future__ import annotations

import pathlib
import shutil
# Git calls below use a resolved executable and argument lists without a shell.
import subprocess  # nosec B404
import sys
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _toml11 as tomllib  # noqa: E402

SCAN_DIRS = ("docs/issues", "validators")
# Absolute path, resolved once. A bare "git" is a partial executable path
# (ruff S607) and would also let PATH decide which binary runs.
GIT = shutil.which("git")

def ascii_word(char: str) -> bool:
    return char == "_" or "0" <= char <= "9" or "a" <= char <= "z" or "A" <= char <= "Z"


def ascii_hex(char: str) -> bool:
    return "0" <= char <= "9" or "a" <= char <= "f" or "A" <= char <= "F"


def uuid_spans(line: str) -> list[tuple[int, int]]:
    """Identify UUID shapes so their segments are not read as commits."""
    spans: list[tuple[int, int]] = []
    widths = (8, 4, 4, 4, 12)
    for start in range(max(0, len(line) - 35)):
        cursor = start
        for index, width in enumerate(widths):
            if not all(ascii_hex(char) for char in line[cursor:cursor + width]) or len(line[cursor:cursor + width]) != width:
                break
            cursor += width
            if index < len(widths) - 1:
                if line[cursor:cursor + 1] != "-":
                    break
                cursor += 1
        else:
            spans.append((start, cursor))
    return spans


def commit_tokens(line: str) -> set[str]:
    """Read complete ASCII words and retain only seven to forty hex digits."""
    masked = [False] * len(line)
    for start, end in uuid_spans(line):
        for pos in range(start, end):
            masked[pos] = True
    tokens: set[str] = set()
    pos = 0
    while pos < len(line):
        if not ascii_word(line[pos]):
            pos += 1
            continue
        end = pos + 1
        while end < len(line) and ascii_word(line[end]):
            end += 1
        word = line[pos:end]
        if 7 <= len(word) <= 40 and all(ascii_hex(char) for char in word) and not any(masked[pos:end]):
            tokens.add(word.lower())
        pos = end
    return tokens


def governed_file(path: pathlib.Path, root: pathlib.Path) -> bool:
    """Vendored parser source and unit fixtures do not make commit claims."""
    rel = path.relative_to(root)
    if rel.parts[:2] == ("validators", "_toml11_vendor") and rel.name != "README.md":
        return False
    return rel.as_posix() not in {
        "validators/test_toml11_scanner.py",
        "validators/test_commit_citations.py",
    }


def parse_args() -> SimpleNamespace:
    repo_root = "."
    baseline = "validators/unresolvable-commit-citations.toml"
    args = iter(sys.argv[1:])
    for item in args:
        if item in ("-h", "--help"):
            print("usage: check_commit_citations.py [--repo-root PATH] [--baseline PATH]")
            raise SystemExit(0)
        if item == "--repo-root":
            repo_root = next(args, "")
            if not repo_root or repo_root.startswith("-"):
                print("error: --repo-root requires a path", file=sys.stderr)
                raise SystemExit(2)
        elif item.startswith("--repo-root="):
            repo_root = item.partition("=")[2]
            if not repo_root:
                print("error: --repo-root requires a path", file=sys.stderr)
                raise SystemExit(2)
        elif item == "--baseline":
            baseline = next(args, "")
            if not baseline or baseline.startswith("-"):
                print("error: --baseline requires a path", file=sys.stderr)
                raise SystemExit(2)
        elif item.startswith("--baseline="):
            baseline = item.partition("=")[2]
            if not baseline:
                print("error: --baseline requires a path", file=sys.stderr)
                raise SystemExit(2)
        else:
            print(f"error: unknown option {item}", file=sys.stderr)
            raise SystemExit(2)
    return SimpleNamespace(repo_root=repo_root, baseline=baseline)


class Infrastructure(Exception):
    """The check could not be run at all, as distinct from finding a defect."""


def tracked_files(root: pathlib.Path, dirs: tuple[str, ...]) -> list[pathlib.Path]:
    # Safe: fixed absolute binary path, list-args invocation, no shell.
    proc = subprocess.run(  # nosec B603  # noqa: S603
        [GIT, "ls-files", "-z", *dirs],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        # Most often: --repo-root does not name a git repository. Report it
        # as an infrastructure error rather than letting a traceback out,
        # so it is never mistaken for "scanned the tree and found nothing".
        raise Infrastructure(
            f"git ls-files failed under {root} (exit {proc.returncode}): "
            + (proc.stderr.strip() or "no stderr")
        )
    return [root / p for p in proc.stdout.split("\0") if p]


def is_shallow(root: pathlib.Path) -> bool:
    """True when the clone lacks history, which makes every lookup a lie.

    A shallow checkout resolves almost nothing, so the check would report
    every citation as broken. That is a false report, not a finding, and it
    is the exact failure this gate exists to prevent elsewhere.
    """
    # Safe: fixed absolute binary path, list-args invocation, no shell.
    proc = subprocess.run(  # nosec B603  # noqa: S603
        [GIT, "rev-parse", "--is-shallow-repository"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    return proc.stdout.strip() == "true"


def resolves(root: pathlib.Path, sha: str) -> bool:
    """True when a reader of this history can follow the citation.

    The test is REACHABILITY FROM HEAD, not object existence. `git rev-parse`
    reads the object store, and a working clone can hold objects that no ref
    reaches: commits from a branch that was squash-merged and deleted, or
    fetched and later pruned. Those resolve for whoever happens to hold them
    and for nobody else, so a rev-parse check reports a citation as good on
    the author's machine and bad in CI. That is not a hypothetical; it is how
    ISS-005's two citations were first recorded here as resolving.

    Reachability from HEAD gives the same answer everywhere, because HEAD is
    the history the document actually ships in: this branch locally, and the
    pull request's merge commit in CI. A commit that is not an ancestor of
    HEAD is not in the history a reader receives, whatever a local object
    store still holds.
    """
    # Safe: fixed absolute binary path, list-args invocation, no shell.
    # Exit 0 = ancestor, 1 = not, 128 = no such object. Only 0 is resolvable.
    return subprocess.run(  # nosec B603  # noqa: S603
        [GIT, "merge-base", "--is-ancestor", f"{sha}^{{commit}}", "HEAD"],
        cwd=root, capture_output=True,
    ).returncode == 0


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.repo_root).resolve()

    if GIT is None:
        print("error: git not found on PATH; this check resolves citations "
              "against the repository and cannot run without it.",
              file=sys.stderr)
        return 2

    if is_shallow(root):
        print(
            "error: shallow clone. Every citation would report as "
            "unresolvable because the commits are absent, not because the "
            "citations are wrong. Check out full history "
            "(actions/checkout with fetch-depth: 0) and run again.",
            file=sys.stderr,
        )
        return 2

    baseline_path = root / args.baseline
    if not baseline_path.is_file():
        print(f"error: missing baseline {baseline_path}", file=sys.stderr)
        return 2
    baseline = tomllib.loads(baseline_path.read_bytes().decode("utf-8"))
    recorded = {
        e["sha"].lower(): set(e.get("cited", []))
        for e in baseline.get("unresolvable", [])
    }
    ignored = {e["token"].lower() for e in baseline.get("not_a_commit", [])}

    try:
        tracked = tracked_files(root, SCAN_DIRS)
    except Infrastructure as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    found: dict[str, set[str]] = {}
    scanned = 0
    undecodable: list[str] = []
    for path in tracked:
        if path == baseline_path or not governed_file(path, root):
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError) as exc:
            undecodable.append(f"{path.relative_to(root).as_posix()}: {exc.__class__.__name__}")
            continue
        scanned += 1
        rel = path.relative_to(root).as_posix()
        for line in text.splitlines():
            for token in commit_tokens(line):
                found.setdefault(token, set()).add(rel)

    if scanned == 0:
        print(
            f"error: scanned 0 files under {', '.join(SCAN_DIRS)} in {root}.\n"
            "A check that reads nothing reports nothing; refusing to pass.",
            file=sys.stderr,
        )
        return 2
    if undecodable:
        print("error: tracked files under the scanned trees could not be read:",
              file=sys.stderr)
        for u in undecodable:
            print(f"  {u}", file=sys.stderr)
        print("A citation in an unreadable file would be invisible to this check.",
              file=sys.stderr)
        return 2
    unresolvable = {
        tok: sites for tok, sites in found.items()
        if tok not in ignored and not resolves(root, tok)
    }
    unrecorded: dict[str, set[str]] = {}
    for tok, sites in unresolvable.items():
        allowed = recorded.get(tok)
        if allowed is None:
            unrecorded[tok] = sites
            continue
        new_sites = sites - allowed
        if new_sites:
            unrecorded[tok] = new_sites
    stale = sorted(set(recorded) - set(unresolvable))
    unused_ignores = sorted(ignored - set(found))

    print("commit-citation check")
    print(f"  scanned                 {', '.join(SCAN_DIRS)}  ({scanned} files)")
    print(f"  commit-shaped tokens    {len(found)}")
    print(f"  resolve                 {len(found) - len(unresolvable) - len(ignored & set(found))}")
    print(f"  recorded unresolvable   {len(unresolvable) - len(unrecorded)}")
    print(f"  not-a-commit ignores    {len(ignored & set(found))}")

    fail = False
    if unrecorded:
        fail = True
        print("\nFAIL: commit citations that do not resolve and are not recorded:",
              file=sys.stderr)
        for tok, sites in sorted(unrecorded.items()):
            ordered = sorted(sites)
            print(f"  {tok}  cited in {', '.join(ordered[:4])}"
                  + (f" (+{len(ordered) - 4} more files)" if len(ordered) > 4 else ""),
                  file=sys.stderr)
        print(
            "\nEither cite a commit this repository carries, or record the token in\n"
            f"{args.baseline} with the reason it cannot be resolved.",
            file=sys.stderr,
        )

    if stale:
        fail = True
        print("\nFAIL: baseline records tokens that now resolve or are no longer cited:",
              file=sys.stderr)
        for tok in stale:
            print(f"  {tok}", file=sys.stderr)
        print("Remove them from the baseline; it ratchets down, not up.", file=sys.stderr)

    if unused_ignores:
        fail = True
        print("\nFAIL: not_a_commit entries that no longer appear in the scanned trees:",
              file=sys.stderr)
        for tok in unused_ignores:
            print(f"  {tok}", file=sys.stderr)

    if fail:
        return 1

    print("\nOK: every commit citation resolves or is recorded with a reason")
    return 0


if __name__ == "__main__":
    sys.exit(main())
