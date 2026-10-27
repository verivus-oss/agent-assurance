"""Prove merge, deletion, and inline-allow secret scan boundaries."""

from _literal_args import ArgumentParser
from _literal_json import loads as loads_json
from check_secret_scan import (
    GIT_LOG_OPTIONS, check_exact_config, gitleaks_command, patch_bearing_commits,
    reachable_commits, scanned_count,
)
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory


def run(command: list[str], root: Path, allowed: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(  # nosec B603  # noqa: S603
        command, cwd=root, capture_output=True, text=True, check=False,
    )
    if result.returncode not in allowed:
        raise RuntimeError("merge scan control command failed: " + command[1])
    return result


def check(gitleaks: Path, config: Path) -> None:
    git = shutil.which("git")
    if git is None or not gitleaks.is_file() or not config.is_file():
        raise RuntimeError("git, Gitleaks, and its configuration are required")
    check_exact_config(config)
    with TemporaryDirectory(prefix="gitleaks-merge-control-") as directory:
        root = Path(directory)
        record = root / "credential.txt"
        run([git, "init", "-q", "-b", "main"], root)
        run([git, "config", "user.name", "Scan Control"], root)
        run([git, "config", "user.email", "control@example.org"], root)
        record.write_text("token=base\n")
        run([git, "add", "credential.txt"], root)
        run([git, "commit", "-qm", "base"], root)
        run([git, "branch", "feature"], root)
        record.write_text("token=main\n")
        run([git, "commit", "-qam", "main"], root)
        run([git, "checkout", "-q", "feature"], root)
        record.write_text("token=feature\n")
        run([git, "commit", "-qam", "feature"], root)
        run([git, "checkout", "-q", "main"], root)
        merge = run([git, "merge", "feature"], root, allowed=(0, 1))
        if merge.returncode != 1:
            raise RuntimeError("merge control did not create a conflict")
        secret = "ghp_" + "Ab12Cd34Ef56Gh78Ij90Kl12Mn34Op56Qr78"
        record.write_text("token=" + secret + "\n")
        run([git, "add", "credential.txt"], root)
        run([git, "commit", "-qm", "resolve conflict"], root)
        merge_sha = run([git, "rev-parse", "HEAD"], root).stdout.strip()

        def findings(log_options: str, name: str, ignore_allow: bool = True) -> tuple[list, int]:
            report = root / (name + ".json")
            command = gitleaks_command(gitleaks, str(config), report, log_options)
            if not ignore_allow:
                command.remove("--ignore-gitleaks-allow")
            result = run(
                command,
                root, allowed=(0, 1),
            )
            records = loads_json(report.read_text())
            if not isinstance(records, list) or (result.returncode == 0) != (len(records) == 0):
                raise RuntimeError("merge control report and exit status disagree")
            return records, scanned_count(result.stdout + "\n" + result.stderr)

        old, _ = findings("--all", "without-merges")
        if any(item.get("Commit") == merge_sha for item in old):
            raise RuntimeError("merge control no longer distinguishes the scan options")
        current, _ = findings(GIT_LOG_OPTIONS, "with-merges")
        detected = [item for item in current if item.get("Commit") == merge_sha
                    and item.get("Secret") == secret]
        if not detected:
            raise RuntimeError("merge resolution credential was not scanned")

        record.write_text("")
        run([git, "commit", "-qam", "delete credential line"], root)
        deletion_sha = run([git, "rev-parse", "HEAD"], root).stdout.strip()
        reachable, _ = reachable_commits(root)
        patch_commits = patch_bearing_commits(root, reachable)
        _, count = findings(GIT_LOG_OPTIONS, "with-deletion")
        if deletion_sha not in patch_commits or count != len(patch_commits):
            raise RuntimeError("deletion-only text commit was not counted")

        record.write_text("token=" + secret + " # gitleaks:allow\n")
        run([git, "commit", "-qam", "inline allow control"], root)
        inline_sha = run([git, "rev-parse", "HEAD"], root).stdout.strip()
        suppressed, _ = findings(GIT_LOG_OPTIONS, "inline-suppressed", ignore_allow=False)
        if any(item.get("Commit") == inline_sha for item in suppressed):
            raise RuntimeError("inline allow control did not suppress the finding")
        enforced, _ = findings(GIT_LOG_OPTIONS, "inline-enforced")
        if not any(item.get("Commit") == inline_sha and item.get("Secret") == secret
                   for item in enforced):
            raise RuntimeError("inline allow bypassed the active secret scan")
        print(f"secret scan controls: {len(detected)} merge-parent findings, deletion and inline allow enforced")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--gitleaks", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    check(Path(args.gitleaks).resolve(), Path(args.config).resolve())
