"""Accept real Git revision forms and reject option-shaped input."""

from contextlib import redirect_stdout
from io import StringIO
from string import hexdigits
import shutil
import subprocess

from _test_require import require
from check_ai_attribution import identity_has_stamp, main, message_has_stamp, valid_revision


def test_revisions() -> None:
    base = "a1B2" * 10
    head = "F9c0" * 10
    require(valid_revision(base))
    require(valid_revision(base + ".." + head))
    require(valid_revision("refs/remotes/origin/main.." + head))
    for value in ("", "--all", "HEAD", "g" * 40, "Ａ" * 40,
                  "refs/remotes/origin/../main.." + head,
                  base + "..--all", "refs/remotes/origin/main~1.." + head):
        require(not valid_revision(value), "unsafe Git revision accepted")
    for code in range(128):
        char = chr(code)
        require(valid_revision(char * 40) == (char in hexdigits),
                "ASCII SHA character boundary changed")


def test_stamps() -> None:
    require(message_has_stamp("Co-authored-by: Claude <example@example.org>"))
    require(message_has_stamp("Generated with Claude Code"))
    require(not message_has_stamp("The ontology names anthropic as an example provider."))
    require(identity_has_stamp("Claude Example"))
    require(not identity_has_stamp("Release Maintainer"))


def test_empty_introduced_range() -> None:
    git = shutil.which("git")
    require(git is not None, "Git is required for the empty-range control")
    head = subprocess.run(  # nosec B603  # noqa: S603
        [git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
    ).stdout.strip()
    output = StringIO()
    with redirect_stdout(output):
        require(main([head + ".." + head]) == 0)
    require(output.getvalue() == "OK: checked 0 introduced commits for attribution stamps\n")


if __name__ == "__main__":
    test_revisions()
    test_stamps()
    test_empty_introduced_range()
    print("attribution gate: revision and stamp boundaries passed")
