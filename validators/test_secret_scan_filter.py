"""Keep the historical public event exception exact and fail closed."""

from contextlib import redirect_stderr
from io import StringIO

from _test_require import expect_raises, require
from _credential_report import encode_report
from check_secret_scan import (KNOWN_COMMITS, PUBLIC_HEX_FILE, PUBLIC_HEX_RULE, PUBLIC_HEX_SHA256,
                               check_findings, check_scan_population, known_public_literal)


def fixture():
    commit = sorted(KNOWN_COMMITS)[0]
    digest = "f" * 64
    capture = {"rule": PUBLIC_HEX_RULE, "value_sha256": PUBLIC_HEX_SHA256, "source_sha256": digest,
               "byte_span": [10, 26], "context_byte_span": [0, 26]}
    return {"rule": PUBLIC_HEX_RULE, "path": PUBLIC_HEX_FILE, "commit": commit,
            "value_sha256": PUBLIC_HEX_SHA256, "source_sha256": digest,
            "capture_count": 1, "parent_capture_counts": [0, 1], "captures": [capture]}


def test_exception():
    record = fixture()
    expected = {record["commit"]}
    require(known_public_literal(record))
    check_findings([record], expected)
    for field, replacement in (
        ("value_sha256", "a" * 64), ("rule", "other-rule"), ("path", "validators/other.toml"),
        ("commit", "a" * 40), ("capture_count", 2), ("capture_count", True),
        ("parent_capture_counts", [1, 1]), ("parent_capture_counts", []),
        ("parent_capture_counts", [False]), ("source_sha256", None),
        ("captures", []), ("captures", [record["captures"][0]] * 2),
        ("captures", [record["captures"][0] | {"decoding": {"depth": 1}}]),
        ("captures", [record["captures"][0] | {"source_sha256": "a" * 64}]),
    ):
        changed = record | {field: replacement}
        require(not known_public_literal(changed), "public exception widened: " + field)
        output = StringIO()
        with redirect_stderr(output):
            expect_raises(RuntimeError, lambda: check_findings([changed], expected),
                          "unapproved event was accepted")
        require("unapproved event" in output.getvalue())
    expect_raises(RuntimeError, lambda: check_findings([], expected), "absent public control was accepted")
    expect_raises(RuntimeError, lambda: check_findings([record, record], expected), "duplicate control passed")


def test_population():
    known, head, blob = sorted(KNOWN_COMMITS)[0], "a" * 40, "b" * 40
    result = {"head": head, "commits": [known, head], "scanned_commits": [known, head],
              "head_ancestry": [known, head], "scanned_blobs": [blob]}
    require(check_scan_population(result) == {known})
    for field, replacement in (
        ("head", "c" * 40), ("commits", []), ("commits", [known, known]),
        ("commits", [head]), ("scanned_commits", [head]), ("scanned_commits", [known, head, blob]),
        ("head_ancestry", [head]), ("head_ancestry", [known, head, blob]),
        ("scanned_blobs", []), ("scanned_blobs", ["bad"]),
    ):
        expect_raises(RuntimeError, lambda: check_scan_population(result | {field: replacement}),
                      "invalid scan population passed: " + field)


def test_report_serialization():
    require(encode_report({"z": [None, True, False, 12, "\n\u2603"], "a": "quoted\""})
            == '{"a":"quoted\\\"","z":[null,true,false,12,"\\n\\u2603"]}')
    for value in (1.5, b"bytes", {1: "key"}, {"set"}):
        expect_raises(TypeError, lambda: encode_report(value), "unsupported report type was accepted")


if __name__ == "__main__":
    test_exception()
    test_population()
    test_report_serialization()
    print("credential event filter: exact accepted and rejected historical controls passed")
