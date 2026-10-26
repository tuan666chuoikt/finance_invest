# 5-review.tech — sprint-05 (fi-software-architect, 2026-10-26)

Reviewed: `origin/sprint-05` **2df45e4** (tip after merge OPS-fix-guards; 104 commits over main) against `dag.json` rev 7 (27 tasks, 1 manual),
`2-tech-plan.md` v1.4 + Rework R1, `2-tech-plan.ai.md` v1 (+ AI-adjust-version, AI-recon-xsrc, AI-fix-lint), the 26 `3-pr.*.md`,
`4-test.be.md` round 2 (PASS; migration rehearsal on a fresh live dump), `4-test.fe.md` round 2 (PASS), `architecture/data.md` v1.8,
`contracts/platform.md` §2.5/§2.6 v1.12–v1.15, `contracts/analytics.md` §1.4, `knowledge/vn-market.md` VN§3/§6, `ux/visual-design.md` §9.2.

**Verdict: PASS — merge `origin/sprint-05` into `main`.** Merge auto-deploys to live (gw-poll) and runs migration 0010 on the live DB;
the rehearsal (live dump restored, `upgrade head` 1.0 s, ssi 947 rows moved `bars_1d_src` → `bars_1d` observed, vci/index/symbols/ticks
counts identical, downgrade 0.6 s and re-upgrade OK, 0010 frozen DDL) is sufficient evidence. Two findings carried (§3), none blocks.

