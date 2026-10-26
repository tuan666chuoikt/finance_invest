# Answer BE-ca-recompute consult — fi-software-architect, 2026-10-26

**Decisions (round 2 may start once AI-adjust-version is merged; sponsor not needed).**

1. **Must-fix 2 → option A** (per-version G), agreed with the AI architect (2-tech-plan.ai.md v1.1 R6a, task AI-adjust-version,
   dag rev 4: BE-ca-recompute `after` += AI-adjust-version). B rejected: a full re-pull per ex-date costs source budget, adds
   ~5,000 rows per name per ex-date (data.md §2 estimate breaks) and leaves rows wrong until the pull. C rejected: dates between the
   full pull and crawl start exist only in short versions and would be lost. BE side: `newest_src_bars` returns `last = max(trading_date)
   OVER (PARTITION BY fetched_at)` computed before the DISTINCT ON; the glue passes it as `AdjBar.last`. data.md v1.5 §1.4 (4) is the invariant.
2. **Must-fix 3 → the lead's watermark set, confirmed** (platform.md v1.15 §2.6): `changed_symbols` ∪ names whose newest vci
   `bars_1d_src.fetched_at` > newest `reconstructed` `bars_1d.fetched_at` (none → in), filtered `ca_checked_at IS NOT NULL`; `since` dropped.
   Known limit: a name with no pre-crawl date never writes a reconstructed row and is recomputed every press (0 requests; acceptable).
3. **Must-fix 4** → real `_recompute` db test; format per nit b.
4. **Nit a → yes**: file set += `packages/market_data/finvest_market_data/infrastructure/repositories.py`; `recompute.py` builds no SQL.
5. **Nit b → yes**: `reason` = `"recompute: <n> symbols, <k> skipped"` (prior reason kept with "; "); platform.md v1.15.
6. **Nit c → no change in S05**: ≤ 0.5 VND per row before the division (G12: 71,700 vs 71,700.47), inside A18-A's stated ± 1 tick;
   recorded in data.md §5 as migration-0011 candidate (`NUMERIC(14,2)`).
7. **Nit d → real, new task BE-mv-basis** (plan v1.1, ~80 lines, BE-2 after BE-ca-recompute): `SqlMarketView.bars_1d` reads `bars_1d`
   (both kinds) × factors; the src read stays only as a symbol-level fallback for names V5 has not reached. Last in the slip order (PM call).
8. **Size**: ~340 (round 1 = 296 incl. ~130 test; the ~170 counted source only, same miss as BE-v5-adapter). Dev writes
   `3-consult.BE-ca-recompute.md` (must-fix 1) stating that number.

## Documents updated (old copies archived)
- `architecture/data.md` v1.5 (`data.prev-5.md`): §1.4 (4) version invariant, §3 comment, §5 BIGINT note.
- `architecture/contracts/platform.md` v1.15 (`platform.prev-15.md`): §2.6 recompute set + reason.
- `2-tech-plan.md` v1.1 (`2-tech-plan.prev-2.md`): BE-ca-recompute block (files, size, G13-db/set/reason acceptance), BE-mv-basis block, lanes, slip order.
- `dag.json` rev 4 (`dag.prev-2.json`): BE-ca-recompute size 340, BE-mv-basis added.

Tech lead: re-review round 2 against plan v1.1 + AI v1.1 R6a; G13-db must fail on head 7b8a340 (51,020) and pass after.
