"""Keep the historical public literal exception exact and fail closed."""

from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from _test_require import require
from check_secret_scan import (
    KNOWN_COMMITS, PUBLIC_HEX_FILE, PUBLIC_HEX_RULE,
    check_exact_config, check_findings, check_no_ignore_file, check_scan_population, gitleaks_command,
    known_public_literal, scanned_count, text_change_commits,
)


def test_exception() -> None:
    public = "".join(chr(code) for code in range(ord("0"), ord("9") + 1))
    public += "".join(chr(code) for code in range(ord("a"), ord("f") + 1))
    commit = sorted(KNOWN_COMMITS)[0]
    record = {"Secret": public, "RuleID": PUBLIC_HEX_RULE,
              "File": PUBLIC_HEX_FILE, "Commit": commit}
    require(known_public_literal(record))
    check_findings([record], {commit})
    for field, replacement in (
        ("Secret", public + "x"),
        ("RuleID", "other-rule"),
        ("File", "validators/other.toml"),
        ("Commit", "a" * 40),
    ):
        changed = record | {field: replacement}
        require(not known_public_literal(changed), "public exception widened")
        output = StringIO()
        try:
            with redirect_stderr(output):
                check_findings([changed], {commit})
        except RuntimeError:
            require("unapproved finding" in output.getvalue())
        else:
            raise AssertionError("unapproved finding was accepted")
    try:
        check_findings([], {commit})
    except RuntimeError:
        pass
    else:
        raise AssertionError("absent scanner control was accepted")


def test_scan_count() -> None:
    require(scanned_count("INF 12 commits scanned.\n") == 12)
    for output in ("", "INF scanned bytes", "INF 12 commits scanned.\nINF 12 commits scanned."):
        try:
            scanned_count(output)
        except RuntimeError:
            pass
        else:
            raise AssertionError("missing or duplicate scan count was accepted")

    head = {"head", "merge", "known"}
    all_commits = head | {"branch"}
    patches = {"head", "known"}
    check_scan_population(2, all_commits, head, {"known"}, patches)
    for count, reachable, ancestry, expected, patch_commits in (
        (0, all_commits, head, {"known"}, patches),
        (1, all_commits, head, {"known"}, patches),
        (3, all_commits, head, {"known"}, patches),
        (2, all_commits, head, {"branch"}, patches),
        (2, all_commits, set(), {"known"}, patches),
        (2, all_commits, head | {"unknown"}, {"known"}, patches),
        (3, all_commits, head, {"known"}, patches | {"unknown"}),
        (0, all_commits, head, {"known"}, set()),
    ):
        try:
            check_scan_population(count, reachable, ancestry, expected, patch_commits)
        except RuntimeError:
            pass
        else:
            raise AssertionError("invalid scan population was accepted")

    first, second = "a" * 40, "b" * 40
    numstat = (b"SCAN-COMMIT:" + first.encode() + b"\0\n2\t0\tfile\0"
               + b"SCAN-COMMIT:" + second.encode() + b"\0\n0\t2\tother\0")
    require(text_change_commits(numstat, {first, second}) == {first, second})
    rename = (b"SCAN-COMMIT:" + first.encode() + b"\0\n1\t1\t\0"
              + b"SCAN-COMMIT:" + second.encode() + b"\0new-name\0")
    require(text_change_commits(rename, {first, second}) == {first})
    for broken in (
        b"SCAN-COMMIT:short\0\n1\t0\tfile\0",
        b"SCAN-COMMIT:" + b"g" * 40 + b"\0\n1\t0\tfile\0",
        b"SCAN-COMMIT:" + second.encode() + b"\0\n1\t0\tfile\0",
        b"SCAN-COMMIT:" + first.encode() + b"\0\nnot-a-count\t0\tfile\0",
        b"SCAN-COMMIT:" + first.encode() + b"\0\n1\tbad\tfile\0",
        b"SCAN-COMMIT:" + first.encode() + b"\0\n-\t1\tbinary\0",
        b"SCAN-COMMIT:" + first.encode() + b"\0\n0\t0\tfile\0",
        b"SCAN-COMMIT:" + first.encode() + b"\0\n1\t0\t\0old-path\0",
        b"\n1\t0\tfile\0",
    ):
        try:
            text_change_commits(broken, {first})
        except RuntimeError:
            pass
        else:
            raise AssertionError("invalid Git numstat record was accepted")

    with TemporaryDirectory(prefix="gitleaks-ignore-control-") as directory:
        root = Path(directory)
        check_no_ignore_file(root)
        ignore = root / ".gitleaksignore"
        ignore.write_text("ignored-fingerprint\n")
        try:
            check_no_ignore_file(root)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Gitleaks ignore file was accepted")
        ignore.unlink()
        ignore.symlink_to("missing-file")
        try:
            check_no_ignore_file(root)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Gitleaks ignore symlink was accepted")
    require("--ignore-gitleaks-allow" in gitleaks_command(
        Path("/usr/bin/gitleaks"), ".gitleaks.toml", Path("findings.json")))


def test_main_rejects_ignore_file() -> None:
    with TemporaryDirectory(prefix="gitleaks-main-control-") as directory:
        root = Path(directory)
        binary = root / "gitleaks"
        binary.write_text("")
        (root / ".gitleaks.toml").write_text("[extend]\nuseDefault = true\n")
        ignore = root / ".gitleaksignore"
        ignore.write_text("ignored-fingerprint\n")
        command = [sys.executable, str(Path(__file__).with_name("check_secret_scan.py")),
                   "--gitleaks", str(binary), "--repo-root", str(root)]
        rejected = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603  # noqa: S603
        require(rejected.returncode == 1 and "Gitleaks ignore file is not permitted" in rejected.stderr)
        ignore.unlink()
        reached_history = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603  # noqa: S603
        require(reached_history.returncode == 1 and "secret scan requires a full Git checkout" in reached_history.stderr)


def test_config_boundary() -> None:
    repository_config = Path(__file__).resolve().parents[1] / ".gitleaks.toml"
    check_exact_config(repository_config)
    with TemporaryDirectory(prefix="gitleaks-config-control-") as directory:
        root = Path(directory)
        binary = root / "gitleaks"
        binary.write_text("")
        config = root / ".gitleaks.toml"
        main_command = [sys.executable, str(Path(__file__).with_name("check_secret_scan.py")),
                        "--gitleaks", str(binary), "--repo-root", str(root)]
        merge_command = [sys.executable, str(Path(__file__).with_name("check_secret_scan_merge.py")),
                         "--gitleaks", str(binary), "--config", str(config)]
        rejected_configs = (
            "[extend]\nuseDefault = true\n[[allowlists]]\npaths = ['validators/']\n",
            "[extend]\nuseDefault = true\n[[rules]]\nid = 'generic-api-key'\n[[rules.allowlists]]\npaths = ['validators/']\n",
            "[extend]\nuseDefault = true\ndisabledRules = ['generic-api-key']\n",
            "[extend]\nuseDefault = true\npath = 'other.toml'\n",
            "[extend]\nuseDefault = 1\n",
        )
        for content in rejected_configs:
            config.write_text(content)
            try:
                check_exact_config(config)
            except RuntimeError:
                pass
            else:
                raise AssertionError("suppressing Gitleaks configuration was accepted")
            for command in (main_command, merge_command):
                result = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603  # noqa: S603
                require(result.returncode != 0 and "default rule extension" in result.stderr)


if __name__ == "__main__":
    test_exception()
    test_scan_count()
    test_main_rejects_ignore_file()
    test_config_boundary()
    print("secret scan filter: exact accepted and rejected controls passed")
