"""Load the repository's exact-option parser for database commands."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "validators"))
from _literal_args import ArgumentParser, Namespace  # noqa: E402, F401

__all__ = ['ArgumentParser', 'Namespace']
