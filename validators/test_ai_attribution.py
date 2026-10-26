"""Accept real Git revision forms and reject option-shaped input."""

from _test_require import require
from check_ai_attribution import identity_has_stamp, message_has_stamp, valid_revision


def test_revisions() -> None:
    base = "a" * 40
    head = "B" * 40
    require(valid_revision(base))
    require(valid_revision(base + ".." + head))
    require(valid_revision("refs/remotes/origin/main.." + head))
    for value in ("", "--all", "HEAD", "g" * 40, "Ａ" * 40,
                  "refs/remotes/origin/../main.." + head,
                  base + "..--all", "refs/remotes/origin/main~1.." + head):
        require(not valid_revision(value), "unsafe Git revision accepted")


def test_stamps() -> None:
    require(message_has_stamp("Co-authored-by: Claude <example@example.org>"))
    require(message_has_stamp("Generated with Claude Code"))
    require(not message_has_stamp("The ontology names anthropic as an example provider."))
    require(identity_has_stamp("Claude Example"))
    require(not identity_has_stamp("Release Maintainer"))


if __name__ == "__main__":
    test_revisions()
    test_stamps()
    print("attribution gate: revision and stamp boundaries passed")
