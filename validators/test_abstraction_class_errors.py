"""Check that descriptor failures are reported from one captured document."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from _literal_path import Path
from tempfile import TemporaryDirectory

from _test_require import require
from validate_abstraction_class import main


def test_single_read_and_invalid_input() -> None:
    root = Path(__file__).resolve().parent.parent
    with TemporaryDirectory(prefix="abstraction-class-control-") as directory:
        subject = Path(directory) / "kind.toml"
        subject.write_bytes(b"[kind]\n")
        original_read = Path.read_bytes
        reads = 0

        def one_read(path: Path) -> bytes:
            nonlocal reads
            if path == subject:
                reads += 1
                require(reads == 1, "descriptor was reopened after validation")
            return original_read(path)

        output = StringIO()
        try:
            Path.read_bytes = one_read
            with redirect_stdout(output):
                code = main(["--repo-root", str(root), str(subject)])
        finally:
            Path.read_bytes = original_read
        require(code == 0 and reads == 1)
        require("1 file(s) checked; 0 declared" in output.getvalue())

        subject.write_bytes(b"[kind\n")
        diagnostic = StringIO()
        with redirect_stderr(diagnostic):
            code = main(["--repo-root", str(root), str(subject)])
        require(code == 1)
        require("cannot parse TOML" in diagnostic.getvalue())


if __name__ == "__main__":
    test_single_read_and_invalid_input()
    print("abstraction class failure controls: 1 test group passed")
