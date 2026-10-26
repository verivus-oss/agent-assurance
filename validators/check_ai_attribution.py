#!/usr/bin/env python3
"""Reject AI attribution in introduced commit messages or identities."""

import subprocess
import shutil
import sys


def message_has_stamp(message: str) -> bool:
    for line in message.splitlines():
        folded = line.casefold()
        trailer = folded.find("co-authored-by:")
        if trailer >= 0 and any(name in folded[trailer:] for name in ("claude", "anthropic")):
            return True
        generated = folded.find("generated with")
        if generated >= 0 and "claude" in folded[generated:]:
            return True
    return False


def identity_has_stamp(identity: str) -> bool:
    folded = identity.casefold()
    return "claude" in folded or "anthropic" in folded


def git_log(format_string: str, revisions: list[str]) -> str:
    if format_string not in ("%H%x00%B%x00%x00", "%H%x00%an%x00%ae%x00%cn%x00%ce%x00%x00"):
        raise ValueError("unapproved Git log format")
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git executable is required")
    if not revisions or any(not valid_revision(value) for value in revisions):
        raise ValueError("invalid commit revision or range")
    result = subprocess.run(  # nosec B603  # noqa: S603
        [git, "log", "--format=" + format_string, *revisions],
        check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError("git log failed: " + result.stderr.strip())
    return result.stdout


def valid_revision(value: str) -> bool:
    def is_sha(text: str) -> bool:
        return len(text) == 40 and all(char in "0123456789abcdefABCDEF" for char in text)

    def is_remote_ref(text: str) -> bool:
        prefix = "refs/remotes/origin/"
        if not text.startswith(prefix):
            return False
        branch = text[len(prefix):]
        return (bool(branch) and not branch.startswith(("-", ".", "/"))
                and not branch.endswith((".", "/"))
                and ".." not in branch and "//" not in branch
                and all(char.isascii() and (char.isalnum() or char in "._/-") for char in branch))

    first, separator, second = value.partition("..")
    return (is_sha(first) or is_remote_ref(first)) and (not separator or is_sha(second))


def main(revisions: list[str]) -> int:
    if not revisions:
        raise ValueError("a commit range is required")
    messages = git_log("%H%x00%B%x00%x00", revisions)
    identities = git_log("%H%x00%an%x00%ae%x00%cn%x00%ce%x00%x00", revisions)
    message_records = [record.strip("\n") for record in messages.split("\0\0") if record.strip("\n")]
    identity_records = [record.strip("\n") for record in identities.split("\0\0") if record.strip("\n")]
    if len(message_records) != len(identity_records):
        raise RuntimeError("commit message and identity populations differ")
    if not message_records:
        raise RuntimeError("no introduced commits to inspect")
    failures = []
    for message_record, identity_record in zip(message_records, identity_records, strict=True):
        message_fields = message_record.split("\0")
        identity_fields = identity_record.split("\0")
        if len(message_fields) != 2 or len(identity_fields) != 5 or message_fields[0] != identity_fields[0]:
            raise RuntimeError("commit record shape or identity differs")
        commit = message_fields[0]
        if message_has_stamp(message_fields[1]):
            failures.append((commit, "message"))
        if identity_has_stamp(" ".join(identity_fields[1:])):
            failures.append((commit, "identity"))
    for commit, reason in failures:
        print("FAIL: AI attribution in commit " + commit + " " + reason)
    if failures:
        return 1
    print("OK: checked " + str(len(message_records)) + " introduced commits for attribution stamps")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (RuntimeError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
