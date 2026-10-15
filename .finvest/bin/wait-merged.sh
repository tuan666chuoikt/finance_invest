#!/usr/bin/env bash
# wait-merged.sh <sprint> <dag-hash|-> [id...]
# Checks now, then every WAIT_STEP seconds (default 570, ~10 min) until WAIT_SECS (default 570) have passed:
# one call = two checks ~10 minutes apart, inside a 10-minute Bash timeout (600000 ms). Prints the ids merged into origin/<sprint> (one per line) and exits, or prints
# "DAG <hash>" when dag.json changed. Used by the workflow's haiku watcher (agents must not run a bare sleep).
. "$(dirname "$0")/env.sh"
S=$1; HASH=$2; shift 2
DAG="$FI_DIR/sprints/$S/dag.json"
STEP=${WAIT_STEP:-570}; TOTAL=${WAIT_SECS:-570}
end=$(( $(date +%s) + TOTAL ))
while :; do
  if [ "$HASH" != "-" ]; then now=$(md5sum "$DAG" 2>/dev/null | cut -d' ' -f1); if [ -n "$now" ] && [ "$now" != "$HASH" ]; then echo "DAG $now"; exit 0; fi; fi
  if [ $# -gt 0 ]; then
    git -C "$FI_ROOT" fetch -q origin 2>/dev/null
    L=$(git -C "$FI_ROOT" log --format=%s "origin/$S" 2>/dev/null)
    found=0
    for id in "$@"; do
      if echo "$L" | grep -qE "\($id\)\$" || git -C "$FI_ROOT" merge-base --is-ancestor "origin/task/$S/$id" "origin/$S" 2>/dev/null; then echo "$id"; found=1; fi
    done
    [ $found = 1 ] && exit 0
  fi
  [ $(( $(date +%s) + STEP )) -gt "$end" ] && exit 0
  sleep "$STEP"
done
