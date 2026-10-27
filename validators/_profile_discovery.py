"""Validate a selected profile declaration before adding it to discovery."""

from pathlib import Path


def profile_name(doc: dict, path: Path) -> str:
    meta = doc.get("meta")
    profile = doc.get("profile")
    if not isinstance(meta, dict) or meta.get("template_kind") != "profile-descriptor":
        raise ValueError(f"{path}: expected a profile-descriptor declaration")
    if not isinstance(profile, dict):
        raise ValueError(f"{path}: missing [profile] table")
    name = profile.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"{path}: [profile].name must be a nonempty string")
    return name
