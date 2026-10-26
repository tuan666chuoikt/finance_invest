"""Tester: recompute ours = nominal x G vs the stored S2 rows (source ssi) per symbol; report 0.1 % mismatches."""
import subprocess, collections
from fractions import Fraction as F
def q(sql):
    out = subprocess.check_output(["docker","exec","finvest-test-be-db-1","psql","-U","finvest","-d","finvest","-AtF","|","-c",sql]).decode()
    return [l.split("|") for l in out.splitlines()]
fac = collections.defaultdict(list)
for s, e, f in q("select symbol,ex_date,factor from adj_factors order by 2"): fac[s].append((e, F(f)))
nom = collections.defaultdict(dict)
for s, d, c in q("select symbol,trading_date,c from bars_1d"): nom[s][d] = int(c)
res = collections.defaultdict(lambda: [0, 0, None, None])
for s, d, c in q("select distinct on (symbol,trading_date) symbol,trading_date,adj_c from bars_1d_src where source='ssi' order by symbol,trading_date,fetched_at desc"):
    if d not in nom[s]: continue
    g = F(1)
    for e, f in fac[s]:
        if e > d: g *= f
    ours = float(nom[s][d] * g); theirs = int(c)
    r = res[s]; r[0] += 1
    if theirs and abs(ours - theirs) / theirs * 100 > 0.1:
        r[1] += 1; r[2] = r[2] or d; r[3] = d
tot = sum(r[1] for r in res.values())
print("total >0.1% rows", tot, "of", sum(r[0] for r in res.values()))
for s, r in sorted(res.items(), key=lambda x: -x[1][1])[:30]: print(s, r)
