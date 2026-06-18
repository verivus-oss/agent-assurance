#!/usr/bin/env bash
# Verification harness for the hardened no-ai-attribution gate.
# Replicates the workflow's two checks exactly and asserts expected verdicts.
R=/srv/repos/external/verivus-oss/agent-assurance
MSG_PATTERN='co-authored-by:.*(claude|anthropic)|generated with.*claude'
ID_PATTERN='anthropic|claude'
fails=0

# verdict for a single commit in repo $1 at sha $2 -> prints "msg=HIT/miss id=HIT/miss"
verdict() {
  local repo="$1" sha="$2" m i
  if git -C "$repo" log -n1 --format='%h %s%n%b' "$sha" | grep -qiE "$MSG_PATTERN"; then m=HIT; else m=miss; fi
  if git -C "$repo" log -n1 --format='%h|%an|%ae|%cn|%ce' "$sha" | grep -qiE "$ID_PATTERN"; then i=HIT; else i=miss; fi
  echo "msg=$m id=$i"
}
assert() { # label  actual  expected
  if [ "$2" = "$3" ]; then printf 'PASS  %-52s %s\n' "$1" "$2"; else printf 'FAIL  %-52s got[%s] want[%s]\n' "$1" "$2" "$3"; fails=$((fails+1)); fi
}

echo "########## REAL commits in agent-assurance ##########"
assert "leaked branch 4a8668c (Werner+Claude co-author)"  "$(verdict "$R" 4a8668cb38)" "msg=HIT id=miss"
assert "leaked branch 5bc75c9"                            "$(verdict "$R" 5bc75c9b93)" "msg=HIT id=miss"
assert "leaked SQUASH a3e86f6 (#21 merge_commit)"         "$(verdict "$R" a3e86f6009)" "msg=HIT id=miss"
assert "leaked SQUASH b8d7a026 (#22 merge_commit)"        "$(verdict "$R" b8d7a026b7)" "msg=HIT id=miss"
assert "clean #21 repl aa5a0b2 (no false positive)"       "$(verdict "$R" aa5a0b2c1f)" "msg=miss id=miss"
assert "clean #22 repl 57b1350"                           "$(verdict "$R" 57b1350133)" "msg=miss id=miss"
assert "current main tip 3419e1a"                         "$(verdict "$R" 3419e1a3dc)" "msg=miss id=miss"
assert "PR#27 GitHub+Werner co-author (no FP)"            "$(verdict "$R" 21d40e4372)" "msg=miss id=miss"
assert "PR#29 dependabot co-author (no FP)"               "$(verdict "$R" 5fe8f98a14)" "msg=miss id=miss"

echo
echo "########## SYNTHETIC vectors in throwaway repo ##########"
T=$(mktemp -d)
git -C "$T" init -q
git -C "$T" config user.name "verivusOSS-releases"
git -C "$T" config user.email "oss-release@verivus.com"

# clean
echo a > "$T/a"; git -C "$T" add -A; git -C "$T" commit -q --no-verify -m "feat: clean commit"
assert "synthetic clean commit"                           "$(verdict "$T" HEAD)" "msg=miss id=miss"

# message vector: co-author trailer (repeated -m -> subject\n\nbody)
echo b > "$T/b"; git -C "$T" add -A
git -C "$T" commit -q --no-verify -m "feat: x" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
assert "synthetic co-author trailer (msg vector)"         "$(verdict "$T" HEAD)" "msg=HIT id=miss"

# message vector: generated-with footer
echo c > "$T/c"; git -C "$T" add -A
git -C "$T" commit -q --no-verify -m "feat: y" -m "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
assert "synthetic generated-with footer (msg vector)"     "$(verdict "$T" HEAD)" "msg=HIT id=miss"

# identity vector: commit AUTHORED by Claude/anthropic email, clean message
echo d > "$T/d"; git -C "$T" add -A
GIT_AUTHOR_NAME="Claude" GIT_AUTHOR_EMAIL="noreply@anthropic.com" \
  git -C "$T" commit -q --no-verify -m "feat: z (clean message, anthropic author)"
assert "synthetic anthropic AUTHOR identity (id vector)"  "$(verdict "$T" HEAD)" "msg=miss id=HIT"

