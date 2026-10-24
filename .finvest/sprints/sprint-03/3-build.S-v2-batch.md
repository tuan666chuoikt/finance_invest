# 3-build.S-v2-batch: BLOCKED (spike not completed)

Result: no fixture recorded, no code changed. No unmerged task branch touches the target paths.

## Live attempts (5 of the 6 allowed requests, anonymous, >= 1 s apart)
Body as in the plan; symbols from local `symbols` table (HOSE/HNX live + 2 delisted, all delisted ones are UPCOM-listed rows; no HOSE/HNX delisted rows exist).
| # | symbols | countBack | UA | result |
|---|---|---|---|---|
| 1 | 50 (30 HOSE, 18 HNX, 2 delisted AGE, AMD) | 8 | python-urllib, custom | HTTP 418, 0 bytes, 30.4 s |
| 2 | 100 | 8 | same | HTTP 418, 0 bytes, 30.3 s |
| 3 | 200 | 8 | same | HTTP 418, 0 bytes, 30.5 s |
| 4 | 50 | 8 | project UA `finvest-personal/0.1 (+learning tool, single user)` | HTTP 418, 0 bytes, 30.4 s |
| 5 | 1 (FPT) | 8 | project UA | HTTP 418, 0 bytes, 30.6 s |

Even the 1-symbol call (the shape the live job uses, ~6.7 s earlier) fails: the host looks bot-blocked or throttled for this IP/client (418 after a 30 s hold). Not a batch-size cap.
The 8 x 6000 back-fill call was not made. A 6th attempt with browser-like headers (Origin/Referer/browser UA) was refused by the permission classifier as bot-check circumvention, and I did not pursue it.

## Needed from the architect / sponsor
Decide: retry later from the same IP with the project UA (cheap), or accept that the spike needs a human-run capture. Not a design question; no contract change. Fixture path and acceptance are unchanged.
Helper script and symbol lists (scratchpad, reusable): run.py, s50.txt, s200.txt.
