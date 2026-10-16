# 5-review.product — Sprint 01 product acceptance

Reviewer: `fi-pm`, 2026-10-16. Inputs: 1-sprint-plan.md, backlog criteria F-020/F-030/F-010/F-011/F-017,
5-review.tech.md (FAIL, 3 FIX tasks since merged), 4-test.be.md incl. re-test (107 pass, QA-BUG-1/2/3 fixed),
Scrum Master's live run (M3) and `data/raw/ticks/2026-10-16/_manifest.json` read by me.

**Verdict: sprint goal met. 5/5 stories DONE, 20/20 points accepted.** One labelling defect (below) is a follow-up,
not a rejection: it over-reports gaps, it never hides one. DoD condition: 5-review.tech.md still reads FAIL
(written before the fixes); acceptance of F-011/F-017/F-030 stands once the architect confirms PASS on the fixed
head (re-test is green, 107/107).

## Live evidence (M3, 2026-10-16)
`make crawl DATE=2026-10-16` at 15:35, exit 0, 777 s (13 min, N5 ≤ 45 min now measured), KBS, 1540 requests,
universe 1540 (vci:symbols/getAll, pinned), 911 fetched, 629 skipped all `no_ticks`, 145,184 rows,
checksum `sha256:3bb625c1…`, status `partial`, reason null. DB 225,520 ticks (10-15 partial + 10-16). API health ok.
`git status` shows nothing under `data/`.

## Is "every symbol fetched or had no trades" really `partial`?
No. After the close, an empty KBS tape for today means the name did not trade (illiquid UPCoM/HNX names, halts).
Nothing was missed: the session is fully captured. `partial` should mean "some data we could have had is not
stored". Today's rule (`feeds/ticks.py`: any entry in `symbols_skipped` → `partial`; platform.md §4 lists
`no_ticks` as a *skip reason*) makes every real session `partial`, so:
- F-021's completeness % (S02) would read ~0 % forever, and a genuine partial (http_429, timeout) would look the
  same as a normal day → the G1 signal "never a silent gap" becomes noise. That is the product risk.
- It is not a G1 breach: the manifest names all 629 symbols with a reason; it errs towards alarm, not silence.

Does it fail a criterion? **No.** F-017 asks the manifest to list fetched symbols, rows, checksum and skipped
symbols with reason — all present and correct. No criterion defines when a session is `complete`. The gap is in the
**contract (architecture stage, platform.md §4 status rule)**, carried into the build exactly as specified. It is
recorded as follow-up **S02-1**, to be closed before F-021 ships.

Caveat noted for S02-1: "no trades" vs "source returned empty by mistake" cannot be told apart from the tape alone;
cross-check against daily volume (F-012) when it lands.

## Per story

| Story | Pts | Verdict | Criteria evidence | Note |
|---|---|---|---|---|
| F-020 Data folder, git-ignored | 1 | **DONE** | Data written under `finance_invest/data/`; `git status` clean after two live crawls; retention default keep-all (qa test). | Root-owned files: see S02-2 (ops, not a criterion). |
| F-030 Compose, one-command start and crawl | 3 | **DONE** | Only API published on 127.0.0.1:8000, db/crawler no ports (qa test); `make up`; `make crawl DATE=2026-10-16` crawled the date live. | |
| F-010 Adapter, fixtures, units | 5 | **DONE** | Thousand-VND → VND via SSI fixture; suite passes with sockets blocked; adapter swap with no core change (test_registry). | |
| F-011 Rate limit, cache, backoff, stop | 3 | **DONE** | Budget test; 3×429/403/challenge → backoff → `source blocked`, exit 2; personal-tool UA; live 1540 requests in 777 s, 0 blocks. | |
| F-017 Tick crawl with manifest | 8 | **DONE** | (1) 911 symbols time/price/volume, `side` NULL as allowed (plan note 4), raw archived, compression policy (db test). (2) Manifest has fetched, rows, checksum, every skip with reason (live + oracle test). (3) Idempotent re-run: fixture tests incl. shuffled/duplicate payloads; universe pinned (QA-BUG-3 fix). (4) Past date → `missed`/`partial` + `source_no_longer_serves`, never absent (QA-BUG-2 fix, fixture). | `partial` label: S02-1 (architecture). Criterion 4 and live re-run idempotence accepted on fixtures; live check S02-3. |

Stage notes from this sprint (for the retro, already fixed): the empty/foreign-tape archive bug and universe drift
were **plan**-stage (tech review F1/F3/F4); `--only` validation was **build**-stage. Lost 10-15 ticks for ~1,186
symbols are the accepted C1 risk (crawl started late), not a story failure.

## Follow-ups for sprint 02

| Id | Follow-up | Owner / stage | Priority |
|---|---|---|---|
| S02-1 | Status rule: a symbol with an empty tape after close is "no trades", counted apart from skips (e.g. `symbols_no_trades`), and a session where every symbol is fetched or no-trade is `complete`. Amend platform.md §4, then feed + tests. Must land before F-021. | architect → BE | high |
| S02-2 | Containers write `data/` as root; sponsor cannot clean or delete without sudo. Run crawler/api as the host UID (compose `user:`) and `chown` existing files once. Needed for the manual 10-15 stale-tape cleanup too. | BE (compose) / F-019 | high |
| S02-3 | Live acceptance checks not yet run on the fixed build: re-run `make crawl DATE=2026-10-16` → same rows + checksum; `make crawl DATE=2026-10-14` → `missed`/`source_no_longer_serves`. | tester | medium |
| S02-4 | Clean the 1,186 stale empty tapes under `data/raw/ticks/2026-10-15/` (by hand, after S02-2), then re-run 10-15 so its manifest reflects the fixed rules. | sponsor / tester | medium |
| S02-5 | Scheduler F-019 so crawls stop depending on someone at 15:30 (every missed evening is lost for good). | plan | high (already S02) |
