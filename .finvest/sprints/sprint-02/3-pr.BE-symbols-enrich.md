# 3-pr BE-symbols-enrich (round 1) - APPROVE
Head reviewed: c6d3fa49846c9ebdc20a1c7286b8a6c32701a9dd (already in sync with origin/sprint-02, no merge needed).
Files reviewed: all 13 (0005 migration, ports, tables, repositories, ssi source/payloads, vci source/payloads, kbs stub, feeds/symbols, 3 test files).
Must-fix: none.
Nits: (1) step 3 calls source_for("symbols") which raises Unsupported if the configured symbols source is not vci; fine today. (2) S1/index failure aborts the symbols run after V3 writes, uncommitted; acceptable (single txn).
Size: 240 ins / 12 del incl. tests vs plan ~200 (<=300): OK.
Checks: kernel 123 passed, ruff/mypy/lint-imports clean; db (throwaway timescale, *_test) 18 passed incl. 0005 round trip and membership/listed_at cases.
Merge sha: 5c44f692bb5d4eaef50b34e75798aa336adf5d38
