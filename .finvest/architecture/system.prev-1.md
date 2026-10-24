# Finvest — System architecture

Owner: `fi-software-architect`. Status: **v1, 2026-10-15** (inception, for R1 with R2–R5 in view). Inputs:
`product/prd.md` (Approved v2), `product/backlog.md`, `product/ux/*`, `knowledge/vn-market.md`,
`docs/03-kien-truc-de-xuat.md` (proposal), `architecture/data.md` §1 (source findings). Decisions are ADRs in
`architecture/adr/`. One machine, one user, zero budget, money correctness first.

## 1. Non-functional requirements

| # | NFR | Target | From |
|---|---|---|---|
| N1 | Runs on the sponsor's Ubuntu machine with `docker compose up`; API and web bound to `127.0.0.1` only | one command start, one command crawl | PR-131 |
| N2 | What-if, 10 y daily | < 2 s | G4 |
| N3 | Compare 5 strategies × 10 symbols × 5 y | < 30 s | G4 |
| N4 | Watchlist board refresh in session | ≤ 5 s median, stale badge > 15 s | G6 |
| N5 | Full tick pass per session | finishes before 20:00 retry window; `[assumed]` ≤ 45 min at 1–2 req/s | PR-013 |
| N6 | Re-running any crawl or computation is idempotent and reproducible (same snapshot + rules → identical bytes) | 100 % | PR-133, F-017 |
| N7 | Storage growth `[assumed]` | ≤ 15 GB/year total (data.md §2 estimates 8–13) | PR-132 |
| N8 | Zero secrets required; no broker SDK; no outbound call except the data sources | audited by test | PR-130 |
| N9 | `[assumed]` RAM for the stack ≤ 4 GB (Postgres 1 GB shared_buffers, API, Vite/nginx) | — | — |
| N10 | Offline test kernel (fixtures only) runs in < 2 min; full suite < 10 min | — | PR-016 |

## 2. Stack (ADR-S-003, ADR-S-004)

| Layer | Choice | Why (short) |
|---|---|---|
| Database | PostgreSQL 16 + TimescaleDB 2.x (Apache + Timescale Community licence, free self-hosted) in Docker | one SQL store for ticks (compressed hypertables) and everything else; ADR-S-001 |
| Backend | Python 3.12, FastAPI + Pydantic v2, SQLAlchemy Core + psycopg 3, Alembic, `uv` for deps | data ecosystem, OpenAPI for free, typed contracts |
| Crawler | same Python package (`services/crawler`), CLI `finvest-crawl`, `httpx` + on-disk raw archive, own adapters (ADR-S-002) | vnstock not usable (data.md §1.1) |
| Scheduler | **systemd user timers** on the host calling `docker compose run --rm crawler …` (ADR-S-009) | PR-020 asks for a timer; survives reboots with `Persistent=true`; no in-process scheduler to babysit |
| Analytics | Python package `services/analytics` imported by the API (no separate service in v1) | AI architect owns; same engine for what-if and backtest (PR-071) |
| Frontend | React 18 + Vite + TypeScript, TanStack Query, TanStack Table (virtualised), `lightweight-charts`, i18next with EN/VI JSON | ADR-S-004 |
| Realtime (R3) | **HTTP polling** of `GET /api/board/watchlist` every 3 s (ADR-S-004 §realtime); SSE only if polling misses N4 | least code that meets G6 |
| Tests | pytest + Hypothesis (money), import-linter (layering), Vitest, Playwright + axe | codebase.md §5 |
| Lint/format | ruff + mypy (strict in `domain/`), eslint + prettier | — |

## 3. Components

```
host (Ubuntu)                                   docker compose (network: localhost only)
┌──────────────────────────────┐      ┌───────────────────────────────────────────────────────────┐
│ systemd user timers          │      │  web   (vite dev / nginx static)  127.0.0.1:5173|8080      │
│  finvest-crawl@close  15:30  │      │        │ REST /api/*  (JSON, OpenAPI)                       │
│  finvest-crawl@retry  20:00  │──────┼─►api   (FastAPI)  127.0.0.1:8000                           │
│  finvest-catchup  OnBoot     │ run  │        │ imports services/analytics (R2+)                  │
└──────────────────────────────┘      │        ▼ SQL                                               │
                                      │  db    (postgres16 + timescaledb)  volume data/pg/          │
                                      │        ▲ upsert (natural keys)                              │
                                      │  crawler (one-shot CLI containers; `poll` long-runner R3)   │
                                      │        │ httpx → KBS · VCI · SSI  (adapters, rate limited)  │
                                      │        └─► raw archive  data/raw/<feed>/<date>/*.json.gz    │
                                      └───────────────────────────────────────────────────────────┘
```

