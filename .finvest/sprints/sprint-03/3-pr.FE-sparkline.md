
## Round 1 (fe lead) - APPROVE, head 2a54231f1e5f1cc717c15082d0244c97865995ab
Files reviewed: Sparkline.tsx, Sparkline.test.tsx, i18n en/vi (curve.aria). Synced with origin/sprint-03 (clean merge, no conflicts).
Size: 121 lines vs ~150 (ok). Contract: invested step with one V per contribution; aria-label vi-VN max/min; empty -> null; focusable, arrows/Home/End; dashed vs solid (not colour-only).
Hand check: y(10,000,000)=44-14025*40/814025=43.31, matches the snapshot "4,43.31 150,44 296,4".
Checks: tsc exit 0; vitest 7 files / 30 tests pass.
Nits: invested not in tooltip; CSS vars fall back to currentColor until the theme exists.
Merged into sprint-03: 5f90edc3a41b90557a10e2035d71a80b13064c0b
