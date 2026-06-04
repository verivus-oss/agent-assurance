import re
import tomllib

with open("policy/REPO_POLICY.toml", "rb") as f:
    policy = tomllib.load(f)

# Find the NO-AI-ATTRIBUTION contract
contract = next(c for c in policy["contracts"] if c["id"] == "REG:NO-AI-ATTRIBUTION")
patterns = [re.compile(p) for p in contract["blacklist_regex"]]

cases = [
    ("Co-Authored-By: Claude Opus <noreply@anthropic.com>", True),
    ("we removed the Co-Authored-By trailers from history", False),
    ("🤖 Generated with Claude Code", True),
    ("Generated with great care by Werner", False),
    ("Co-authored-by: Jane Smith <jane@example.com>", False),
    ("co-authored-by: GitHub Copilot <copilot@github.com>", True),
    ("Co-authored-by: AI Assistant <bot@example.com>", True),
    ("Co-authored-by: Perplexity <bot@perplexity.ai>", True),
    ("Co-authored-by: Codeium <bot@codeium.com>", True),
    ("Co-authored-by: Bob <bob@users.noreply.github.com>", False),
    ("Co-authored-by: Botond Nagy <botond@example.com>", False),
    ("Co-authored-by: Aida Smith <aida@example.com>", False),
    ("Co-authored-by: Agent Smith <agent.smith@example.com>", False),
    ("feat: tidy validators — Generated with Claude Code", True),
    ("Generated with Perplexity", True),
    ("Generated with Codeium", True),
    ("the footer said generated with claude code", True),
    ("Generated with Assistant", True),
    ("Co-authored-by: Cody Johnson <cody@example.com>", False),
    ("Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>", False),
    ("Co-authored-by: github-actions[bot] <github-actions[bot]@users.noreply.github.com>", False),
    ("This bug was generated with a script written by Devin", False),
    ("Co-authored-by: Jean-Claude Van Damme <jc@example.com>", True),
    ("Co-authored-by: Sourcegraph Cody <cody@sourcegraph.com>", True),
]

all_pass = True
for i, (text, expected) in enumerate(cases, 1):
    matched = any(p.search(text) for p in patterns)
    if matched != expected:
        print(f"Case {i} FAIL: '{text}' matched={matched}, expected={expected}")
        all_pass = False
    else:
        print(f"Case {i} PASS: '{text}' matched={matched}")

if all_pass:
    print("ALL 24 PASS")
else:
    print("SOME FAIL")
