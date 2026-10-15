---
description: Sprint planning — pm picks stories; architects write task plans and dag.json
argument-hint: [sprint goal]
---
Ceremony: sprint planning. Goal hint: $ARGUMENTS

1. Next sprint id = current + 1; write it to `/home/stein/Desktop/Learning/finance_invest/.finvest/current-sprint` and create the sprint folder.
2. `fi-pm` (opus): `1-sprint-plan.md`, `stories.tsv`, `milestones.tsv` (Definition of Ready in CLAUDE.md).
3. `fi-ai-architect` (fable): `2-tech-plan.ai.md` for AI stories (skip if none).
4. `fi-software-architect` (fable): `2-tech-plan.md` + `dag.json` merging all tasks
   (template `/home/stein/Desktop/Learning/finance_invest/.finvest/templates/dag.example.json`), effort and lead model per task.
5. Sanity-check yourself, cheaply: `python3 -c` that dag.json parses, every `after` id exists, no cycle,
   and `/home/stein/Desktop/Learning/finance_invest/.finvest/bin/task.sh <id>` prints a block for 3 random ids. Report failures to the architect, do not fix.
6. Relay: goal, points, task count per side, milestones. **Gate:** sponsor says go → `/fi-build`.
