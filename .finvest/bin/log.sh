#!/usr/bin/env bash
# Append ONE line to the active sprint's activity log (append-only; each agent writes its own line).
# usage: log.sh <role> <task-or-PR> <event> "<result, real numbers, <=140 chars>" [report path]
# roles:  dev | lead | arch | ai-arch | pm | po | fe-test | be-test | sm
# events: started built pr-open changes approved merged blocked consult answered red green stopped decision note
set -euo pipefail
. "$(dirname "$0")/env.sh"
[ $# -ge 3 ] || { echo "usage: log.sh <role> <task> <event> \"<result>\" [report]"; exit 2; }
role=$1 task=$2 event=$3 result=${4:-} report=${5:--}
result=$(printf '%s' "$result" | tr '\n|' '  ' | cut -c1-140)
report=${report#"$SPRINT_DIR/"}
mkdir -p "$SPRINT_DIR"
line=$(printf '%s | %-7s | %-24s | %-9s | %s | %s' "$(date '+%Y-%m-%d %H:%M')" "$role" "$task" "$event" "$result" "$report")
flock /tmp/fi-activity.lock sh -c 'printf "%s\n" "$1" >> "$2"' _ "$line" "$SPRINT_DIR/activity.log"
echo "logged: $line"
