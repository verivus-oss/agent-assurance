"""Accepted and rejected boundaries for the exact link scan exceptions."""

from _test_require import expect_raises, require
import check_link_scan as scanner
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import os
import hashlib
from _literal_json import dumps, loads
from _temporary_attribute import temporary_attribute, returning, successive
from prepare_link_scan import host_of, included_source, select_links, split_record, tracked_files, tracked_paths
from _literal_path import Path
from _credential_test_support import TemporaryTree, command, commit, initialize, write


def test_source_identity_detects_hidden_working_bytes():
    with TemporaryTree() as directory:
        root = Path(directory).resolve()
        initialize(root)
        subject = root / 'source.md'
        original = b'original\n'
        write(subject, original)
        commit(root, 'link source byte control')
        baseline = scanner.source_identity(root)
        require(baseline['tree_state'] == 'clean')
        for flag in ('assume-unchanged', 'skip-worktree'):
            command(root, 'update-index', '--' + flag, '--', 'source.md')
            try:
                write(subject, b'changed!\n')
                require(command(root, 'status', '--porcelain').stdout == b'', 'link source change was not hidden')
                changed = scanner.source_identity(root)
                require(changed['tree_state'] == 'working-files' and changed['diff_sha256'] != baseline['diff_sha256'],
                        'link receipt identity concealed changed source bytes')
            finally:
                write(subject, original)
                command(root, 'update-index', '--no-' + flag, '--', 'source.md')
            require(scanner.source_identity(root) == baseline)


def native_report(candidates, source, *, failures=(), timeouts=()):
    errors, delayed = set(failures), set(timeouts)
    successes = set(candidates) - errors - delayed
    def mapping(urls, code):
        return {str(source): [{"url": url, "status": {"code": code, "text": "private producer diagnostic"},
                               "span": {"line": None, "column": None}} for url in sorted(urls)]} if urls else {}
    return {"total": len(candidates), "unique": len(candidates), "successful": len(successes),
            "unknown": 0, "unsupported": 0, "timeouts": len(delayed), "redirects": 0,
            "remaps": 0, "excludes": 0, "errors": len(errors), "cached": 0,
            "success_map": mapping(successes, 200), "error_map": mapping(errors, 500),
            "timeout_map": mapping(delayed, None), "excluded_map": {}}


def no_producer_metadata(value):
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            require(not set(item) & {"span", "line", "column", "details", "text", "duration",
                                     "success_map", "error_map", "timeout_map"})
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)


def test_records() -> None:
    require(split_record("https://example.org/a (./README.md)") ==
            ("https://example.org/a", "./README.md"))
    require(split_record("mailto:a@example.org (./README.md) [excluded]") ==
            ("mailto:a@example.org", "./README.md"))
    for malformed in ("", "https://example.org/a", "https://example.org/a (./README.md"):
        expect_raises(ValueError, lambda: split_record(malformed),
                      "malformed extractor record was accepted")


def test_tracked_source_framing_and_ambient_index_boundary():
    require(tracked_paths(b"README.md\0.github/workflows/validate.yml\0") ==
            {"README.md", ".github/workflows/validate.yml"})
    for raw in (b"", b"README.md", b"README.md\0\0", b"README.md\0README.md\0",
                b"\xff\0", b"/outside\0", b"../outside\0", b"root/./source.md\0",
                b"root\\source.md\0", b"root\nsource.md\0"):
        expect_raises(RuntimeError, lambda: tracked_paths(raw), "ambiguous tracked source population passed")
    before = tracked_files()
    require(len(before) >= 100)
    with TemporaryDirectory(prefix="link-foreign-index-") as directory:
        previous = os.environ.get("GIT_INDEX_FILE")
        try:
            os.environ["GIT_INDEX_FILE"] = str(Path(directory) / "absent-index")
            require(tracked_files() == before, "ambient foreign index changed the declared source population")
        finally:
            if previous is None:
                del os.environ["GIT_INDEX_FILE"]
            else:
                os.environ["GIT_INDEX_FILE"] = previous


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
    expect_raises(ValueError,
                  lambda: select_links(rows + ["https://github.com/example/excluded (./README.md) [excluded]"], tracked),
                  "excluded in-scope HTTP URL was accepted")
    require(select_links(rows + ["mailto:reader@example.org (./README.md) [excluded]"], tracked) ==
            (selected, exceptions))
    for absent in ("https://toml.io/en/v1.1.0", "https://www.fco-im.nl/papers"):
        expect_raises(ValueError,
                      lambda: select_links([row for row in rows if not row.startswith(absent)], tracked),
                      "missing exception control was accepted")