# simulated GitHub squash: clean subject + auto-appended co-author trailer
echo e > "$T/e"; git -C "$T" add -A
git -C "$T" commit -q --no-verify -m "feat: squashed feature (#99)" -m "Squashed branch work." \
  -m "Co-authored-by: Werner Kasselman <werner@verivus.com>" \
  -m "Co-authored-by: Claude Opus 4.8 <noreply@anthropic.com>"
assert "simulated squash w/ appended trailer (msg vector)" "$(verdict "$T" HEAD)" "msg=HIT id=miss"

rm -rf "$T"

echo
echo "########## new-branch push FALLBACK regression (Codex blocker) ##########"
# New branch: BAD first introduced commit + CLEAN tip. The OLD fallback
# (-n 1 <tip>) scanned only the tip and MISSED the earlier bad commit
# (fail-open). The FIX scans the introduced range (default-branch..AFTER).
B2=$(mktemp -d); git -C "$B2" init -q
git -C "$B2" config user.name "verivusOSS-releases"; git -C "$B2" config user.email "oss-release@verivus.com"
echo base > "$B2/base"; git -C "$B2" add -A; git -C "$B2" commit -q --no-verify -m "feat: base on default branch"
git -C "$B2" branch -M main
echo x > "$B2/x"; git -C "$B2" checkout -q -b feature; git -C "$B2" add -A
git -C "$B2" commit -q --no-verify -m "feat: bad first" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
echo y > "$B2/y"; git -C "$B2" add -A; git -C "$B2" commit -q --no-verify -m "feat: clean tip"
TIP=$(git -C "$B2" rev-parse HEAD)
if git -C "$B2" log -n1 --format='%h %s%n%b' "$TIP" | grep -qiE "$MSG_PATTERN"; then old=HIT; else old=miss; fi
assert "OLD fallback (-n1 tip) was fail-open (miss==bug)" "$old" "miss"
if git -C "$B2" log --format='%h %s%n%b' "main..$TIP" | grep -qiE "$MSG_PATTERN"; then new=HIT; else new=miss; fi
assert "FIX fallback (range main..AFTER) catches it"      "$new" "HIT"
rm -rf "$B2"

echo
echo "########## stale-local-\$DEF regression (Codex r2 blocker) ##########"
# A divergent LOCAL 'main' that already contains the buried bad commit would,
# under the removed 'elif $DEF..$AFTER' tier, EXCLUDE that commit from the
# range (miss). With no remote-tracking ref present, the FIX selects the
# fail-closed full scan of $AFTER, which still catches it.
S=$(mktemp -d); git -C "$S" init -q
git -C "$S" config user.name "verivusOSS-releases"; git -C "$S" config user.email "oss-release@verivus.com"
echo a > "$S/a"; git -C "$S" add -A; git -C "$S" commit -q --no-verify -m "feat: base"
echo b > "$S/b"; git -C "$S" add -A
git -C "$S" commit -q --no-verify -m "feat: bad buried" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
git -C "$S" branch -M main                  # stale/divergent local 'main' already contains the bad commit
git -C "$S" checkout -q -b feature
echo c > "$S/c"; git -C "$S" add -A; git -C "$S" commit -q --no-verify -m "feat: clean tip"
TIP=$(git -C "$S" rev-parse HEAD)
# removed tier: local main..tip excludes the bad commit (the danger Codex found)
if git -C "$S" log --format='%h %s%n%b' "main..$TIP" | grep -qiE "$MSG_PATTERN"; then stale=HIT; else stale=miss; fi
assert "removed local-\$DEF tier (main..tip) MISSES buried bad" "$stale" "miss"
# fix: no refs/remotes/origin/main here -> selection falls to full scan of AFTER
if git -C "$S" rev-parse --verify --quiet "refs/remotes/origin/main^{commit}" >/dev/null; then sel="origin"; else sel="fullscan"; fi
assert "no remote-tracking ref -> selection is fullscan"       "$sel" "fullscan"
if git -C "$S" log --format='%h %s%n%b' "$TIP" | grep -qiE "$MSG_PATTERN"; then fs=HIT; else fs=miss; fi
assert "FIX full scan of AFTER catches the buried bad"         "$fs" "HIT"
rm -rf "$S"

echo
if [ "$fails" -eq 0 ]; then echo "ALL ASSERTIONS PASSED"; else echo "$fails ASSERTION(S) FAILED"; fi
exit "$fails"
