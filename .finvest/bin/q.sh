#!/bin/sh
# Quiet check wrapper. Usage: q.sh <label> <command...>
#   e.g. q.sh api-tests uv run pytest services/crawler/tests/test_ticks.py -q
#        q.sh e2e flock /tmp/fi-e2e.lock pnpm --filter web exec playwright test board --reporter=line
# The full output goes to /tmp/fi-q/<time>-<label>.log. Prints only: exit code, duration, summary lines and,
# on failure, the first failure lines. Read more with `sed -n` only if that is not enough. Exit code = the command's.
set -u
L=${1:?usage: q.sh <label> <command...>}; shift
D=/tmp/fi-q; mkdir -p "$D"
F="$D/$(date +%H%M%S)-$(printf '%s' "$L" | tr -c 'A-Za-z0-9._-' '_').log"
t0=$(date +%s)
"$@" >"$F" 2>&1; rc=$?
dt=$(( $(date +%s) - t0 ))
C="$F.clean"; sed -E 's/\x1B\[[0-9;?]*[A-Za-z]//g' "$F" >"$C"
echo "[$L] exit $rc in ${dt}s; full log: $F ($(wc -l <"$C" | tr -d ' ') lines)"
# Summary lines: pytest, ruff, mypy, vitest, playwright, tsc, eslint.
grep -E '^=+ .*(passed|failed|error).* =+$|^ *(Test Files|Tests|Duration) |[0-9]+ (passed|failed|flaky|skipped|did not run)|Found [0-9]+ errors?|Success: no issues|error TS[0-9]+|All checks passed|✖ [0-9]+ problems?|[0-9]+ problems? \(' "$C" | sort -u | head -12
if [ "$rc" -ne 0 ]; then
  echo "---- first failure lines:"
  grep -n -E '^FAILED |^ERROR |^E  |FAIL |✘|×|Error:|error TS|AssertionError|Expected|Received|  [0-9]+:[0-9]+ +error|Traceback|timed out' "$C" | head -40
fi
rm -f "$C"
exit "$rc"
