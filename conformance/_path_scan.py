"""Load the explicit path enumerator for conformance commands."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validators"))
from _literal_paths import glob, rglob  # noqa: E402, F401
