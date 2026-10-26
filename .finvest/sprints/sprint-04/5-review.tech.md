# 5-review.tech — sprint-04 (fi-software-architect, 2026-10-25)

Reviewed: `origin/sprint-04` **e591bde** (tip after merge 7894e44 BE-fix-index-value) against `dag.json` rev 2 (18 tasks, 2 manual),
`2-tech-plan.md` v1.0 + Rework R1, `2-tech-plan.ai.md` v1 (AI-rw-curve, AI-rw-bench-na acceptance), the 16 `3-pr.*.md`,
`4-test.be.md` (B1/B2 + SM re-run of `make smoke` on the live db after rework: check (1) VNINDEX ratio 0 rows, check (2) weekend
rows 0), `4-test.fe.md` re-run (§9.2 PASS 18/18, per SM; the file on disk at review time is still the round-1 red copy, 12/6),
`contracts/platform.md`, `contracts/analytics.md` v1.2, `architecture/data.md` §1.2, `product/ux/visual-design.md`.

**Verdict: PASS — merge `origin/sprint-04` into `main`.** No blocker. Every automated task has an APPROVE round and a merge sha;
every rework task closed its bug with a test that fails on the old code; both testers' final runs are green. One observation (OBS-7)
is carried, not fixed (§3).

## 1. Per task (dag rev 2)
| Task | Merge | Verdict | Note |
|---|---|---|---|
| FE-tokens, FE-base, FE-guards (F-129, F-132) | 7ed8cb8, dd69694, e56b845 | PASS | tokens compared by value to visual-design §3.1–3.5 light+dark; guards prove on a removed token; vite `test.css:true` outside-set edit justified. |
| FE-shell (F-130) | 4f63258 | PASS after R1 | round-1 BUG-1/3/6 (spacing, landmarks, doubled ✕) closed by FE-fix-shell 696ee6d; axe all rules 0 in the re-run. |
| FE-sc-cards, FE-sc-table, FE-sc-panel (F-131) | c247190, 0b0ad4d, 82824eb | PASS after R1 | BUG-2 (P/L ₫ sign from `cell.num`, worked example +1.290.559 ₫ / +2,58 % hand-checked by lead) and BUG-4 (header wrap, 1280 fit) closed by FE-fix-table 5dd0944; BUG-5 (§6.6 typography) by FE-fix-panel 931ce32. |
| FE-shots → FE-shots-rw (F-132, manual) | — | PASS | round 1: 12/6 (6 bugs, all build stage, all fixed); re-run 18/18, screens/real-stack 0 FAIL. Playwright kept out of package.json as planned. |
| BE-rw-ledger-rank (S04-RW T5b) | e5ac19f | PASS | rank case() on both sides, `rows >= AND rank >=`; test proves the 10-23 scenario (complete 4,949 not lowered by blocked 10,357). Closes sprint-03 §3 T5b. |
| OPS-rw-smoke-dsn (T5c, T6, smoke) | 84dedfa | PASS | round 1 CHANGES (F-030 guard stale) → round 2 APPROVE, guard now asserts every published port is 127.0.0.1 (F-030 intent kept). T5c orphan 10-24 row gone (weekend rows 0). Closes T5c/T6. |
| OPS-fix-testdb-doc (B2) | 860af49 | PASS | `make test-db` refuses a name not ending in `_test`, `-rs` prints skips; silent false green gone. |
| BE-fix-index-value (B1) | 7894e44 | PASS | adapter band `INDEX_VALUE_PER_UNIT=(100, 1e7)` + `repair_index_1d_value` + migration 0009; true division confirmed, idempotent, v=0 safe; 8 live rows nulled; `make smoke` (1) now 0 rows. Accepted deviation: adapter also drops `vol == 0` (agrees with the repair, so a re-crawl cannot undo it). |
| AI-rw-curve (AI-1 + AI-3) | 80c8247 | PASS | `i = -1` literal gone (`git grep` on the tip: empty), assert on first calendar day, `holding_days` display-only comment; curve[0] = buy day 9.985.975 and DCA `invested == contributions[0]` tests hand-checked; goldens 001–010 unchanged; analytics 42 passed. Matches 2-tech-plan.ai.md acceptance. |
| AI-rw-bench-na (AI-2, F-048) | ee8cc98 | PASS | three-way branch in `ScenarioCard` (`null` → nodate, `first_available > buy` → dated, else `card.bench_na_gap`), vi/en strings verbatim from the plan; dated test moved past `dates.buy`; no contract change (decision upheld). |

## 2. Per contract
| Contract | Verdict | Note |
|---|---|---|
| contracts/analytics.md v1.2 §2.4 | PASS | `equity_curve` now starts at buy day as §2.4 states; `benchmarks[].first_available` unchanged, wording logic lives in the card. |
| contracts/platform.md | PASS | no payload change this sprint; index `value` was already nullable, so B1 nulling is inside the contract. |
| architecture/data.md §1.2 | PASS | index `value` VND-or-null honored; o/h/l/c/v of repaired rows never edited; benchmark reads `c` only, so no analytics rule change. |
| product/ux/visual-design.md §3.2, §6.4, §6.6, §9.2 | PASS | P/L sign+colour identical cards/table; drawer typography scoped in panel.css; 18/18 checklist in the re-run. |
| ops/README.md + Makefile (test DSN) | PASS | F-030 loopback-only intent preserved (db 127.0.0.1:55432, api 127.0.0.1:8001, guard runs, not skipped). |

## 3. Open items — carry
| Id | Finding | Stage | Blocks merge? | Disposition |
|---|---|---|---|---|
| OBS-7 | at 768 px the top bar wraps to two lines (menu, crawl, VI/EN). visual-design §9.2 line 9 only pins 375 and 1280; the 768–1023 band was "CSS media query only read", never shot in either run. Cosmetic, no function lost. | build (FE-shell) + test gap (no 768 shot) | No | **Carry → sprint-05 as a small FE task**: one `@media (min-width: 768px)` rule in `shell.css` plus a 768 shot added to screens.mjs (≈ 15 lines). Not a sprint-04 rework: it is outside the sprint's acceptance widths. |
| nit | `make test-db` recipe echoes the DSN with the password (no `@`); `PGPASS` breaks on URL-reserved chars | ops | No | fold into the next ops task that touches the Makefile. |
| nit | DCA card lists 5 "Ngày bán dời sang" lines (noisy) | ux | No | pm decides whether to dedupe to one line (backlog note). |

## 4. Architecture notes
- Decision B1 "repair in code, no re-fetch" held: the same band is now enforced at ingest, by the one-off migration and by the smoke
  check, so the three cannot disagree. Keep `INDEX_VALUE_PER_UNIT` as the single source if the band ever moves (smoke.sql repeats the
  numbers — acceptable for a read-only check, note for a later ops task).
- Plain CSS tokens/sheets (no UI library) delivered F-129..F-132 at +~800 lines total with zero dependencies added; keep for sprint-05.
- Rework sizes stayed inside estimates (all ≤ 1.5x), no outside-set edit without a lead note.

Log: `2026-10-25 | software-architect | sprint-04 | review | PASS, 18 tasks, OBS-7 carried to sprint-05 | 5-review.tech.md`
