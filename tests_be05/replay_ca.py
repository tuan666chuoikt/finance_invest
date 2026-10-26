import os, re, sys
from datetime import date
from finvest_market_data.infrastructure import repositories as R
from finvest_crawler.feeds import corporate_actions as C
from finvest_crawler.settings import Settings
d = "/app/data/raw/corporate_actions/2026-10-26"
syms = sorted({re.sub(r"-p\d+\.json\.gz$", "", f) for f in os.listdir(d)})
R.ca_symbols_in_order = lambda conn, limit=None: syms
r = C.run_corporate_actions(Settings(), date(2026,10,26), budget=len(syms)+5)
print(len(syms), r)
