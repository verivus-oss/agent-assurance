"""Pinned database downloads require HTTPS and an exact digest."""

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import os

from _test_require import require
from database_ci import download


def main() -> None:
    with TemporaryDirectory(prefix="database-download-") as work:
        root = Path(work)
        curl = root / "curl"
        curl.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "want = ['--fail', '--location', '--silent', '--show-error', "
            "'--max-time', '60', '--proto', '=https', '--proto-redir', '=https', "
            "'https://example.org/archive']\n"
            "if sys.argv[1:] != want:\n"
            "    raise SystemExit(1)\n"
            "sys.stdout.buffer.write(b'pinned archive')\n"
        )
        curl.chmod(0o755)
        target = root / "archive"
        previous = os.environ.get("PATH")
        os.environ["PATH"] = str(root) + os.pathsep + (previous or "")
        try:
            digest = sha256(b"pinned archive").hexdigest()
            download("https://example.org/archive", digest, target)
            require(target.read_bytes() == b"pinned archive")
            for url, checksum, error in (
                ("http://example.org/archive", digest, ValueError),
                ("https://example.org/archive", "0" * 64, ValueError),
                ("https://example.org/other", digest, RuntimeError),
            ):
                try:
                    download(url, checksum, root / "rejected")
                except error:
                    pass
                else:
                    raise AssertionError("unsafe or unpinned download was accepted")
            require(not (root / "rejected").exists())
        finally:
            if previous is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = previous
    print("database download: HTTPS, digest, and redirect controls passed")


if __name__ == "__main__":
    main()
