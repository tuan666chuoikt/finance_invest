# Retro input (Scrum Master, 2026-10-16)

## Cost (cost.py, whole session 980c2e15 incl. sprint 0 planning, API-equivalent USD)
total 45.60 — main session 23.58 (52%), subagents 22.02. By model: opus 28.57 (incl. main), fable 10.85, sonnet 6.14, haiku 0.04.
Workflows: build 1.61M subagent tokens / 31 agents / 36 min; FIX run 0.41M / 9 agents / 7 min.

## Facts the SM observed
1. Main session ran in /home/stein/Desktop/Learning (not FI_ROOT) for two days: fi-* agents not registered → workflow "portable" mode (no maxTurns/omitClaudeMd/cacheTtl); main context very long → main = 52% of cost.
2. BE-schema landed ~410 lines vs 200 planned; neither dev nor lead invoked the 1.5x size stop.
3. FIX-only-validate: dev and lead both could not run pytest and the lead still APPROVED and merged; SM ran the kernel afterwards (82 pass); DB tests ran only in the tester's re-test.
4. Live tick crawl of 10-15 was cut by a session restart overnight; source stopped serving 10-15 by morning → 1,186 symbols lost. Time-bound live work was not a scheduled milestone with a clock time.
5. Two of the three FAIL findings were plan/contract-stage (architect), not build.
6. Containers write data/ as root; sponsor cannot clean data/ without sudo (S02-2).
7. The `partial` status rule counted no-trade symbols as skips (contract §4, fixed in v1.3).
8. A tester ran `sm.sh push` from the main checkout once and pushed sprint-01 by accident (harmless this time).
9. What worked: 0 dead agents, leads caught real defects in 4/8 tasks, fix loop closed 3 bugs in 7 minutes, live crawl 10-16 complete in 13 min.
