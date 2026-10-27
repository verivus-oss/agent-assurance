"""Exercise provenance source selection through the CI entry point."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from _test_require import require
from check_workflow_text import provenance


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


if __name__ == "__main__":
    test_provenance_population()
    print("provenance population: accepted and rejected source boundaries passed")
