"""Tester: independent check of stored adj_factors / reconstructed bars on the test db (run: uv run python -I? no, plain)."""
import subprocess, collections, sys
from datetime import date
from fractions import Fraction as F
sys.path.insert(0, "tests_be05")
from test_oracle_ca import oracle, q12
from finvest_rules import CaEvent

def q(sql):
    out = subprocess.check_output(["docker","exec","finvest-test-be-db-1","psql","-U","finvest","-d","finvest","-AtF","|","-c",sql]).decode()
    return [l.split("|") for l in out.splitlines()]
n = lambda x: int(x) if x not in ("", None) else None
ev = collections.defaultdict(list)
for sym, typ, ex, a, b, cash, price in q("select symbol,type,ex_date,ratio_a,ratio_b,cash_per_share,issue_price from corporate_actions"):
    if typ == "cash_dividend" and not cash: continue
    if typ in ("stock_dividend","rights","split","merge") and (not a or not b): continue
    if typ == "rights" and not price: continue
    ev[(sym, ex)].append(CaEvent(typ, n(a), n(b), n(cash), n(price)))
fac = {(s, e): F(f) for s, e, f in q("select symbol,ex_date,factor from adj_factors")}
bars = collections.defaultdict(dict)
for s, d, c in q("select symbol,trading_date,c from bars_1d"):
    bars[s][d] = int(c)
bad = checked = 0
for (s, e), f in sorted(fac.items()):
    prior = [d for d in bars[s] if d < e]
    if not prior or (s, e) not in ev: continue
    P = bars[s][max(prior)]
    want = q12(oracle(ev[(s, e)], P)); checked += 1
    if abs(F(str(want)) - f) > F(2, 10**12) :
        bad += 1; print("MISMATCH", s, e, P, want, f) if bad < 15 else None
print("factors", len(fac), "checked", checked, "mismatch", bad)
# recon: nominal x G vs latest source row, per symbol
src = collections.defaultdict(dict)
for s, d, c, fa in q("select distinct on (symbol,trading_date) symbol,trading_date,adj_c,fetched_at from bars_1d_src where source='vci' order by symbol,trading_date,fetched_at desc"):
    src[s][d] = int(c)
worst = collections.Counter(); tot = 0; over1 = 0
for s in {k[0] for k in fac}:
    fs = sorted((e, f) for (s2, e), f in fac.items() if s2 == s)
    for d, nom in bars[s].items():
        if d not in src[s]: continue
        g = F(1)
        for e, f in fs:
            if e > d: g *= f
        tot += 1
        if abs(float(nom * g) - src[s][d]) > 1.0001: over1 += 1; worst[s] += 1
print("compared rows", tot, "diff>1VND", over1, dict(worst.most_common(5)))
