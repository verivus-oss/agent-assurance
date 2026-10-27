"""Accepted and rejected boundaries for the exact link scan exceptions."""

from _test_require import expect_raises, require
from check_link_scan import check_report
from prepare_link_scan import host_of, included_source, select_links, split_record
from pathlib import Path


def test_records() -> None:
    require(split_record("https://example.org/a (./README.md)") ==
            ("https://example.org/a", "./README.md"))
    require(split_record("mailto:a@example.org (./README.md) [excluded]") ==
            ("mailto:a@example.org", "./README.md"))
    for malformed in ("", "https://example.org/a", "https://example.org/a (./README.md"):
        expect_raises(ValueError, lambda: split_record(malformed),
                      "malformed extractor record was accepted")


def test_scope() -> None:
    tracked = {"README.md", "docs/reviews/report.md"}
    require(included_source("./README.md", tracked))
    require(not included_source("./docs/reviews/report.md", tracked))
    for source in ("./not-tracked.md", "../README.md"):
        expect_raises(ValueError, lambda: included_source(source, tracked),
                      "untracked source was accepted")


def test_hosts() -> None:
    require(host_of("https://toml.io/en/v1.1.0") == "toml.io")
    require(host_of("https://toml.io.evil.example/path") == "toml.io.evil.example")
    for url in ("https://user@toml.io/path", "https://toml.io:port/path"):
        expect_raises(ValueError, lambda: host_of(url),
                      "ambiguous authority was accepted")


def test_selection() -> None:
    tracked = {"README.md"}
    urls = ["https://github.com/example/" + str(index) for index in range(18)]
    urls.append("https://toml.io.evil.example/path")
    rows = [url + " (./README.md)" for url in urls]
    rows += ["https://toml.io/en/v1.1.0 (./README.md)",
             "https://www.fco-im.nl/papers (./README.md)"]
    selected, exceptions = select_links(rows, tracked)
    require(selected == sorted(urls))
    require(len(exceptions) == 2)
    for absent in ("https://toml.io/en/v1.1.0", "https://www.fco-im.nl/papers"):
        expect_raises(ValueError,
                      lambda: select_links([row for row in rows if not row.startswith(absent)], tracked),
                      "missing exception control was accepted")


def test_report() -> None:
    source = Path("candidate-links.txt")
    candidates = ["https://example.org/a", "https://example.org/b"]
    report = {"total": 2, "unique": 2, "successful": 2, "unknown": 0,
              "unsupported": 0, "timeouts": 0, "excludes": 0, "errors": 0,
              "success_map": {str(source): [{"url": url} for url in candidates]}}
    check_report(report, candidates, source)
    for change in ({"successful": 1}, {"excludes": 1}, {"errors": 1},
                   {"success_map": {str(source): [{"url": candidates[0]}]}}):
        expect_raises(RuntimeError, lambda: check_report(report | change, candidates, source),
                      "incomplete link check report was accepted")


if __name__ == "__main__":
    test_records()
    test_scope()
    test_hosts()
    test_selection()
    test_report()
    print("link scan: exact scope and host boundaries passed")
