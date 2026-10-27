"""Exercise provenance source selection through the CI entry point."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from _test_require import require
from check_workflow_text import banned_markers, language_symbols, provenance


def test_provenance_population() -> None:
    with TemporaryDirectory(prefix="provenance-population-") as directory:
        root = Path(directory)
        validator = root / "validators/validate_provenance.py"
        validator.parent.mkdir()
        validator.write_text(
            "from pathlib import Path\n"
            "import sys\n"
            "sources = sys.argv[1:sys.argv.index('--repo-root')]\n"
            "raise SystemExit(int(any('reject' in Path(source).read_text() for source in sources)))\n"
        )
        negative = root / "examples/negative/bad.toml"
        sibling = root / "examples/negative-extra/sibling.toml"
        positive = root / "examples/valid.toml"
        negative.parent.mkdir(parents=True)
        sibling.parent.mkdir(parents=True)
        negative.write_text("[provenance]\nreject = true\n")
        sibling.write_text("[provenance]\naccepted = true\n")
        positive.write_text("[provenance]\naccepted = true\n")

        output = StringIO()
        with redirect_stdout(output):
            provenance(root)
        require("2 positive files accepted, 1 negative files rejected" in output.getvalue())

        sibling.write_text("[provenance]\nreject = true\n")
        try:
            provenance(root)
        except ValueError as exc:
            require("positive provenance sweep failed" in str(exc))
        else:
            raise AssertionError("sibling-named directory escaped the positive sweep")

        sibling.write_text("[provenance]\naccepted = true\n")
        negative.write_text("[provenance]\naccepted = true\n")
        try:
            provenance(root)
        except ValueError as exc:
            require("negative provenance fixture was not rejected" in str(exc))
        else:
            raise AssertionError("accepted negative fixture passed the rejection check")

        negative.write_text("[provenance]\nreject = true\n")
        sibling.unlink()
        positive.unlink()
        try:
            provenance(root)
        except ValueError as exc:
            require("population is empty" in str(exc))
        else:
            raise AssertionError("empty positive provenance population was accepted")
        positive.write_text("[provenance]\naccepted = true\n")
        negative.unlink()
        try:
            provenance(root)
        except ValueError as exc:
            require("population is empty" in str(exc))
        else:
            raise AssertionError("empty negative provenance population was accepted")


def test_language_symbols() -> None:
    with TemporaryDirectory(prefix="language-symbol-control-") as directory:
        root = Path(directory)
        source = root / "examples/language-validation/src/target.py"
        source.parent.mkdir(parents=True)
        source.write_text("def target_symbol():\n    pass\n")
        declaration = root / "examples/language-validation/traceability.toml"
        declaration.write_text(
            "[[code]]\nid = 'code-one'\n"
            "path = 'examples/language-validation/src/target.py'\n"
            "symbol = 'target_symbol'\n"
        )
        output = StringIO()
        with redirect_stdout(output):
            language_symbols(root)
        require("1 declared symbols found" in output.getvalue())
        source.write_text("def other_symbol():\n    pass\n")
        try:
            language_symbols(root)
        except ValueError as exc:
            require("fixture symbol missing" in str(exc))
        else:
            raise AssertionError("missing declared language symbol was accepted")


def test_banned_markers() -> None:
    git = shutil.which("git")
    require(git is not None, "git is required for tracked-file control")
    with TemporaryDirectory(prefix="banned-marker-control-") as directory:
        root = Path(directory)
        (root / "core").mkdir()
        (root / "examples").mkdir()
        (root / "fixtures").mkdir()
        (root / "spec.md").write_text("public specification\n")
        (root / "core/ontology.toml").write_text("name = 'ontology'\n")
        example = root / "examples/example.toml"
        example.write_text("name = 'example'\n")
        for index in range(100):
            (root / "fixtures" / f"source-{index}.txt").write_text("public fixture\n")
        subprocess.run([git, "init", "-q"], cwd=root, check=True, capture_output=True)  # nosec B603  # noqa: S603
        subprocess.run([git, "add", "--all"], cwd=root, check=True, capture_output=True)  # nosec B603  # noqa: S603
        output = StringIO()
        with redirect_stdout(output):
            banned_markers(root)
        require("1 example TOML files and 103 tracked files checked" in output.getvalue())
        example.write_text("kind = 'bare'\n")
        try:
            banned_markers(root)
        except ValueError as exc:
            require("bare kind field" in str(exc))
        else:
            raise AssertionError("bare kind field was accepted")
        example.write_text("name = 'example'\n")
        (root / "fixtures/source-0.txt").write_text("/srv/" + "repos/internal" + "/private\n")
        try:
            banned_markers(root)
        except ValueError as exc:
            require("internal path found" in str(exc))
        else:
            raise AssertionError("internal path was accepted")


if __name__ == "__main__":
    test_provenance_population()
    test_language_symbols()
    test_banned_markers()
    print("workflow text boundaries: accepted and rejected source cases passed")
