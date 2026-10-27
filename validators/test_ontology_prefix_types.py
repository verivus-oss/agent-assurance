"""Check accepted and rejected ontology prefix declarations in all validators."""

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import _literal_args as argparse
import _toml11 as tomllib
from validate_ijb_conformance import validate_ontology


ROOT = Path(__file__).resolve().parents[1]
MARKER = 'id_prefix    = "REQ"'
ERROR = "declare exactly one uppercase ASCII id_prefix or id_decimal_prefix"


def cases(source: str) -> tuple[tuple[str, str, bool], ...]:
    if source.count(MARKER) != 1:
        raise AssertionError("ontology prefix fixture marker changed")
    return (
        ("plain-prefix", MARKER, True),
        ("decimal-prefix", 'id_decimal_prefix = "REQ"', True),
        ("both-strings", MARKER + '\nid_decimal_prefix = "U"', False),
        ("second-integer", MARKER + "\nid_decimal_prefix = 1", False),
        ("second-boolean", MARKER + "\nid_decimal_prefix = true", False),
        ("first-integer", 'id_prefix = 1\nid_decimal_prefix = "U"', False),
        ("first-array", 'id_prefix = []\nid_decimal_prefix = "U"', False),
        ("lowercase-prefix", 'id_prefix = "req"', False),
        ("missing-prefix", '', False),
    )


def check(binary: Path, name: str, path: Path, accepted: bool) -> None:
    process = subprocess.run(  # nosec B603  # noqa: S603
        [str(binary), "--repo-root", str(ROOT), "--mode", "ijb", str(path)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    output = process.stdout + process.stderr
    if accepted and process.returncode != 0:
        raise AssertionError(f"{name} rejected a valid ontology: {output}")
    if not accepted and (process.returncode == 0 or ERROR not in output):
        raise AssertionError(f"{name} accepted an invalid prefix or failed for another reason: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rs", required=True)
    parser.add_argument("--go", required=True)
    args = parser.parse_args()
    binaries = ((Path(args.rs).resolve(), "Rust"), (Path(args.go).resolve(), "Go"))
    if any(not binary.is_file() for binary, _ in binaries):
        raise AssertionError("both primary validator binaries are required")
    source = (ROOT / "core/ontology.toml").read_text()
    controls = cases(source)
    with TemporaryDirectory(prefix="ontology-prefix-") as work:
        for name, replacement, accepted in controls:
            path = Path(work) / (name + ".toml")
            path.write_text(source.replace(MARKER, replacement))
            errors = validate_ontology(tomllib.loads_bytes(path.read_bytes()), str(path))
            prefix_errors = [error for error in errors if ERROR in error]
            if accepted and prefix_errors or not accepted and not prefix_errors:
                raise AssertionError("Python reference prefix verdict differs from expected: " + name)
            for binary, language in binaries:
                check(binary, language + "/" + name, path, accepted)
    print(f"ontology prefix boundaries: {len(controls)} controls across Rust, Go, Python passed")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
