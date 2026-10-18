# Common rules for every Finvest agent (read first)

- **Paths are absolute.**
  - FI_ROOT=/home/stein/Desktop/Learning/finance_invest
  - FI_DIR=$FI_ROOT/.finvest ; SPRINT_DIR=$FI_DIR/sprints/$(cat $FI_DIR/current-sprint)
  - Worktrees: /home/stein/Desktop/Learning/finance_invest-worktrees/<TASK>
  - Scripts always from the main checkout: `$FI_DIR/bin/<script>` (never a worktree copy).
- **Read lean.** Every turn re-reads your whole context, so every output you pull in is paid again on
  every later turn.
  - Never `cat` a file over ~300 lines: `rg -n '<heading>' <file>` then `sed -n '<a>,<b>p' <file>`.
  - Search with ripgrep, always bounded: `rg -l`, `rg -n -m 5`, `| head -40`. No `find` without
    `-maxdepth` or `| head`. Batch several small reads into one Bash call.
  - Run every check through the quiet wrapper: `$FI_DIR/bin/q.sh <label> <cmd...>` (prints exit code,
    summary and first failure lines; the full log stays in `/tmp/fi-q/`).
- **Think briefly** on routine steps (running commands, git, reading, writing the report). Think fully
  only on design, contracts, money/return calculations, data correctness, auth, and a failure you do
  not yet understand.
- **Locks:** only `flock /tmp/fi-{test,e2e,merge}.lock <cmd>`. Never create or delete lock files by hand.
- **Domain truth:** `$FI_DIR/knowledge/vn-market.md` (lots, price bands, fees, tax, T+2, corporate
  actions, sessions). Cite its section when you rely on it; never invent market rules.
- **Data sources are free only.** No paid API, no broker login stored in code. Respect rate limits and
  cache everything you fetch.
- **Secrets** come from `.env` (git-ignored). Never print, log or commit them.
- **Git:** never bare `git stash` (use a WIP commit); never force-push or rewrite shared history; never
  merge into `dev`/`main`.
- **Last step, always:** one activity line:
  `$FI_DIR/bin/log.sh <role> <task-or-PR> <event> "<result with real numbers>" <report path>`
  (events: started built pr-open changes approved merged blocked consult answered red green note).
- **Hand-back:** at most **5 lines**: result, branch/sha, blockers, report path. Detail goes in your file.
- **Wait loops:** cap every loop (`for i in $(seq 1 90)`), match processes as `'[p]laywright'`, and stop
  any loop you started before handing back. Never a bare long `sleep`.
- **Node toolchain on this machine (2026-10-18):** Node 18.20, npm 10; **pnpm is not installed** and there is no
  sudo. Use npm (lockfile `package-lock.json`), or `npx -y pnpm@9` if the plan insists. Pin tools that support
  Node 18 (e.g. Vite ≤ 6, Vitest ≤ 2); Vite 7 needs Node 20.
