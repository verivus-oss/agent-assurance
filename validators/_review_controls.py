"""Executed regression controls for declaration and source-discovery boundaries."""

import contextlib
import hashlib
import io
import json
import subprocess
import sys
import textwrap
from unittest.mock import patch

from _instrument import require


def exercise(candidate, work):
    """Mutate only an isolated source copy; retain each property failure."""
    from check_attribute_values import parse_go_expected_counts, parse_rust_expected_counts
    from discrimination import discover_cases
    from _storage import StorageError
    import ingest_runtime_document as ingest_cli
    import replay_runtime_documents as replay_cli

    observations = []

    def command(name, argv, expected, needle):
        result = subprocess.run(argv, cwd=candidate, capture_output=True, text=True, timeout=60)  # nosec B603 # noqa: S603
        output = result.stdout + result.stderr
        require(result.returncode == expected and needle in output, name + ": " + output)
        observations.append({"control": name, "status": "confirmed" if expected == 0 else "killed", "output": output})

    generator = [sys.executable, str(candidate / "reference/database/generate_allowed_values.py"), "--repo-root", str(candidate)]
    command("generator-positive", generator, 0, "all three owned seed sections match")
    marker = "-- BEGIN GENERATED DECLARED VOCABULARY VALUES\n"
    for engine in ("postgres", "sqlite", "duckdb"):
        path = candidate / f"reference/database/{engine}/seed.sql"
        original = path.read_text()
        for name, variant, needle in (
            ("duplicate-marker", original + marker, "exactly one of each generation marker"),
            ("format-drift", original.replace(marker, marker + "\n"), "generated catalog differs"),
        ):
            require(variant != original)
            path.write_text(variant)
            try:
                command(engine + "/" + name, generator, 1, needle)
            finally:
                path.write_text(original)

    for language, relative, parser, declaration in (
        ("rust", "tools/dagtoml-duckdb/src/main.rs", parse_rust_expected_counts, '("runtime_document", 0)'),
        ("go", "tools/dagtoml-duckdb-go/main.go", parse_go_expected_counts, '{"runtime_document", 0}'),
    ):
        require(parser(candidate)["runtime_document"] == 0)
        path = candidate / relative
        original = path.read_text()
        require(original.count(declaration) == 1)
        path.write_text(original.replace(declaration, declaration + ",\n    " + declaration))
        try:
            parser(candidate)
        except ValueError as exc:
            require("duplicate loader count key" in str(exc))
            observations.append({"control": language + "/duplicate-count-key", "status": "killed", "output": str(exc)})
        else:
            raise AssertionError("duplicate loader declaration survived")
        finally:
            path.write_text(original)

    manifest = candidate / "reference/database/MANIFEST.toml"
    original = manifest.read_text()
    for key, retired in (("informational_native_enum_types", "closed_enums"), ("informational_column_constraint_hints", "closed_checks")):
        require(key in original)
        manifest.write_text(original.replace(key, retired))
        try:
            command(retired + "/retired-manifest-key", [sys.executable, str(candidate / "validators/check_attribute_values.py"),
                    "--repo-root", str(candidate), "--declarations-only", "--no-rdf"], 1, "retired manifest constraint labels")
        finally:
            manifest.write_text(original)

    workflow = (candidate / ".github/workflows/validate.yml").read_text()
    section = workflow.split("- name: Discrimination coverage (external assertion)", 1)[1]
    external = textwrap.dedent(section.split("python3 - <<'PY'\n", 1)[1].split("          PY\n", 1)[0])
    command("external-discovery-positive", [sys.executable, "-c", external], 0, "discrimination coverage OK")
    directory = candidate / "conformance/cases/gate-decision"
    hidden = work / "withheld-gate-decision"
    directory.rename(hidden)
    try:
        try:
            discover_cases(candidate / "conformance/cases")
        except ValueError as exc:
            require("mapped kinds have no conformance directory" in str(exc))
            observations.append({"control": "removed-kind-directory", "status": "killed", "output": str(exc)})
        else:
            raise AssertionError("removed complete kind directory survived")
        command("external-removed-kind-directory", [sys.executable, "-c", external], 1, "mapped kinds are absent")
    finally:
        hidden.rename(directory)

    # A dotted stem's sidecar contains an impossible diagnostic. The readers
    # must consume it even when process results are supplied by this instrument.
    side = next(directory.glob("invalid/*.expected.toml"))
    case = side.with_name(side.name.removesuffix(".expected.toml") + ".toml")
    dotted = case.with_name("review.dotted.toml")
    dotted_side = dotted.with_suffix(".expected.toml")
    dotted.write_bytes(case.read_bytes())
    dotted_side.write_text('error_contains = ["review-impossible-dotted-sidecar-diagnostic"]\n')
    require(dotted in discover_cases(candidate / "conformance/cases"))
    # Stub process observations only for this sidecar-reader instrument. The
    # complete conformance suite separately executes the actual validators.
    import runner
    args = type("Arguments", (), {"cases": str(candidate / "conformance/cases"), "known_divergences": str(work / "absent"),
                                  "rs": "inert-rust", "go": "inert-go", "repo_root": str(candidate)})()
    def verdict(argv):
        return (1 if "/invalid/" in str(argv[-1]) else 0), "review-stub-observation"
    try:
        with patch.object(runner, "parse_args", return_value=args), patch.object(runner, "run_validator", side_effect=verdict), contextlib.redirect_stdout(io.StringIO()) as output:
            result = runner.main()
        require(result == 1 and "review-impossible-dotted-sidecar-diagnostic" in output.getvalue())
        observations.append({"control": "dotted-sidecar-runner", "status": "killed", "output": output.getvalue()})
        import discrimination
        with patch.object(sys, "argv", ["discrimination", "--rs", "inert-rust", "--go", "inert-go", "--repo-root", str(candidate), "--cases", str(candidate / "conformance/cases")]), patch.object(discrimination, "collect_output", return_value="review-stub-observation"), contextlib.redirect_stdout(io.StringIO()) as output:
            result = discrimination.main()
        require(result == 1 and "review.dotted.toml: sidecar fails to match" in output.getvalue())
        observations.append({"control": "dotted-sidecar-discrimination", "status": "killed", "output": output.getvalue()})
    finally:
        dotted.unlink()
        dotted_side.unlink()

    error = StorageError("commit-outcome-unknown", "injected acknowledgement loss")
    error.context = {"operation": "ingest", "contract_bundle_sha256": "a" * 64,
                     "documents": [{"source_path": "captured.toml", "content_sha256": "sha256:" + hashlib.sha256(b"captured").hexdigest()}]}
    for module in (ingest_cli, replay_cli):
        with patch.object(module, "connect", side_effect=error), contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            args = ["--engine", "sqlite", "--destination", "inert.db"]
            if module is ingest_cli:
                args += ["ingest", "captured.toml"]
            else:
                args += ["--manifest", "inert.toml", "--report", str(work / "unknown-report.json")]
            require(module.main(args) == 1)
        result = json.loads(err.getvalue() if module is ingest_cli else out.getvalue())
        require(result["status"] == "commit-outcome-unknown" and result["code"] == "commit-outcome-unknown")
        require({key: result[key] for key in error.context} == error.context)
        observations.append({"control": module.__name__ + "/unknown-identities", "status": "confirmed", "output": result})
    require(len(observations) == 18, "review control population changed")
    return observations
