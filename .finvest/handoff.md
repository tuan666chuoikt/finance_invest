# Finvest hand-off: read this first in a fresh session

Owner: the Scrum Master. Updated **2026-10-14**. Keep under ~6 KB: current state only. History lives in
git, `product/sponsor-answers.md` and the activity logs.

## 0. Start here
1. `CLAUDE.md` holds the rules. Run `.finvest/bin/progress.py` once a sprint exists.
2. Read the last ~5 entries of `product/sponsor-answers.md`.

## 1. Status
- **Sprint 0 (inception).** Team, briefs, scripts and docs are set up (2026-10-14). No PRD, no code yet.
- Next step: `/fi-prd draft` (A1–A4 already answered) → sponsor answers new A# questions → `/fi-prd approve`
  → `/fi-backlog init` → `/fi-architect` → `/fi-sprint-plan` → `/fi-build`.

## 2. Running now
- Nothing.

## 3. Open decisions for the sponsor
- A1–A4 answered 2026-10-14 (all exchanges; no broker account yet; no margin; no local LLM yet). Next free label: **A5**.

## 4. Environment notes
- Linux machine; scripts use `flock` and `md5sum`. `gh` is not installed: merges go by `git push` under
  the merge lock (`sm.sh merge`); PRs are optional (install `gh` + `gh auth login` to enable them).
- Workflows need Claude Code ≥ 2.1.248 for `cacheTtl: "1h"` in agent definitions.

## 5. Cost
- No runs yet.