| Component | Responsibility | Owner side |
|---|---|---|
| `apps/web` | board-ui: shell, EN/VI, data-quality, rules page, (R2+) what-if, charts, scenarios, why-it-moved | FE |
| `apps/api` | REST (contracts/platform.md), reads DB, runs analytics in-process, enqueues `jobs` (manual re-run) | BE |
| `services/crawler` | feeds (data.md §4), `MarketDataSource` adapters, raw archive, manifests, gap detection, anomalies, reconciliation, catch-up | BE |
| `services/analytics` | portfolio-sim, backtest, decomposition (`architecture/analytics.md`, AI architect) | AI |
| `packages/market_rules` | VN rules with `effective_from` + verification flags, generated from `knowledge/vn-market.md`; trading calendar + session phase | BE (AI architect approves values) |
| `packages/contracts` | OpenAPI JSON exported from the API → TS types for the web | BE |
| `db` | schema in data.md §3; Alembic migrations in `apps/api/migrations/` | BE |

Data flow, after close (R1): timer → `crawler close_snapshot` (SSI, 3 calls → nominal daily + flows) →
`crawler ticks` (KBS per symbol → raw gz → normalise → upsert → manifest) → `bars_1d_src` (VCI, adjusted) →
`corporate_actions` (VCI IQ) → `adj_factors` recompute → `recon` + anomalies → data-quality page reads tables.

## 4. Key design rules

1. **Ports and adapters.** Domain code imports nothing from adapters; `MarketDataSource` (codebase.md §3) is the
   only way data enters. Each adapter has recorded fixtures under `tests/fixtures/<source>/`; the kernel runs
   offline (PR-016).
2. **Nominal is truth, adjusted is derived.** Observed nominal bars + corporate actions → our adjusted series;
   source-adjusted series are versioned snapshots used only for reconciliation (data.md §1.4).
3. **Money is integer VND, time is UTC in storage and Asia/Ho_Chi_Minh in every API payload and screen**
   (ADR-S-005, ADR-S-006). Percentages are computed with `Decimal`, rendered by the web as vi-VN.
4. **Idempotent by natural key; manifests make absence visible.** A session that was not fetched has a
   `crawl_sessions` row with a reason; the gap list is a table scan, never an inference (G1).
5. **Degrade, don't lie.** Source blocked → `source_health.blocked_since`, feed status ⏸, crawl stops (PR-135);
   board rows carry `as_of`; the web shows stale/closed/holiday states from the API's `session` object.
6. **No orders, no credentials, no paid calls.** No broker SDK in the lock files (audit test F-032); the API has no
   write endpoint except `POST /api/jobs` (re-run a crawl) and, from R2, saving scenarios.
7. **Reproducibility.** Every result payload carries `data_snapshot` (max `fetched_at` of its inputs) and
   `rules_version` (git-tracked version of `packages/market_rules`) (F-023).

## 5. Deployment and operations

- `docker compose up -d` starts `db`, `api`, `web`; `docker compose run --rm crawler <feed> --date YYYY-MM-DD`
  runs one feed; `make crawl DATE=…` wraps it (F-030). Profiles: `dev` (Vite with HMR), `prod` (nginx static).
- Ports bind `127.0.0.1` only (compose `ports: "127.0.0.1:8000:8000"`); Postgres is not published to the host at
  all (API/crawler reach it on the compose network). No auth `[assumed, PR-131]`.
- `systemd --user` units installed by `make install-timers` (templates in `ops/systemd/`); `loginctl
  enable-linger $USER` so timers run without a login session. Timers: 15:30 and 20:00 Mon–Fri
  (`OnCalendar`), `finvest-catchup.service` `WantedBy=default.target` with a 3-min delay after boot.
- Backups: none in v1 (PR-136 Could); the data-quality page shows "No backup configured".
- Logs: structured JSON to stdout (compose logs) + `crawl_runs` rows; no external services.
- Upgrades: Alembic migrations run by the API at start-up (`alembic upgrade head`) — single user, so safe.

## 6. Failure modes

| Failure | Behaviour |
|---|---|
| Machine off at 15:30 and 20:00 | boot catch-up runs; KBS serves only the current session → `crawl_sessions(ticks, D) = missed: machine off`; daily nominal for D is **recoverable later** only as reconstructed (VCI adjusted) and is flagged |
| Source returns 429/403/HTML challenge | backoff 1→2→4→8 s; after 3 consecutive → `blocked`, feed stops, manifest `partial` with skipped list, UI ⏸ |
| Source changes payload shape | adapter validation (Pydantic) fails → feed `failed`, raw payload kept for a fixture; nothing partial is written |
| Partial tick pass (time or block) | manifest lists skipped symbols; status ⚠ Partial; re-run same evening picks up only skipped symbols (raw archive = cache) |
| Postgres down | API returns 503 with error code `DB_UNAVAILABLE`; web shows the "Cannot reach the local server" state |
| Duplicate/odd rows (same ts+seq different price) | upsert keeps the newer `fetched_at` and writes a `data_anomalies(rule=duplicate_tick)` row |

