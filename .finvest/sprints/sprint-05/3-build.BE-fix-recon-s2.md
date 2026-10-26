# 3-build BE-fix-recon-s2
Result: done. S2 rows stored/compared as `ssi_s2` (bars retagged with dataclasses.replace in `_cross_check`, since the adapter emits source `ssi`); `crawl recon` exits 1 on missing, mismatches or ssi_mismatches.
Files: services/crawler/finvest_crawler/feeds/recon.py, finvest_crawler/cli.py, tests/test_recon_feed.py (~+18/-7).
Contract: data.md §3 bars_1d_src source list vci | ssi_s2.
Checks: recon tests 13 passed (new exit 1/0 test; S2 test asserts row under ssi_s2, none under ssi); crawler suite 198 passed; ruff clean.
Tests need FINVEST_DATABASE_URL=...@localhost:15433/finvest_test.
Deviations / outside-set edits: none.
