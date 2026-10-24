# ruff: noqa
import json,subprocess,urllib.request,sys
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_FLOOR
def q(sql):
    o=subprocess.check_output(["docker","compose","exec","-T","db","psql","-U","finvest","-At","-F","|","-c",sql],text=True)
    return [r.split("|") for r in o.strip().splitlines()]
def api(body):
    r=urllib.request.Request("http://127.0.0.1:8001/api/whatif",json.dumps(body).encode(),{"content-type":"application/json"})
    return json.load(urllib.request.urlopen(r))
def bars(sym):
    # latest fetch per (date) -> adj close
    return {r[0]:int(r[1]) for r in q(f"select distinct on (trading_date) trading_date,adj_c from bars_1d_src where symbol='{sym}' order by trading_date,fetched_at desc")}
rnd=lambda x:int(D(x).quantize(D(1),ROUND_HALF_UP))
def lump(sym,amt,buy):
    b=bars(sym); days=sorted(b); bd=next(d for d in days if d>=buy); sd=days[-1]
    p=b[bd]; fee=D("0.0015")
    lots=int((D(amt)/(D(p)*100*(1+fee))).to_integral_value(ROUND_FLOOR)); qty=lots*100
    bf=rnd(D(qty*p)*fee); cash=amt-qty*p-bf
    sp=b[sd]; sv=qty*sp; sf=rnd(D(sv)*fee); tax=rnd(D(sv)*D("0.001"))
    return dict(qty=qty,price=p,buy_fee=bf,cash=cash,sell=sd,sell_price=sp,sell_fee=sf,tax=tax,liq=sv-sf-tax+cash)

bad=0
for sym,amt,buy in [("FPT",50_000_000,"2025-03-03"),("HPG",30_000_000,"2025-06-10"),("VCB",100_000_000,"2024-01-15"),("FPT",5_000_000,"2025-03-03"),("MWG",77_777_777,"2025-11-05"),("SSI",12_345_678,"2023-07-03"),("FPT",50_000_000,"2024-02-10"),("ACB",999_999_999,"2020-03-31")]:
    try: o=lump(sym,amt,buy)
    except StopIteration: print(sym,"no bars"); continue
    try: r=api(dict(symbol=sym,style="lump_sum",amount_vnd=amt,buy_date=buy))["result"]
    except Exception as e: print("HTTP",sym,amt,buy,e,e.read()[:200]); continue
    v=r["value"]; liq=int(v["liquidation_vnd"]["value"]); sh=int(r["position"]["shares"]["value"])
    ok=(liq==o["liq"] and sh==o["qty"]); bad+=not ok
    print("OK " if ok else "BAD",sym,amt,buy,"api",sh,liq,"oracle",o["qty"],o["liq"],o["sell"])
print("bad",bad)

# DCA: monthly on day-of-month of buy_date (clamped), shifted forward to next bar day; cash carries
import calendar,datetime as dt
def dca(sym,amt,buy):
    b=bars(sym); days=sorted(b); end=dt.date.fromisoformat(days[-1]); y,m=map(int,buy.split("-")[:2]); dom=int(buy[8:])
    cash=0; sh=0; inv=0; out=[]
    while True:
        d=dt.date(y,m,min(dom,calendar.monthrange(y,m)[1]))
        if d>end: break
        n=next((x for x in days if x>=d.isoformat()),None)
        if n is None: break
        cash+=amt; inv+=amt; p=b[n]
        lots=int((D(cash)/(D(p)*100*D("1.0015"))).to_integral_value(ROUND_FLOOR)); q=lots*100
        if q: f=rnd(D(q*p)*D("0.0015")); cash-=q*p+f; sh+=q
        out.append((n,q,cash)); m+=1
        if m>12: m=1;y+=1
    sp=b[days[-1]]; mv=sh*sp; liq=mv-rnd(D(mv)*D("0.0015"))-rnd(D(mv)*D("0.001"))+cash
    return sh,cash,inv,liq,out
for sym,amt,buy in [("HPG",2_000_000,"2025-03-31"),("FPT",5_000_000,"2025-01-15"),("MWG",1_500_000,"2025-02-28"),("ACB",10_000_000,"2025-06-05")]:
    o=dca(sym,amt,buy); r=api(dict(symbol=sym,style="dca",amount_vnd=amt,buy_date=buy))["result"]
    got=(int(r["position"]["shares"]["value"]),int(r["position"]["cash"]["value"]),int(r["position"]["invested_vnd"]["value"]),int(r["value"]["liquidation_vnd"]["value"]))
    ok=got==o[:4] and [(c["date"],c["qty"],c["cash_after"]) for c in r["contributions"]]==o[4]
    print("OK " if ok else "BAD","DCA",sym,amt,buy,got,o[:4]); bad+=not ok
print("bad total",bad)
