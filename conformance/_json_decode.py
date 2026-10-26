"""Expose the repository JSON decoder to conformance commands."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validators"))
from _literal_json import loads  # noqa: E402, F401
