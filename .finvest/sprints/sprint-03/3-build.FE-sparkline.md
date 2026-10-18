# 3-build FE-sparkline (F-056)
Result: DONE. Branch task/sprint-03/FE-sparkline.
Files: apps/web/src/features/scenarios/Sparkline.tsx (+test), i18n en.json/vi.json (`curve.aria`).
Changes: inline SVG, viewBox 0 0 width(300) x height(48), preserveAspectRatio none, width 100%; solid market-value polyline, dashed invested path (one `V` per contribution step); focusable svg, ArrowLeft/Right/Home/End and mouse pick point; `<div role="status">` shows `dd/mm/yyyy · 10.610.975 ₫`; aria-label vi/en with max/min; empty points render null.
Checks: tsc 0 errors; vitest 7 files / 30 tests pass (5 new, incl. hand-computed points snapshot).
Deviations: no CSS variables exist in the app yet, so colours are `var(--chart-line, currentColor)` / `var(--chart-invested, currentColor)`. Y-scale spans both market value and invested. Flat series draws at mid height. Focus shows the first point. Lint script absent in apps/web.
Outside-set edits: none. Size: 121 lines vs ~150.
Tester notes: tooltip is below the svg (no overlay); invested not in tooltip.
