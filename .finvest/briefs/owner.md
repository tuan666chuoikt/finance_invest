# Owner brief (po, pm, software architect, ai architect). Also follow common.md.

## Artifacts — one writer per file

```
.finvest/
  product/
    brief.md                  sponsor (input; only the sponsor changes it)
    sponsor-answers.md        Scrum Master appends the sponsor's words verbatim
    prd.md                    po     PR-### requirements, metrics, scope, release criteria
    backlog.md                pm     epics + stories F-### (trace to PR-###), G/W/T, points, status
    roadmap.md                pm     releases, sprint timeline, velocity
    ux/<screen>.md            pm     UX specs (states: empty, loading, error, stale data, market closed)
  knowledge/vn-market.md      ai-architect (domain rules; the software architect may propose edits)
  architecture/
    system.md                 software-architect   NFRs, stack, components, deployment
    codebase.md               software-architect   bounded contexts, module map, layering, conventions, test kernel
    data.md                   software-architect   schemas, retention, crawl schedules, storage tiers
    analytics.md              ai-architect         backtest engine, metrics, attribution ("why it moved"), news, evals
    contracts/platform.md     software-architect   REST, WebSocket, crawler→DB contracts
    contracts/analytics.md    ai-architect         the analytics service interface
    adr/ADR-S-###-*.md        software-architect
    adr/ADR-A-###-*.md        ai-architect
  sprints/sprint-NN/
    1-sprint-plan.md          pm
    2-tech-plan.md            software-architect   FE/BE task blocks (#### <TASK> — title)
    2-tech-plan.ai.md         ai-architect         AI task blocks (same format)
    dag.json                  software-architect   the task graph the workflow runs (merges the AI tasks in)
    stories.tsv, milestones.tsv  pm                for progress.py
    3-build.<TASK>.md         developer
    3-consult.<TASK>.md       developer or lead (question)  → 3-consult.<TASK>.answer.<sa|ai|pm|po>.md (owner)
    3-pr.<TASK>.md            tech lead
    4-test.be.md / 4-test.fe.md   testers
    5-review.tech.md / 5-review.ai.md / 5-review.product.md
    6-retro.md                pm
    activity.log              everyone, one line each, via log.sh
```

## Task block format (architects)

```
#### <TASK> — <title>
- Story: F-### ; Side: fe|be|ai ; Effort: high|medium ; Size: ~<N> lines ; Lead: sonnet|opus
- Files: <exact paths; the exclusive file set>
- Change: <what, in 3–8 bullets>
- Contract: <section refs, e.g. contracts/platform.md §3.2>
- Acceptance: <checks a test must prove; for money math give a worked numeric example>
- Out of scope: <...>
```

Set `Effort: high` only for design-heavy, money/return math, data correctness, auth or concurrency
tasks; everything else `medium`. Set `Lead: opus` only for contracts, money/return calculations,
auth, ops. Keep tasks ≤ ~250 changed lines; split otherwise. Every block must be readable alone through
`task.sh <TASK>` — cite sections, do not rely on surrounding text.

## dag.json (software architect)

Schema: `.finvest/templates/dag.example.json`. One entry per task: `id, side, lane, milestone, after[],
base?, effort, leadModel, bothLeads, priority, manual, size`. Bump `dagRev` on every change. Tasks whose
file sets overlap must be ordered with `after`.

## Consult mode

When dispatched with "Mode: consult", answer only the questions addressed to you. Update your own
documents first (archive the old version), then write `3-consult.<TASK>.answer.<you>.md` (≤ 30 lines).
If only the sponsor can decide (scope, money, data source that costs, risk policy), say so explicitly.

## Questions for the sponsor
Label every question `A<n>`, continuing the numbering in `product/brief.md` and `sponsor-answers.md` (next free label;
never reuse one). Give your recommended answer next to each. Answered labels stay in the files as history.
