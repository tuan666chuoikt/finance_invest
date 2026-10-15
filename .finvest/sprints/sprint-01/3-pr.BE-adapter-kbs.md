# 3-pr BE-adapter-kbs, round 1 (lead: sonnet)
Verdict: APPROVE. Reviewed head 77938317b6a3c39cb328251eada9a14f5df5c0d6 (already contains origin/sprint-01 bfe14bc, no sync commit needed).
Files reviewed: adapters/kbs/{__init__,payloads,source}.py, tests/test_adapter_kbs.py, both fixtures, ports.py (outside-set edit).
- Contract: price int VND, volume shares, seq=AVO, side B|S|None, ts local VN -> UTC with cc*10000 us, URL exactly K1 with limit=50000; Unsupported for symbols()/bars(); SourceNoLongerServes on empty or date mismatch with served_date; PayloadShapeError names archive path.
- Real fixture checked: 50 rows, envelope {data}, FMP/FV/AVO/LC as documented. Sort by AVO (not t) justified by builder's 3,870-row verification.
- Outside-set edit (ports.py SourceNoLongerServes ctor, served_date) is backwards compatible and required by acceptance; accepted. Card example row asserted via synthetic row (deviation reported; fine).
- Tests fail without the change (each acceptance bullet covered); network disabled via MockTransport.
Nits (non-blocking): symbol is interpolated into the URL without validation (host allowlist limits impact; feed passes symbols from the symbol list, validate there); mypy kernel scope excludes crawler.
Checks: make test-kernel exit 0, 34 passed, ruff ok, mypy ok, lint-imports ok.
Merged into sprint-01: 53e6d99029
