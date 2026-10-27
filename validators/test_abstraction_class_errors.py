"""Check that descriptor failures are reported from one captured document."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from _test_require import require
from validate_abstraction_class import main


def test_single_read_and_invalid_input() -> None:
    root = Path(__file__).resolve().parent.parent
    with TemporaryDirectory(prefix="abstraction-class-control-") as directory:
        subject = Path(directory) / "kind.toml"
        subject.write_text("[kind]\n")
        original_read = Path.read_text
        reads = 0

        def one_read(path: Path, *args: object, **kwargs: object) -> str:
            nonlocal reads
            if path == subject:
                reads += 1
                require(reads == 1, "descriptor was reopened after validation")
            return original_read(path, *args, **kwargs)

        output = StringIO()
        with patch.object(Path, "read_text", one_read), redirect_stdout(output):
            code = main(["--repo-root", str(root), str(subject)])
        require(code == 0 and reads == 1)
        require("1 file(s) checked; 0 declared" in output.getvalue())

        subject.write_text("[kind\n")
        diagnostic = StringIO()
        with redirect_stderr(diagnostic):
            code = main(["--repo-root", str(root), str(subject)])
        require(code == 1)
        require("cannot parse TOML" in diagnostic.getvalue())


if __name__ == "__main__":
    test_single_read_and_invalid_input()
    print("abstraction class failure controls: 1 test group passed")
