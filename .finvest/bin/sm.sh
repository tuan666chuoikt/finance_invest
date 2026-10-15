#!/usr/bin/env bash
# Git helper for agents and the Scrum Master. Never forces, never touches dev/main.
#   sm.sh push [base]           (in a worktree) push the current task/test branch to origin
#   sm.sh pr <TASK> [base]      open a GitHub PR if `gh` is installed and logged in; else print "branch-only"
#   sm.sh merge <TASK> <H>      (lead, in the task worktree) --no-ff merge of reviewed head H into sprint-NN, push under the merge lock
#   sm.sh finvest "<message>"   (Scrum Master, main checkout) commit .finvest/ artifacts on the current branch
set -euo pipefail
. "$(dirname "$0")/env.sh"
cmd=${1:?usage: sm.sh push|pr|merge|finvest ...}; shift
br=$(git rev-parse --abbrev-ref HEAD)
guard() { case "$1" in main|dev) echo "refused: never on $1"; exit 3;; esac; }

case "$cmd" in
push)
  guard "$br"
  git push -u origin "$br" 2>&1 | tail -3 ;;
pr)
  T=${1:?sm.sh pr <TASK> [base]}; base=${2:-$SPRINT}
  if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
    gh pr create --base "$base" --head "$br" --title "$T: $(git log -1 --format=%s)" \
      --body "Task $T. Details: .finvest/sprints/$SPRINT/3-build.$T.md" 2>&1 | tail -1
  else
    echo "branch-only: $br (no gh; the lead reviews the branch directly)"
  fi ;;
merge)
  T=${1:?sm.sh merge <TASK> <H>}; H=${2:?reviewed head sha}
  [ "$(git rev-parse HEAD)" = "$(git rev-parse "$H")" ] || { echo "refused: HEAD moved since review ($H)"; exit 4; }
  [ -z "$(git status --porcelain)" ] || { echo "refused: dirty worktree"; exit 4; }
  [ -f "$SPRINT_DIR/3-pr.$T.md" ] && grep -q 'APPROVE' "$SPRINT_DIR/3-pr.$T.md" || { echo "refused: no APPROVE in 3-pr.$T.md"; exit 4; }
  git fetch -q origin
  B=$(git rev-parse "origin/$SPRINT")
  git checkout -q --detach "$B"
  git merge -q --no-ff -m "merge: $br ($T)" "$H"
  M=$(git rev-parse HEAD)
  flock /tmp/fi-merge.lock bash -c '
    git fetch -q origin
    [ "$(git rev-parse origin/'"$SPRINT"')" = "'"$B"'" ] || { echo "base moved; re-sync and re-run checks"; exit 5; }
    git push -q origin HEAD:refs/heads/'"$SPRINT"''
  git checkout -q "$br"
  echo "merged $T: base $B head $H merge $M" ;;
finvest)
  msg=${1:?sm.sh finvest "<message>"}
  cd "$FI_ROOT"; guard "$(git rev-parse --abbrev-ref HEAD)"
  git add .finvest
  git diff --cached --quiet && { echo "nothing to commit"; exit 0; }
  git commit -q -m "$msg" && git log -1 --format='%h %s' ;;
*) echo "unknown: $cmd"; exit 2 ;;
esac