def test_report() -> None:
    source = Path("candidate-links.txt")
    candidates = ["https://example.org/a", "https://example.org/b"]
    report = native_report(candidates, source)
    scanner.check_report(report, candidates, source)
    for change in ({"successful": 1}, {"excludes": 1}, {"errors": 1},
                   {"success_map": {str(source): [{"url": candidates[0]}]}}):
        expect_raises(RuntimeError, lambda: scanner.check_report(report | change, candidates, source),
                      "incomplete link check report was accepted")


def test_complete_failure_partition_is_actionable_without_producer_coordinates():
    source = Path("candidate-links.txt")
    candidates = ["https://example.org/a", "https://example.org/b", "https://example.org/c"]
    summary = scanner.report_outcomes(native_report(candidates, source, failures=candidates[:1], timeouts=candidates[1:2]),
                              candidates, source)
    require(summary == {"status": "failed", "total": 3, "successful": 1, "errors": 1, "timeouts": 1,
                        "failures": [{"url": candidates[0], "outcome": "error", "http_status": 500},
                                     {"url": candidates[1], "outcome": "timeout", "http_status": None}]})
    no_producer_metadata(summary)
    expect_raises(RuntimeError,
                  lambda: scanner.check_report(native_report(candidates, source, failures=candidates[:1]), candidates, source),
                  "complete failed checks were accepted by the successful-report guard")
    uniform = scanner.report_outcomes(native_report(candidates, source, failures=candidates), candidates, source)
    require(uniform["status"] == "failed" and uniform["errors"] == len(candidates) and not uniform["successful"])
    require({row["url"] for row in uniform["failures"]} == set(candidates))


def test_outcome_partition_rejects_absent_duplicate_substituted_and_falsely_successful_results():
    source = Path("candidate-links.txt")
    candidates = ["https://example.org/a", "https://example.org/b"]
    def rejected(change):
        report = native_report(candidates, source)
        change(report)
        expect_raises(RuntimeError, lambda: scanner.report_outcomes(report, candidates, source),
                      "invalid outcome partition was accepted")
    rejected(lambda report: report.update(successful=True))
    rejected(lambda report: report.update(errors=1))
    rejected(lambda report: report.update(cached=1))
    rejected(lambda report: report.update(remaps=1))
    rejected(lambda report: report["excluded_map"].update({str(source): [{"url": candidates[0]}]}))
    rejected(lambda report: report.pop("timeout_map"))
    rejected(lambda report: report["success_map"].update({"other-source": []}))
    rejected(lambda report: report["success_map"][str(source)][1].update(url=candidates[0]))
    rejected(lambda report: report["success_map"][str(source)][0].update(url="https://other.example/"))
    rejected(lambda report: report["success_map"][str(source)][0].update(status={}))
    rejected(lambda report: report["success_map"][str(source)][0]["status"].update(text=None))
    for code in (None, True, 0, 199, 300, 404, 500, 600, "200"):
        rejected(lambda report: report["success_map"][str(source)][0]["status"].update(code=code))
    for candidate_set in ([], [candidates[0], candidates[0]], list(reversed(candidates)), [7], [["nested"]],
                          ["file:///private"], ["https://example.org/\nforged"]):
        expect_raises(RuntimeError, lambda: scanner.report_outcomes({}, candidate_set, source),
                      "absent or invalid candidate set was accepted")
    for code in (200, 204, 299, 403, 429):
        report = native_report(candidates, source)
        for entry in report["success_map"][str(source)]:
            entry["status"]["code"] = code
        require(scanner.report_outcomes(report, candidates, source)["status"] == "passed")