## 1. Per task (dag rev 7)
| Task | Merge | Verdict | Note |
|---|---|---|---|
| BE-mig-0010 (F-013/F-014) | f5bb4dd | PASS after R1 | round 1 must-fix (DDL built from live `tables.py`) closed: inline frozen `op.create_table` x5 + `add_column`, compared column by column; observed-over-reconstructed guard G9 93,499/93,500 hand-checked by lead; down/up/down/up test. |
| BE-observed-bar (F-013) | f6a6c67 | PASS | S1 board bar → `bars_1d` observed with `ref`; nit (`last_bar_dates`/`daily_coverage` still read `bars_1d_src`) closed by BE-mv-basis for the basis path; coverage read is ops-only, carry as nit. |
| BE-v5-adapter (F-014) | 7c8087b | PASS after R1 + rework | B-05-1 (ISS stock dividends unmapped, ~10 % nominal error on HPG/SHB/ACB/MBB) was a real money bug of this task; closed by BE-fix-v5-iss 85efde3 with a test red on the old mapper. |
| BE-ca-repo, BE-ca-step3 (F-014) | ec4275a, 5d1976a | PASS | `(source, source_event_id)` upsert, diff log, budget B; `ca_symbols_in_order` plain-SQL read of `scenarios` carries its `# shortcut:`; B-05-2 (budget 28, `ca_checked_at NULLS FIRST` inside every tier) closed by BE-fix-ca-budget 2f5c6b7. |
| AI-ca-factors, AI-adjust-series, AI-adjust-version, AI-recon-rules, AI-recon-xsrc (F-015/F-016) | 33e63c1, 695ca05, 97dcde1, (r2 APPROVE), f73248e | PASS | Fractions oracle over all 1,346 stored factors: 1,303 exact to 12 dp, 43 within 7.4e-5 rel (1 VND inversion rounding); reconstructed × G vs V2 292,577 rows, 0 > 1 VND. R6a per-version `last` and `self_check` landed before the BE consumers (dag rev 3/5 ordering held). |
| BE-ca-recompute (F-015) | 0d69b8b | PASS after R1 | v1.1 layering kept (no SQL in `recompute.py`); anomalies via `insert_anomaly_once` (idempotent); `recompute --symbols HPG` x2 → identical bars md5; replay 0 requests / 0 changes. |
| BE-market-view-ca, BE-mv-basis (F-023/F-015) | 9cf1d44, 23a7f8d | PASS | `/health.rules_version` 2026.10.28; basis reads `bars_1d` (observed + reconstructed), so mixed `bars_1d_src` versions can no longer leak into the simulator (consult nit d closed). Pre-existing `whatif.py:143` contract deviation noted by lead → §3. |
| BE-recon-cli, BE-recon-s2 (F-016) | r2 APPROVE, r2 APPROVE | PASS after rework | `tick_size` moved into `finvest_rules` (consult, +1 file); B-05-6 (exit 1 on mismatches, S2 rows as `ssi_s2`) closed by BE-fix-recon-s2 4d47710. Live S2 cross-check not re-run after B-05-1 (30 calls) — acceptable, S2 path is unit-tested and the first live press will run it. |
| BE-fix-runner-now (B-05-5) | merged | PASS (unit) | 14:50/15:06 target rule unit-tested; real-press check is L-milestone work for the SM. |
| OPS-guards, OPS-fix-guards (F-033, B-05-3/7) | a87190a, 2df45e4 | PASS | audit now scans `.js/.jsx/.mjs/.cjs` (tester's strict-xfail probe XPASSes); test db port 15433; loopback-only intent (PR-130) kept. |
| AI-fix-lint (B-05-4) | 3b8fefc | PASS | `ruff check apps services packages` clean on the tip. |
| FE-e2e-carry, FE-crawl-step3, FE-rw, FE-fix-dca-shifts (S05-RW, F-014 UI, F-05-1) | 92b86c8, c51edc4, 36c1114, 70a16d5 | PASS | OBS-7 closed (top bar 1 line h=53 at 768/800); DCA one shift line + `<details>` from the real API shape (5 shifts HPG); vitest 94, tsc 0, screens 138/0, widths 88/0, real-stack 40/0. |
| FE-shots (manual) | — | PASS | round 2 §9 checklist all PASS at 375/768/800/1280 light+dark, shots in `shots/FE-test/`. |

## 2. Per contract
| Contract | Verdict | Note |
|---|---|---|
| data.md v1.8 §3 (five tables, `symbols.ca_checked_at`), §1.4 (1)(4) | PASS | migration 0010 matches column by column; per-version G invariant proven by the oracle; `bars_1d_src.source` now `vci \| ssi \| ssi_s2`. |
| data.md §1.2 V5 (B = 28, block after ~30) | PASS | budget 28 enforced; tester's Note A reproduced the block on a test IP only (no live impact). |
| platform.md §2.6 v1.12–v1.15 (step 2 units, step 3 summary, `symbols_deferred`, `/health.rules_version`), §2.5 `data_snapshot` | PASS | FE crawl status renders the v1.14 summary shape; reproducibility test on snapshot. |
| contracts/analytics.md §1.4 `data_snapshot`, `shifts` | PASS | FE-fix-dca-shifts reads `contribution` shifts as documented; whatif.py deviation pre-existing (§3). |
| vn-market.md VN§3/§6 | PASS | ISS title mapping (v1.2 bullet) cited in `_map`; tick sizes in `finvest_rules`. |
| visual-design.md §9.2 (S05 lines) | PASS | 768/800 one-line bar and DCA ≤ 1 shift line asserted in `fe05-widths.mjs`. |

## 3. Open items — carry
| Id | Finding | Stage | Blocks merge? | Disposition |
|---|---|---|---|---|
| B-05-8 | recon 26/30: VNM, VPB, VPL, VRE have 1 `vci` row each in `bars_1d_src` and no reconstructed history, so F-016 "30/30" is not met on the live copy. Root cause is **missing V2 daily backfill (data), not code**: `crawl bars --only` exists (`cli.py:43`) and the pipeline is proven on the other 26. | data/ops | **No** | **Carry, not block.** SM runs `crawl bars --only VNM,VPB,VPL,VRE` on live after deploy, then `crawl recon`; record the 30/30 line in `activity.log`. If any of the 4 still has < 200 vci rows after the backfill (V2 cap, 418 hold) → open a sprint-06 data task. Milestone M2 "VN30 recon 30/30" closes on that log line, not on this review. |
| B-05-9 | `corporate_action_unmapped` anomalies appended on every run (364 → 411 …): `feeds/corporate_actions.py:85` calls `insert_anomaly`, while `recompute.py:69` already uses `insert_anomaly_once`. Not harmful (table only grows, no money path). | build (BE-ca-step3) | No | **Carry → sprint-06** as a ~5-line BE task: use `insert_anomaly_once` at `corporate_actions.py:85` (guard `ex_date is None` → keep plain insert or key on `(symbol, rule, value)`), one db test "second run adds 0 rows". Count distinct `(symbol, value)` in any ops/UI sentinel until then. |
| tests_be05 | tester's oracle `tests_be05/` (60 ruff style errors) is **not in the tree** (`git ls-tree origin/sprint-05`: 0 files), so `make test-kernel` on main is clean. | test | No | If the lead merges them later: put them under `services/crawler/tests/oracle/` and fix the 60 errors (they are E/F/I, mechanical), or add the path to `[tool.ruff] extend-exclude`. Do **not** merge them unlinted into the tree. |
| nit | `whatif.py:143` contract deviation (pre-existing, owner ai) noted in 3-pr.BE-market-view-ca.md | ai | No | ai-architect decides in sprint-06 planning. |
| nit | `repositories.last_bar_dates` / `daily_coverage` still read `bars_1d_src` only (BE-observed-bar nit 2) | build | No | fold into the next ops/coverage task. |
| not exercised | board bar of the run date in a real press (B-05-5 live), ex-date change in V5, S2 live cross-check after B-05-1 | test | No | covered by the L-milestone presses after deploy; SM confirms per milestones.tsv. |

## 4. Architecture notes
- Live deploy path: merge → gw-poll → `alembic upgrade head` (0010). 0010 is frozen DDL + a data move keyed on `DISTINCT ON (symbol, trading_date) ORDER BY fetched_at DESC`; downgrade restores the ssi rows, so a rollback is `downgrade 0009` + redeploy of main, no dump restore needed. Take the usual pre-deploy `pg_dump` anyway (7.8 s).
- Layering held under pressure: `recompute.py` builds no SQL, factor maths stays in `finvest_rules`/`finvest_analytics`, the tick table moved into `finvest_rules` when the lead caught it in BE-recon-cli. Keep the dependency-rule test as the gate.
- Rework sizes stayed ≤ 1.5x; two consults (BE-ca-recompute, BE-recon-s2) changed the plan (per-version G, `self_check` without slack) before code was written — that is the process working, not slippage.
- Idempotency is now the norm (`insert_anomaly_once`, upsert keys, replay 0 requests); B-05-9 is the last plain-append path in the press, close it in sprint-06.

Log: `2026-10-26 | software-architect | sprint-05 | review | PASS, 27 tasks; B-05-8 carried (live backfill by SM), B-05-9 carried to sprint-06 | 5-review.tech.md`
