"""Accepted and rejected JSON boundaries for the guarded codec."""
import ast
import json
import subprocess
from io import StringIO
from pathlib import Path
from _test_require import require
from decimal import Decimal
from _literal_json import InvalidJSON, dump, dumps, loads

def test_values() -> None:
    require(loads(' \t{"one": [true, null, 1.25, "a\\nb"]}\r\n') == {'one': [True, None, 1.25, 'a\nb']})
    require(loads(b'{"number": 1.20}', parse_float=Decimal) == {'number': Decimal('1.20')})
    require(loads('[[1]]', parse_int=Decimal) == [[Decimal(1)]])

def test_rejections() -> None:
    for value in ('', ' ', '{}x', '[]\xa0', '{"x":}', '[1,]', '1 2'):
        try:
            loads(value)
        except InvalidJSON as exc:
            require(len(exc.source_sha256) == 64)
            require(isinstance(exc.byte_span, tuple) and len(exc.byte_span) == 2)
            require(not hasattr(exc, 'lineno') and not hasattr(exc, 'colno'))
            require(exc.__context__ is None)
            continue
        raise AssertionError('invalid JSON accepted')

def test_scanner_boundary() -> None:
    original_value = json.scanner.make_scanner
    original_string = json.decoder.scanstring
    try:
        json.scanner.make_scanner = json.scanner.py_make_scanner
        try:
            loads('{}')
        except RuntimeError as exc:
            require('regex-free JSON scanner is unavailable' in str(exc))
        else:
            raise AssertionError('Python value scanner was accepted')
    finally:
        json.scanner.make_scanner = original_value
    try:
        json.decoder.scanstring = json.decoder.py_scanstring
        try:
            loads('{}')
        except RuntimeError as exc:
            require('regex-free JSON scanner is unavailable' in str(exc))
        else:
            raise AssertionError('Python string scanner was accepted')
    finally:
        json.decoder.scanstring = original_string


def test_encoder_boundary() -> None:
    expected = '{"text": "\\u2603"}'
    require(dumps({"text": "☃"}) == expected)
    output = StringIO()
    dump({"text": "☃"}, output)
    require(output.getvalue() == expected)
    class ForbiddenPattern:
        def sub(self, *args):
            raise AssertionError("regex JSON encoder was used")

    original_escape = json.encoder.ESCAPE
    original_escape_ascii = json.encoder.ESCAPE_ASCII
    try:
        json.encoder.ESCAPE = ForbiddenPattern()
        json.encoder.ESCAPE_ASCII = ForbiddenPattern()
        require("☃" in dumps({"text": "☃"}, ensure_ascii=False, indent=2))
        output = StringIO()
        dump({"text": "☃"}, output, ensure_ascii=True, indent=2)
        require("\\u2603" in output.getvalue())
    finally:
        json.encoder.ESCAPE = original_escape
        json.encoder.ESCAPE_ASCII = original_escape_ascii
    for active, fallback in (
        ("encode_basestring", "py_encode_basestring"),
        ("encode_basestring_ascii", "py_encode_basestring_ascii"),
    ):
        original = getattr(json.encoder, active)
        try:
            setattr(json.encoder, active, getattr(json.encoder, fallback))
            try:
                dumps({"text": "☃"})
            except RuntimeError as exc:
                require("regex-free JSON string encoder is unavailable" in str(exc))
            else:
                raise AssertionError(f"Python JSON string encoder was accepted: {active}")
        finally:
            setattr(json.encoder, active, original)


def test_stdlib_json_import_boundary() -> None:
    root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(  # nosec B603 # noqa: S603
        ["git", "ls-files", "-z", "--", "*.py"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    allowed = {
        Path("validators/_literal_json.py"),
        Path("validators/test_literal_json.py"),
        Path("tools/test_prepare_osv_python.py"),
    }
    observed: set[Path] = set()
    for raw in tracked.split(b"\0"):
        if not raw:
            continue
        relative = Path(raw.decode("utf-8"))
        tree = ast.parse((root / relative).read_text())
        for node in ast.walk(tree):
            direct = isinstance(node, ast.Import) and any(
                alias.name == "json" for alias in node.names
            )
            imported = isinstance(node, ast.ImportFrom) and node.module == "json"
            if direct or imported:
                observed.add(relative)
    require(observed == allowed, f"direct standard JSON imports changed: {sorted(observed ^ allowed)}")
if __name__ == '__main__':
    test_values()
    test_rejections()
    test_scanner_boundary()
    test_encoder_boundary()
    test_stdlib_json_import_boundary()
    print('literal JSON codec: accepted and rejected cases passed')