def test_artifacts_cannot_overwrite_checkout_sources_or_escape_through_a_symlink():
    with TemporaryDirectory(prefix="link-output-boundary-") as directory:
        work = Path(directory)
        root = work / "checkout"
        root.mkdir()
        tracked = {"README.md", ".github/workflows/validate.yml"}
        require(scanner.artifact_target(root, work / "report.json", tracked) == work / "report.json")
        require(scanner.artifact_target(root, root / ".local/report.json", tracked) == root / ".local/report.json")
        for target in (root / "README.md", root / "new-report.json", root / ".github/workflows/validate.yml",
                       root / ".hidden/report.json"):
            expect_raises(ValueError, lambda: scanner.artifact_target(root, target, tracked),
                          "report could overwrite a governed source path")
        (root / ".local").mkdir()
        (root / "README.md").write_text("independent source sentinel")
        (root / ".local/alias").symlink_to(root / "README.md")
        expect_raises(ValueError, lambda: scanner.artifact_target(root, root / ".local/alias", tracked),
                      "report symlink could overwrite tracked source")
        require((root / "README.md").read_text() == "independent source sentinel")


def test_entry_point_retains_failed_and_incomplete_results_and_matches_exit_status():
    # Scripted process outcomes exercise wrapper logic. Native controlled HTTP
    # responses establish the supplier format separately from these fixtures.
    candidates = ["https://example.org/" + str(index) for index in range(20)]
    rows = [url + " (./README.md)" for url in candidates]
    rows += ["https://toml.io/en/v1.1.0 (./README.md)", "https://www.fco-im.nl/papers (./README.md)"]
    candidates = sorted(candidates)
    expected = {"success": (0, "passed"), "error": (1, "failed"), "timeout": (1, "failed"),
                "uniform-error": (1, "failed"), "missing": (2, "incomplete"), "malformed": (2, "incomplete"),
                "bad-exit": (2, "incomplete"), "false-success": (2, "incomplete"),
                "extract-failed": (2, "incomplete"), "admission-excluded": (2, "incomplete"),
                "source-moved": (2, "incomplete"), "binary-moved": (2, "incomplete"),
                "absent-binary": (2, "incomplete"), "wrong-version": (2, "incomplete"),
                "no-inputs": (2, "incomplete"), "summary-unavailable": (2, "incomplete")}
    phases = {"success": "complete", "error": "complete", "timeout": "complete", "uniform-error": "complete",
              "missing": "checking", "malformed": "checking", "bad-exit": "checking", "false-success": "checking",
              "extract-failed": "extraction", "admission-excluded": "admission", "source-moved": "source-recheck",
              "binary-moved": "source-recheck", "absent-binary": "scanner-identity", "wrong-version": "scanner-identity",
              "no-inputs": "extraction", "summary-unavailable": "report-delivery"}
    require(set(phases) == set(expected))
    for mode, (exit_status, status) in expected.items():
        with TemporaryDirectory(prefix="link-report-control-") as directory:
            work = Path(directory)
            binary = work / "lychee"
            if mode != "absent-binary":
                binary.write_bytes(b"independent fixture producer")
            report, summary = work / "retained.json", work / "summary.md"
            if mode == "summary-unavailable":
                summary.mkdir()

            def controlled_run(_binary, arguments):
                if arguments == ["--version"]:
                    return SimpleNamespace(returncode=0, stdout="lychee 0.0.0\n" if mode == "wrong-version" else "lychee 0.24.2\n",
                                           stderr="")
                output = Path(arguments[arguments.index("--output") + 1])
                subject = arguments[-1]
                if "--dump" in arguments:
                    if mode == "extract-failed":
                        return SimpleNamespace(returncode=1, stdout="", stderr="private extraction detail")
                    selected = rows if subject == "." else [url + " (" + subject + ")" for url in candidates]
                    if subject != "." and mode == "admission-excluded":
                        selected[0] += " [excluded]"
                    output.write_text("" if mode == "no-inputs" else "\n".join(selected) + "\n")
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                native = native_report(candidates, subject,
                                       failures=candidates if mode == "uniform-error" else candidates[:1] if mode == "error" else (),
                                       timeouts=candidates[:1] if mode == "timeout" else ())
                if mode == "false-success":
                    for entry in native["success_map"][subject]:
                        entry["status"]["code"] = 500
                if mode != "missing":
                    output.write_text("{" if mode == "malformed" else dumps(native))
                if mode == "binary-moved":
                    binary.write_bytes(b"different fixture producer")
                return SimpleNamespace(returncode=2 if mode in ("error", "timeout", "uniform-error", "bad-exit") else 0,
                                       stdout="", stderr="private producer diagnostic")

            identity = scanner.source_identity(Path.cwd().resolve())
            identities = successive([identity, identity | {"status_sha256": "0" * 64}]) if mode == "source-moved" else returning(identity)
            with temporary_attribute(scanner, "run", controlled_run), \
                 temporary_attribute(scanner, "tracked_files", returning({"README.md"})), \
                 temporary_attribute(scanner, "source_identity", identities), \
                 redirect_stdout(StringIO()), redirect_stderr(StringIO()) as diagnostic:
                result = scanner.main(["--lychee", str(binary), "--report", str(report), "--summary", str(summary)])
            require(result == exit_status, "wrong wrapper exit for " + mode)
            retained = loads(report.read_text())
            require(retained["status"] == status and retained["source"] == identity, "wrong retained result for " + mode)
            require(retained["phase"] == phases[mode], "fixture failed before its intended property: " + mode)
            if mode != "absent-binary":
                require(retained["scanner"]["binary_sha256"] == hashlib.sha256(b"independent fixture producer").hexdigest())
                require(retained["scanner"]["expected_version"] == "lychee 0.24.2")
                require(("version" in retained["scanner"]) == (mode != "wrong-version"))
            if mode == "malformed":
                require(retained["failure_type"] == "InvalidJSON")
            if mode == "summary-unavailable":
                require(retained["phase"] == "report-delivery" and summary.is_dir())
            else:
                require(dumps(retained, indent=2) in summary.read_text())
            no_producer_metadata(retained)
            if status == "failed":
                expected_failures = len(candidates) if mode == "uniform-error" else 1
                require(len(retained["failures"]) == expected_failures)
                require(all(row["url"] in diagnostic.getvalue() for row in retained["failures"]))
            require("private producer diagnostic" not in diagnostic.getvalue())


def test_report_and_summary_cannot_alias_or_overwrite_an_existing_output():
    with TemporaryDirectory(prefix="link-output-alias-") as directory:
        output = Path(directory) / "combined.txt"
        output.write_text("independent existing output sentinel")
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()) as diagnostic:
            code = scanner.main(["--lychee", "unused", "--report", str(output), "--summary", str(output)])
        require(code == 2 and "destinations must differ" in diagnostic.getvalue())
        require(output.read_text() == "independent existing output sentinel")


if __name__ == "__main__":
    required = {name for name, value in tuple(globals().items()) if name.startswith("test_") and callable(value)}
    require(required, "link scan controls are absent")
    visited = set()
    for name in sorted(required):
        globals()[name]()
        visited.add(name)
    require(visited == required)
    print("link scan: complete declared scope, outcome, output and failure-retention controls executed")
