"""Expose the repository JSON decoder to conformance commands."""

from _path_scan import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validators"))
from _literal_json import dump, dumps, loads  # noqa: E402, F401

__all__ = ['dump', 'dumps', 'loads']
