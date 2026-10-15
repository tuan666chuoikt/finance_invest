---
description: Build — run the sprint workflow in the background (dev → lead → fix → lead per task)
argument-hint: [all | TASK,TASK,...] [seats fe=2 be=2 ai=1]
---
Build. Argument: $ARGUMENTS

1. Run the workflow `/home/stein/Desktop/Learning/finance_invest/.finvest/bin/finvest-sprint.workflow.js` (Workflow tool, scriptPath) with args
   `{ sprint: "<current-sprint>", seats: {fe:2, be:2, ai:1}, leads: {fe:1, be:1} }`; add `only: [...]` when
   task ids are given. Default seats suit this machine; lower them if it is slow.
2. Log `sm build started "<n> tasks"` with `/home/stein/Desktop/Learning/finance_invest/.finvest/bin/log.sh`. Then **stop and wait**: do not poll agents.
   The workflow messages you on consult, 3rd review round, sponsor decision, dead agent, milestone.
3. On a message: decide whether it needs the sponsor (scope, money, risk) → ask in Vietnamese; else
   re-dispatch the owner per the rework routing in CLAUDE.md. A STOPPED task restarts with `stage` override.
4. Answer progress questions with `/fi-status`.
