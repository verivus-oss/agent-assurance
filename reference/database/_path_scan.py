"""Expose owned path primitives and explicit discovery to local commands."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "validators"))
from _literal_path import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath  # noqa: E402, F401
from _literal_paths import glob, rglob  # noqa: E402, F401

__all__ = ["Path", "PosixPath", "PurePath", "PurePosixPath", "PureWindowsPath", "WindowsPath", "glob", "rglob"]
