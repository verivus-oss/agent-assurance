import re
pattern = re.compile(r"(?im)^\s*co-authored-by:.*\b(ai|bot|assistant|llm)\b[^@\s]*@")
print("github-actions:", bool(pattern.search("Co-authored-by: github-actions[bot] <github-actions[bot]@users.noreply.github.com>")))
print("dependabot:", bool(pattern.search("Co-authored-by: dependabot[bot] <dependabot[bot]@users.noreply.github.com>")))
print("renovate:", bool(pattern.search("Co-authored-by: renovate[bot] <renovate[bot]@users.noreply.github.com>")))
print("botond:", bool(pattern.search("Co-authored-by: Some Human <botond@example.com>")))
print("botond name:", bool(pattern.search("Co-authored-by: Botond Nagy <some@example.com>")))
