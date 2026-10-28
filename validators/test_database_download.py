"""Pinned database downloads require HTTPS and an exact digest."""

from hashlib import sha256
from _literal_path import Path
from tempfile import TemporaryDirectory
import io
import os
import tarfile

from _test_require import expect_raises, require
from database_ci import download, extract_source


def extraction_boundaries(root):
    archive = root / "source.tar"
    source = root / "source"
    source.mkdir()
    content = b"source bytes"
    with tarfile.open(archive, "w", format=tarfile.GNU_FORMAT) as contents:
        for name in ("short.txt", "nested/" + "a" * 110):
            member = tarfile.TarInfo(name)
            member.size = len(content)
            contents.addfile(member, io.BytesIO(content))
        link = tarfile.TarInfo("hardlink")
        link.type, link.linkname = tarfile.LNKTYPE, "short.txt"
        contents.addfile(link)
    extract_source(archive, source)
    require((source / "short.txt").read_bytes() == content)
    require((source / "nested" / ("a" * 110)).read_bytes() == content)
    require((source / "hardlink").read_bytes() == content)

    # An extended header must fail before the standard PAX parser runs.
    parser = tarfile.TarInfo._proc_pax
    def forbidden_pax(*_args):
        raise AssertionError("standard PAX parser was reached")
    tarfile.TarInfo._proc_pax = forbidden_pax
    try:
        for kind in (tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.SOLARIS_XHDTYPE):
            with tarfile.open(archive, "w") as contents:
                member = tarfile.TarInfo("extended")
                member.type = kind
                contents.addfile(member)
            error = expect_raises(ValueError, lambda: extract_source(archive, source),
                                  "extended tar header was accepted")
            require("PAX extended headers" in str(error))
    finally:
        tarfile.TarInfo._proc_pax = parser

    for name in ("../escaped", str(root / "absolute")):
        with tarfile.open(archive, "w") as contents:
            member = tarfile.TarInfo(name)
            member.size = len(content)
            contents.addfile(member, io.BytesIO(content))
        if name.startswith("/"):
            # The data filter strips the leading slash and confines the member.
            extract_source(archive, source)
            require(not (root / "absolute").exists())
        else:
            expect_raises(tarfile.FilterError, lambda: extract_source(archive, source),
                          "escaping tar member was accepted")
            require(not (root / "escaped").exists())


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
                expect_raises(error, lambda: download(url, checksum, root / "rejected"),
                              "unsafe or unpinned download was accepted")
            require(not (root / "rejected").exists())
        finally:
            if previous is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = previous
        extraction_boundaries(root)
    print("database download: HTTPS, digest, redirect, and source extraction controls passed")


if __name__ == "__main__":
    main()
