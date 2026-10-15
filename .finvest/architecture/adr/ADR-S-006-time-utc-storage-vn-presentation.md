# ADR-S-006 — Time: store UTC TIMESTAMPTZ, present Asia/Ho_Chi_Minh; trading_date is a VN DATE
Status: Accepted · 2026-10-15

## Decision
All instants are tz-aware and stored as TIMESTAMPTZ (UTC). `trading_date` is a DATE in Asia/Ho_Chi_Minh (UTC+7,
no DST) and is the key for daily tables, manifests and the calendar. API payloads render instants with the
`+07:00` offset; the web never converts time zones. Source time strings (KBS "2026-10-15 14:45:08:16" local,
VCI epoch seconds UTC, SSI epoch seconds) are converted in adapters only. Session phases come from
`finvest_rules` against the calendar, never from data presence (PR-002).
