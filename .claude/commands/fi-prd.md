---
description: Product requirements — fi-po drafts, revises or finalises the PRD
argument-hint: draft | <sponsor answers> | approve
---
Ceremony: PRD. Argument: $ARGUMENTS

1. If the argument is sponsor answers, append them **verbatim** with a timestamp to `/home/stein/Desktop/Learning/finance_invest/.finvest/product/sponsor-answers.md` first.
2. Dispatch `fi-po` (model fable) with a 3–5 line brief: mode (draft / revise / approve), FI_DIR=/home/stein/Desktop/Learning/finance_invest/.finvest,
   "Follow briefs/common.md and briefs/owner.md". On `approve`, the PO marks the PRD status Approved with the date.
3. Relay the hand-back (≤ 5 lines) and the PRD's `## Open questions for the sponsor` (read only that section with rg + sed).
4. **Gate:** stop. The sponsor answers with `/fi-prd <answers>` or `/fi-prd approve`.
