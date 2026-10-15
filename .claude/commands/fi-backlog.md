---
description: Backlog refinement — fi-pm turns the approved PRD into stories, UX specs and a roadmap
argument-hint: init | <new idea or change>
---
Ceremony: backlog. Argument: $ARGUMENTS

1. Check `/home/stein/Desktop/Learning/finance_invest/.finvest/product/prd.md` is Approved; if not, stop and say so.
2. Dispatch `fi-pm` (opus): mode init or refine, FI_DIR=/home/stein/Desktop/Learning/finance_invest/.finvest, "Follow briefs/common.md and briefs/owner.md".
   A new idea that changes scope goes to `fi-po` first (PRD revision), not straight into the backlog.
3. Relay: story count, points, the first two sprints in the roadmap, open questions.
4. **Gate:** the sponsor reviews `product/backlog.md` and `product/roadmap.md`.
