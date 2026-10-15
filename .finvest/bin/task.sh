#!/bin/sh
# Print one task's card. Usage: task.sh <TASK> [sprint-NN]
# Prints the `#### <TASK> —` block (from 2-tech-plan.md or 2-tech-plan.ai.md) up to the next heading, then
# the documents and sections it cites, so an agent reads its block once instead of searching the whole plan.
set -eu
. "$(dirname "$0")/env.sh"
T=${1:?usage: task.sh <TASK> [sprint-NN]}
S=${2:-$SPRINT}
for P in "$FI_DIR/sprints/$S/2-tech-plan.md" "$FI_DIR/sprints/$S/2-tech-plan.ai.md"; do
  [ -f "$P" ] || continue
  block=$(awk -v id="$T" '
    f && /^##/ { exit }
    $0 ~ "^#### " id "( |$)" { f = 1 }
    f { print }' "$P")
  if [ -n "$block" ]; then
    echo "($P)"
    printf '%s\n' "$block"
    echo
    echo "---- Cited (read only these; find one with: rg -n '<heading>' <doc>):"
    printf '%s\n' "$block" | grep -oE '(platform\.md|analytics\.md|codebase\.md|data\.md|system\.md|vn-market\.md|ADR-[SA]-[0-9]+|ux/[a-z0-9-]+\.md)[^;,)]{0,24}|§ ?[0-9]+(\.[0-9]+)*' | sort -u | head -30
    exit 0
  fi
done
echo "No '#### $T' block in sprint $S tech plans. Lines that name it:"
rg -n -m 10 -- "$T" "$FI_DIR/sprints/$S"/2-tech-plan*.md 2>/dev/null | cut -c1-240 | head -15
exit 1
