"""Validate a selected profile declaration before adding it to discovery."""

from _literal_path import Path
import stat


def profile_candidates(repo_root: Path):
    """Yield present descriptors and reject profile links that cannot be read."""
    profiles_dir = repo_root / "profiles"
    try:
        entries = sorted(profiles_dir.iterdir())
    except OSError as exc:
        raise OSError(f"{profiles_dir}: cannot enumerate profiles ({exc})") from exc
    for entry in entries:
        try:
            entry_link = entry.is_symlink()
            entry_mode = entry.stat().st_mode
        except FileNotFoundError as exc:
            if entry.is_symlink():
                raise OSError(f"{entry}: dangling discovery directory") from exc
            continue
        except OSError as exc:
            raise OSError(f"{entry}: cannot inspect profile entry ({exc})") from exc
        if not stat.S_ISDIR(entry_mode):
            if entry_link:
                raise OSError(f"{entry}: profile link does not target a directory")
            continue
        candidate = entry / "PROFILE.toml"
        try:
            candidate.lstat()
            candidate_mode = candidate.stat().st_mode
        except FileNotFoundError as exc:
            if candidate.is_symlink():
                raise OSError(f"{candidate}: dangling discovery candidate") from exc
            continue
        except OSError as exc:
            raise OSError(f"{candidate}: cannot inspect profile descriptor ({exc})") from exc
        if not stat.S_ISREG(candidate_mode):
            raise OSError(f"{candidate}: profile descriptor is not a regular file")
        yield candidate


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
