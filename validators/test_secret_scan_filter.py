"""Keep the historical public literal exception exact and fail closed."""

from contextlib import redirect_stderr
from io import StringIO

from _test_require import require
from check_secret_scan import (
    KNOWN_COMMITS, PUBLIC_HEX_FILE, PUBLIC_HEX_RULE,
    added_line_commits, check_findings, check_scan_population, known_public_literal, scanned_count,
)


def test_exception() -> None:
    public = "".join(chr(code) for code in range(ord("0"), ord("9") + 1))
    public += "".join(chr(code) for code in range(ord("a"), ord("f") + 1))
    commit = sorted(KNOWN_COMMITS)[0]
    record = {"Secret": public, "RuleID": PUBLIC_HEX_RULE,
              "File": PUBLIC_HEX_FILE, "Commit": commit}
    require(known_public_literal(record))
    check_findings([record], {commit})
    for field, replacement in (
        ("Secret", public + "x"),
        ("RuleID", "other-rule"),
        ("File", "validators/other.toml"),
        ("Commit", "a" * 40),
    ):
        changed = record | {field: replacement}
        require(not known_public_literal(changed), "public exception widened")
        output = StringIO()
        try:
            with redirect_stderr(output):
                check_findings([changed], {commit})
        except RuntimeError:
            require("unapproved finding" in output.getvalue())
        else:
            raise AssertionError("unapproved finding was accepted")
    try:
        check_findings([], {commit})
    except RuntimeError:
        pass
    else:
        raise AssertionError("absent scanner control was accepted")


def test_scan_count() -> None:
    require(scanned_count("INF 12 commits scanned.\n") == 12)
    for output in ("", "INF scanned bytes", "INF 12 commits scanned.\nINF 12 commits scanned."):
        try:
            scanned_count(output)
        except RuntimeError:
            pass
        else:
            raise AssertionError("missing or duplicate scan count was accepted")

    head = {"head", "merge", "known"}
    all_commits = head | {"branch"}
    patches = {"head", "known"}
    check_scan_population(2, all_commits, head, {"known"}, patches)
    for count, reachable, ancestry, expected, patch_commits in (
        (0, all_commits, head, {"known"}, patches),
        (1, all_commits, head, {"known"}, patches),
        (3, all_commits, head, {"known"}, patches),
        (2, all_commits, head, {"branch"}, patches),
        (2, all_commits, set(), {"known"}, patches),
        (2, all_commits, head | {"unknown"}, {"known"}, patches),
        (2, all_commits, head, {"known"}, patches | {"unknown"}),
    ):
        try:
            check_scan_population(count, reachable, ancestry, expected, patch_commits)
        except RuntimeError:
            pass
        else:
            raise AssertionError("invalid scan population was accepted")

    first, second = "a" * 40, "b" * 40
    numstat = (b"SCAN-COMMIT:" + first.encode() + b"\0\n2\t0\tfile\0"
               + b"SCAN-COMMIT:" + second.encode() + b"\0\n0\t2\tother\0")
    require(added_line_commits(numstat, {first, second}) == {first})
    rename = (b"SCAN-COMMIT:" + first.encode() + b"\0\n1\t1\t\0"
              + b"SCAN-COMMIT:" + second.encode() + b"\0new-name\0")
    require(added_line_commits(rename, {first, second}) == {first})
    for broken in (
        b"SCAN-COMMIT:short\0\n1\t0\tfile\0",
        b"SCAN-COMMIT:" + first.encode() + b"\0\nnot-a-count\t0\tfile\0",
        b"SCAN-COMMIT:" + first.encode() + b"\0\n0\t1\tfile\0",
        b"\n1\t0\tfile\0",
    ):
        try:
            added_line_commits(broken, {first})
        except RuntimeError:
            pass
        else:
            raise AssertionError("invalid Git numstat record was accepted")


if __name__ == "__main__":
    test_exception()
    test_scan_count()
    print("secret scan filter: exact accepted and rejected controls passed")
