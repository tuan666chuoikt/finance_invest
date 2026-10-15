# Sourced by every Finvest script. The only place the absolute paths live.
FI_ROOT=${FI_ROOT:-/home/stein/Desktop/Learning/finance_invest}
FI_DIR="$FI_ROOT/.finvest"
WT="${FI_WORKTREES:-/home/stein/Desktop/Learning/finance_invest-worktrees}"
SPRINT=$(cat "$FI_DIR/current-sprint" 2>/dev/null || echo sprint-00)
SPRINT_DIR="$FI_DIR/sprints/$SPRINT"
