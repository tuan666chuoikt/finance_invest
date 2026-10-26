// S05 FE test: 768/800 (+375/1280 done state, th/DCA/topbar metrics). Run: PW_DIR=/tmp/pw BASE=.. OUT=.. node e2e/fe05-widths.mjs
import { createRequire } from "node:module";
const req = createRequire((process.env.PW_DIR || "/tmp/pw") + "/");
const { chromium } = req("playwright"); const AxeBuilder = req("@axe-core/playwright").default;
const BASE = process.env.BASE, OUT = process.env.OUT;
const J = (o) => ({ status: 200, contentType: "application/json", body: JSON.stringify(o) });
const job = (status, x = {}) => ({ id: 99, kind: "crawl", status, created_at: new Date(Date.now() - 95000).toISOString(), finished_at: status === "running" ? null : new Date().toISOString(), progress: null, summary: null, error: null, ...x });
const run = job("running", { progress: { step: 3, steps: 3, done: 18, total: 40, label: "corporate_actions" } });
const done = job("done", { summary: { ticks: { symbols_fetched: 30, rows: 812344, symbols_skipped: 2 }, bars_1d: { sessions_added: 6, symbols_skipped: 0, symbols_deferred: 5 }, corporate_actions: { status: "partial", symbols_checked: 40, events_upserted: 3, changes: 1, symbols_deferred: 7 }, duration_s: 221 } });
const res = []; const ok = (n, c, i = "") => { res.push({ n, pass: !!c, i }); console.log(c ? "PASS" : "FAIL", n, c ? "" : i); };
const b = await chromium.launch();
const ctx0 = await b.newContext(); const p0 = await ctx0.newPage(); await p0.goto(BASE + "/");
const api = (path, init) => p0.evaluate(async ([path, init]) => { const r = await fetch("/api" + path, init); return r.json().catch(() => null); }, [path, init]);
const H = { "content-type": "application/json" };
const clean = async () => { for (const s of (await api("/scenarios")).filter((s) => s.name.startsWith("E2E"))) await api("/scenarios/" + s.id, { method: "DELETE" }); };
await clean();
for (const [n, s, st] of [["E2E lump", "FPT", "lump_sum"], ["E2E dca", "HPG", "dca"], ["E2E dca2", "ACB", "dca"]]) await api("/scenarios", { method: "POST", headers: H, body: JSON.stringify({ name: n, symbol: s, style: st, amount_vnd: 2000000, buy_date: "2025-03-03", sell_date: "2026-10-16" }) });
try {
for (const [w, h] of [[768, 1024], [800, 900], [375, 812], [1280, 800]]) for (const scheme of ["light", "dark"]) {
  const tag = `${w}-${scheme}`; const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: scheme });
  const light = scheme === "light";
  // (a) cards
  let p = await ctx.newPage(); await p.goto(BASE + "/scenarios"); await p.waitForSelector(".sc-card"); await p.waitForFunction(() => !document.querySelector(".skeleton") && ![...document.querySelectorAll(".sc-card")].some((c) => /Đang tính|Đang tải/.test(c.textContent)), null, { timeout: 20000 }).catch(() => {}); await p.waitForTimeout(600);
  const m = await p.evaluate(() => {
    const tb = document.querySelector('[data-testid="top-bar"]'); const ch = [...tb.querySelectorAll("a,button,span")].filter((e) => e.children.length === 0 && e.textContent.trim());
    const lines = (e) => { const r = document.createRange(); r.selectNodeContents(e); return new Set([...r.getClientRects()].map((q) => Math.round(q.top))).size; };
    const wrapped = ch.filter((e) => e.getBoundingClientRect().height > 0 && lines(e) > 1).map((e) => e.textContent.trim());
    const tops = new Set([...tb.querySelectorAll("a,button")].filter((e) => e.getBoundingClientRect().width > 0).map((e) => Math.round(e.getBoundingClientRect().top / 8))).size;
    const g = document.querySelector(".sc-grid");
    const hd = document.querySelector("main h1"); 
    const dca = [...document.querySelectorAll(".sc-card")].map((c) => ({ txt: c.textContent.length, shift: [...c.querySelectorAll("*")].filter((e) => e.children.length === 0 && /dời sang/.test(e.textContent)).length }));
    return { sw: document.documentElement.scrollWidth, tbh: tb.getBoundingClientRect().height, wrapped, tops, cols: g ? getComputedStyle(g).gridTemplateColumns.split(" ").length : null, hdh: hd?.getBoundingClientRect().height, dca, lh: hd && parseFloat(getComputedStyle(hd).lineHeight) };
  });
  console.log(tag, JSON.stringify(m));
  ok(`topbar one line ${tag}`, m.tbh <= 54 && m.wrapped.length === 0, JSON.stringify([m.tbh, m.wrapped]));
  if (w === 375) ok(`375 no hscroll`, m.sw <= 375, m.sw);
  if (w === 800) ok(`800 2 cols`, m.cols === 2, m.cols); if (w === 1280) ok(`1280 3 cols`, m.cols === 3, m.cols); if (w === 375) ok(`375 1 col`, m.cols === 1, m.cols);
  ok(`page header single line ${tag}`, m.hdh == null || m.hdh <= m.lh * 1.5 + 2, JSON.stringify([m.hdh, m.lh]));
  ok(`DCA shift <=1 line ${tag}`, m.dca.every((d) => d.shift <= 1), JSON.stringify(m.dca));
  if (w >= 768) { const ax = await new AxeBuilder({ page: p }).analyze(); ok(`axe all cards ${tag}`, ax.violations.length === 0, ax.violations.map((v) => v.id).join()); }
  if (w === 1280) { // DCA details + table headers
    const det = p.locator(".sc-card details").first(); if (await det.count()) { await det.locator("summary").click(); await p.waitForTimeout(200); await p.screenshot({ path: `${OUT}/FE-rw-dca-details-${tag}.png` }); }
  }
  await p.screenshot({ path: `${OUT}/cards-${tag}.png` });
  await p.getByRole("button", { name: /^Bảng$/ }).click(); await p.waitForSelector("table"); await p.waitForTimeout(1200);
  const t = await p.evaluate(() => [...document.querySelectorAll("table thead th")].map((th) => { const lh = parseFloat(getComputedStyle(th).lineHeight) || 16; return { t: th.textContent.trim().slice(0, 30), l: Math.round((th.getBoundingClientRect().height - 16) / lh) } }));
  console.log("th", tag, JSON.stringify(t.map((x) => x.l)));
  if (w === 1280) ok(`table th <=2 lines ${tag}`, t.every((x) => x.l <= 2), JSON.stringify(t));
  await p.screenshot({ path: `${OUT}/FE-rw-table-${tag}.png` }); await p.close();
  // (f) crawl running + done
  for (const [k, seq] of [["running", [run]], ["done", [run, run, done]]]) {
    p = await ctx.newPage(); let n = 0; await p.route("**/api/jobs/current", (r) => r.fulfill(J(seq[Math.min(n++, seq.length - 1)])));
    await p.goto(BASE + "/scenarios"); await p.waitForSelector("h1");
    if (k === "done") await p.waitForFunction(() => /Xong/.test(document.querySelector('[data-testid="crawl-status"]')?.textContent || ""), null, { timeout: 30000 }).catch(() => {});
    await p.waitForSelector('[data-testid="crawl-status"]', { timeout: 8000 }).catch(() => {}); await p.waitForTimeout(500);
    const txt = await p.locator('[data-testid="crawl-status"]').first().textContent().catch(() => null); console.log(tag, k, txt);
    if (k === "running") ok(`crawl running step 3 ${tag}`, /3\/3/.test(txt || "") && /18\/40/.test(txt || ""), txt);
    else ok(`crawl done ${tag}`, /3 sự kiện quyền|sự kiện/.test(txt || "") && /1 thay đổi/.test(txt) && /12 mã chờ lượt sau/.test(txt), txt);
    const sw = await p.evaluate(() => [document.documentElement.scrollWidth, document.querySelector('[data-testid="top-bar"]').getBoundingClientRect().height]); ok(`crawl-${k} no overflow/bar ${tag}`, sw[0] <= w && sw[1] <= 54, sw);
    const ax = await new AxeBuilder({ page: p }).withRules(["color-contrast"]).analyze(); ok(`axe contrast crawl-${k} ${tag}`, ax.violations.length === 0, ax.violations.map((v) => v.nodes.map((n) => n.html.slice(0, 80))).join());
    await p.screenshot({ path: `${OUT}/crawl-${k}-${tag}.png` }); await p.close();
  }
  await ctx.close();
}
} finally { await clean(); await b.close(); console.log(res.filter((r) => r.pass).length + " pass / " + res.filter((r) => !r.pass).length + " fail"); }
