# Answer S-v2-batch (sa, 2026-10-24 eve) — take **B**, with a control call first; A is the pre-wired fallback

**Decision: B, fresh cap of 6 live calls, by hand, one at a time** (plan block S-v2-batch rev 2 in `2-tech-plan.md`).
No sponsor decision needed: nothing costs money and no bot-check work-around is involved (C stays out of scope; SM 15:18).

Why not A straight away: the 9 `200 []` calls do not yet separate the hypotheses —
- no 1-name `countBack 8` control was made (the working app call was `FPT-1d-6000`), so "`[]` = soft block for this client" is open;
- every multi-name list mixed exchanges (HOSE+HNX) and/or a delisted name, or used `countBack 6000`; a live-only 2-name
  `countBack 8` body was never sent. Hypothesis 3 (mixed list → `[]`) is **not** ruled out by the 8 × 6000 call.
Two calls (rungs 1–2) answer that; the ladder stops at the first `[]` after the control, so the normal cost is 2–3 calls.

Ladder (all ≥ 1 s apart, project UA, `to` = today 23:59:59 VN, stop at the first `[]` after rung 1):
1 `FPT` cb 8 (control; `[]` → retry cb 60; still empty/418 → verdict "blocked, retry on <date>", stop) · 2 `FPT,VNM` ·
3 `FPT,SHB` · 4 `FPT,VNM,VTS` · 5 50 live names → fixture · 6 spare 8 × 6000.
Report every call as a citable line (body incl. `to`, status, bytes, wall time, symbols back/asked, bars/symbol).

If rung 2 is `[]` → verdict **cap = 1** (= option A), recorded in the report; no fixture; data.md §1.2 V2 is already marked
unverified and BE-bars-batch already carries the `BATCH_MAX = 1` branch (batching code degenerates to today's loop, request
figures become ≈ 1 780 ≈ 15 min at 2 req/s). BE-bars-batch is **not** unnecessary in that case: indices-first (T2) and the
418 fix below are still needed, and 15 min is acceptable for a manual press.

Side finding for BE-bars-batch (added to its block): `fetch.py` `_blocked` does not count **418**, so the 15:18-style
answers (418 after a 30 s hold) are retried 3× with back-off as plain `HTTPError` — ≈ 100 s per blocked name and
`SourceBlocked` never trips. That, not the token bucket, is the likelier source of the 6.7 s/name average measured by the
job (`[]` answers take 0.1–0.5 s). One line + one test, now in the task's file set (dag rev 10, size 190).

Documents updated: `2-tech-plan.md` (S-v2-batch rev 2, BE-bars-batch `BATCH_MAX`/418; prev-5), `data.md` §1.2 V2 (prev-2),
`contracts/platform.md` v1.11 §2.6 (prev-11), `dag.json` rev 10 (prev-5). No dag edges changed.
Over-cap note: the 9 calls were all 2-byte answers, no source load; rule kept — no script loops for live probes.
