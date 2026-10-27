"""Expose the repository JSON decoder to database commands."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "validators"))
from _literal_json import dump, dumps, loads  # noqa: E402, F401

__all__ = ['dump', 'dumps', 'loads']
