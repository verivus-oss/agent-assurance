"""Keep the historical public literal exception exact and fail closed."""

from contextlib import redirect_stderr
from io import StringIO

from _test_require import require
from check_secret_scan import (
    KNOWN_COMMITS, PUBLIC_HEX_FILE, PUBLIC_HEX_RULE,
    check_findings, known_public_literal, scanned_count,
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


if __name__ == "__main__":
    test_exception()
    test_scan_count()
    print("secret scan filter: exact accepted and rejected controls passed")
