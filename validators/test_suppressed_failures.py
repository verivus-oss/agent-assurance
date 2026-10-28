"""Failures in optional counts and cleanup must remain visible."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from _literal_path import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

import _literal_json as json
from _test_require import require
from check_attribute_values import derive_rdf_counts
from validate_api_snapshot import main as snapshot_main

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference/database"))
import ingest_runtime_document as ingest_cli  # noqa: E402
import replay_runtime_documents as replay_cli  # noqa: E402


class CloseFails:
    def close(self) -> None:
        raise OSError("secret connection detail")


class FakeStore:
    def __init__(self, *args, **kwargs) -> None:
        self.connection = CloseFails()

    def initialize(self, **kwargs) -> dict:
        return {"status": "committed"}


def test_snapshot_failures() -> None:
    output = StringIO()
    with redirect_stdout(output):
        require(snapshot_main(["--repo-root", str(ROOT), str(ROOT / "examples/minimal-api-snapshot.toml")]) == 0)
    require("api-snapshot instances: 1" in output.getvalue())
    with TemporaryDirectory(prefix="snapshot-failure-") as directory:
        malformed = Path(directory) / "invalid.toml"
        malformed.write_bytes(b"[meta]\n\xff")
        for selected in (malformed, Path(directory) / "missing.toml"):
            output = StringIO()
            with redirect_stdout(output):
                require(snapshot_main([str(selected)]) == 1)
            require(str(selected) in output.getvalue() and "cannot parse TOML" in output.getvalue())


def test_rdf_count_failures() -> None:
    with TemporaryDirectory(prefix="rdf-count-failure-") as directory:
        root = Path(directory)
        try:
            derive_rdf_counts(root)
        except ValueError as exc:
            require("binary is unavailable" in str(exc))
        else:
            raise AssertionError("missing RDF binary was accepted")
        binary = root / "tools/dagtoml-rdf/target/release/dagtoml-rdf"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"placeholder")
        with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, "parsed 42 triples", "")):
            require(derive_rdf_counts(root) == {"schema": 42, "shapes": 42})
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("rdf", 30)):
            try:
                derive_rdf_counts(root)
            except ValueError as exc:
                require("TimeoutExpired" in str(exc))
            else:
                raise AssertionError("RDF timeout was suppressed")


def test_connection_close_warning() -> None:
    output, diagnostic = StringIO(), StringIO()
    with patch.object(ingest_cli, "connect", return_value=CloseFails()), patch.object(ingest_cli, "Store", FakeStore):
        with redirect_stdout(output), redirect_stderr(diagnostic):
            require(ingest_cli.main(["--engine", "sqlite", "--destination", "unused", "initialize"]) == 0)
    require(json.loads(output.getvalue())["status"] == "committed")
    require(json.loads(diagnostic.getvalue())["code"] == "connection-close-failed")
    require("secret connection detail" not in diagnostic.getvalue())

    with TemporaryDirectory(prefix="replay-close-warning-") as directory:
        root = Path(directory)
        manifest = root / "manifest.toml"
        manifest.write_text("[meta]\n")
        report = root / "report.json"
        output, diagnostic = StringIO(), StringIO()
        with patch.object(replay_cli, "connect", return_value=CloseFails()), \
             patch.object(replay_cli, "Store", FakeStore), \
             patch.object(replay_cli, "replay", return_value={"status": "committed"}):
            with redirect_stdout(output), redirect_stderr(diagnostic):
                require(replay_cli.main(["--engine", "sqlite", "--destination", "unused",
                                         "--manifest", str(manifest), "--report", str(report)]) == 0)
        require(json.loads(report.read_text())["status"] == "committed")
        require(json.loads(diagnostic.getvalue())["code"] == "connection-close-failed")
        require("secret connection detail" not in diagnostic.getvalue())


if __name__ == "__main__":
    test_snapshot_failures()
    test_rdf_count_failures()
    test_connection_close_warning()
    print("suppressed failure boundaries: accepted and rejected cases passed")