## 7. Sizing (from data.md §1–2)

~1,520 stocks + 21 ETFs; ~2–3 M ticks/day market-wide (FPT 3.9 k, SHB 10.9 k on 2026-10-15); ticks ≈ 15–25 MB/day
compressed + 10–20 MB/day raw gzip → 8–13 GB/year all feeds. Postgres with 1 GB `shared_buffers` and
Timescale compression keeps a 10-year daily what-if (≈ 2,500 rows) in the low milliseconds; N3 is CPU bound in
`services/analytics` (vectorised numpy over integer VND arrays, Decimal only at the ledger boundary).

## 8. Risks (technical)

| Risk | Mitigation |
|---|---|
| Unofficial endpoints change or block (C6) | 3 independent sources for daily (VCI, SSI, KBS-recent), 2 for ticks (KBS, VCI), fixtures per adapter, adapter swap is config (`FINVEST_SOURCE_TICKS=kbs`) |
| Tick `side` missing (KBS `LC` empty in probe) | `ticks.side` nullable; VCI provides side for the watchlist; features say "side unavailable" |
| Nominal history before crawl start is reconstructed | flagged `nominal_kind`, A18; R1 spike re-probes VNDirect/cafef for observed history |
| TimescaleDB adds ops surface | single `docker compose` image `timescale/timescaledb:2.17-pg16`; if it ever hurts, plain Postgres partitioning is a drop-in for these schemas (ADR-S-001 fallback) |
| Polling board misses ≤ 5 s | measured in R3; SSE path documented in ADR-S-004, no schema change |

## Open questions for the sponsor

- **A16 — Nguồn dữ liệu.** Thư viện `vnstock` (đề xuất ban đầu) hiện là bản biên dịch sẵn, giấy phép riêng, phải
  đăng ký tài khoản, bị PyPI cách ly (24/09/2026) và giới hạn thấp hơn nhiều so với chính các API nó gọi (1m chỉ
  180 ngày, tick 5.000 lệnh/lần, sổ lệnh/khối ngoại chỉ cho gói trả phí). Em đề xuất **tự viết adapter gọi thẳng API
  web công khai của KBS, Vietcap (VCI) và SSI iBoard** — không cần tài khoản, miễn phí, dữ liệu sâu hơn (daily từ
  2006, 1m ~3 năm, tick cả phiên trong 1 lệnh gọi), nhưng đây là API không chính thức: không có điều khoản sử dụng
  công bố, có thể đổi/chặn bất kỳ lúc nào (PRD C6), ta chỉ đọc, tốc độ ≤ 2 yêu cầu/giây, dừng ngay khi bị chặn.
  **Khuyến nghị: A16-A** chấp nhận dùng API không chính thức theo cách trên (vnstock cũng chỉ gọi đúng các API này);
  A16-B: chỉ dùng vnstock Community (đăng ký tài khoản miễn phí, chấp nhận giới hạn và mã biên dịch sẵn).
- **A17 — Dòng tiền tự doanh (PR-018, R5, Should).** Không tìm thấy nguồn miễn phí nào (vnstock chỉ có ở gói trả
  phí). **Khuyến nghị: A17-A** bỏ mục tự doanh khỏi PR-018 cho v1, giữ khối ngoại (có miễn phí, lưu từ ngày bắt đầu
  cào); A17-B: nhập tay từ báo chí hằng ngày (tốn công, dễ sai).
- **A18 — Giá danh nghĩa trước ngày bắt đầu cào.** Mọi nguồn miễn phí chỉ trả **giá đã điều chỉnh** cho lịch sử
  (ví dụ FPT 18/09/2026 = 65.182,47 sau khi chia thưởng 10 % ngày 21/09). Giá danh nghĩa thật chỉ quan sát được từ
  ngày ta bắt đầu cào; trước đó Finvest **tái dựng** giá danh nghĩa = giá điều chỉnh ÷ hệ số điều chỉnh (VN§6) và
  gắn cờ "tái dựng" trên mọi kết quả what-if dùng nó. Sai số có thể tới vài chục đồng do làm tròn bước giá.
  **Khuyến nghị: A18-A** chấp nhận, hiển thị cờ và ghi rõ trong "cách tính"; A18-B: what-if chỉ cho phép ngày mua
  từ khi có giá danh nghĩa quan sát được (mất phần lớn giá trị học L2 trong năm đầu).
