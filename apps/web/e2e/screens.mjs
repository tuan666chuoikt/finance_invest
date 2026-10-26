// Screenshots + axe + visual guards (FE-shots, F-132). Run: PW_DIR=/tmp/pw OUT=<dir> node e2e/screens.mjs  (stack on BASE, default 127.0.0.1:8080)
// Creates "E2E ..." scenarios for the cards shots and deletes them at the end. Never presses the real crawl button (job/crawl calls are mocked).
import { createRequire } from "node:module";
import fs from "node:fs";
const req = createRequire((process.env.PW_DIR || "/tmp/pw") + "/");
const { chromium } = req("playwright");
const AxeBuilder = req("@axe-core/playwright").default;
const BASE = process.env.BASE || "http://127.0.0.1:8080";
const OUT = process.env.OUT || "/tmp/pw/shots";
fs.mkdirSync(OUT, { recursive: true });
const PIN = "2026-10-16";
const res = [], metrics = {};
const ok = (n, c, i = "") => { res.push({ n, pass: !!c, i: String(i).slice(0, 300) }); console.log(c ? "PASS" : "FAIL", n, c ? "" : i); };
const J = (o) => ({ status: 200, contentType: "application/json", body: JSON.stringify(o) });
const job = (status, extra = {}) => ({ id: 99, kind: "crawl", status, created_at: new Date(Date.now() - 95000).toISOString(), finished_at: status === "running" ? null : new Date().toISOString(), progress: null, summary: null, error: null, ...extra });
const JOBS = {
  running: job("running", { progress: { step: 3, steps: 3, done: 18, total: 40, label: "corporate_actions" } }),
  failed: job("failed", { error: { message: "nguồn vci_iq đang chặn tạm, thử lại sau ~1 giờ", code: "SourceBlocked", source: "vci_iq", http_status: 0 }, progress: { step: 3, steps: 3, done: 18, total: 40 }, summary: { ticks: { symbols_fetched: 30, rows: 812344, symbols_skipped: 0 }, bars_1d: { sessions_added: 6, symbols_skipped: 0, symbols_deferred: 0 }, corporate_actions: { status: "blocked", symbols_checked: 18, events_upserted: 3, changes: 1, symbols_deferred: 22 } } }),
  done: job("done", { summary: { ticks: { symbols_fetched: 30, rows: 812344, symbols_skipped: 2 }, bars_1d: { sessions_added: 6, symbols_skipped: 0, symbols_deferred: 5 }, corporate_actions: { status: "partial", symbols_checked: 40, events_upserted: 3, changes: 1, symbols_deferred: 7 }, duration_s: 221 } }),
};

const b = await chromium.launch();
const mk = (w, h, scheme) => b.newContext({ viewport: { width: w, height: h }, colorScheme: scheme });
const api = (p, path, init) => p.evaluate(async ([path, init]) => { const r = await fetch("/api" + path, init); return { s: r.status, j: await r.json().catch(() => null) }; }, [path, init]);
const clean = async (p) => { await p.goto(BASE + "/"); for (const s of (await api(p, "/scenarios")).j.filter((s) => s.name.startsWith("E2E"))) await api(p, "/scenarios/" + s.id, { method: "DELETE" }); };
const post = (p, o) => api(p, "/scenarios", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(o) });

// seed real scenarios: lump FPT (P/L down), DCA HPG, lump up case (E1VFVN30-like picked by probe)
const sp = await (await mk(1280, 900, "light")).newPage();
await clean(sp);
const seed = [
  { name: "E2E FPT một lần", symbol: "FPT", style: "lump_sum", amount_vnd: 50000000, buy_date: "2025-03-03", sell_date: PIN },
  { name: "E2E HPG định kỳ", symbol: "HPG", style: "dca", amount_vnd: 2000000, buy_date: "2025-03-03", sell_date: null },
  { name: "E2E VNM nhỏ hơn 1 lô", symbol: "FPT", style: "lump_sum", amount_vnd: 10000000, buy_date: "2025-03-03", sell_date: null },
];
let up = null;
for (const sym of ["VCB", "SSI", "MWG", "VNM", "ACB"]) { // find a lump case with P/L up for the green card
  const r = await api(sp, "/whatif", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ symbol: sym, style: "lump_sum", amount_vnd: 50000000, buy_date: "2026-01-05", sell_date: null }) });
  const v = r.j?.result?.returns?.pl_pct?.value; if (v && Number(v) > 0) { up = sym; break; }
}
if (up) seed.push({ name: "E2E " + up + " lãi", symbol: up, style: "lump_sum", amount_vnd: 50000000, buy_date: "2026-01-05", sell_date: null });
ok("seed: a P/L-up scenario exists", !!up, "none of probe symbols up");
for (const s of seed) { const r = await post(sp, s); ok("seed " + s.name, r.s === 201 || r.s === 200, JSON.stringify(r.j).slice(0, 150)); }
await sp.context().close();

try {
  for (const [w, h] of [[375, 812], [1280, 800]]) for (const scheme of ["light", "dark"]) {
    const ctx = await mk(w, h, scheme);
    const tag = `${w}-${scheme}`;
    const open = async (mock, path = "/scenarios", wait = "h1") => {
      const p = await ctx.newPage();
      if (mock) await mock(p);
      await p.goto(BASE + path);
      if (wait) await p.waitForSelector(wait, { timeout: 10000 });
      return p;
    };
    const shot = async (p, name) => { if (!/loading|api-error/.test(name)) await p.waitForFunction(() => !/Đang tải/.test(document.querySelector('[data-testid="top-bar"]')?.textContent || ""), null, { timeout: 8000 }).catch(() => {}); await p.waitForTimeout(400); await p.screenshot({ path: `${OUT}/${name}-${tag}.png` }); };
    const settle = (p) => p.waitForFunction(() => !document.querySelector('[data-testid="scenario-card"] .skeleton, .skeleton') && document.querySelectorAll('[data-testid="scenario-card"]').length > 0 && ![...document.querySelectorAll('[data-testid="scenario-card"]')].some((c) => /Đang tính|Đang tải/.test(c.textContent)), null, { timeout: 20000 }).catch(() => {});
    const pre = async (p, name) => { // shared checks per shot
      const m = await p.evaluate(() => ({
        sw: document.documentElement.scrollWidth, ff: getComputedStyle(document.body).fontFamily, bg: getComputedStyle(document.body).backgroundColor,
        tbh: document.querySelector('[data-testid="top-bar"]')?.getBoundingClientRect().height ?? null,
        btns: [...document.querySelectorAll("button")].filter((e) => getComputedStyle(e).backgroundColor === "buttonface" || getComputedStyle(e).backgroundColor === "rgb(239, 239, 239)").length,
        serif: [...document.querySelectorAll("body *")].filter((e) => /serif/.test(getComputedStyle(e).fontFamily) && !/sans-serif|system-ui/.test(getComputedStyle(e).fontFamily)).length,
        cols: (() => { const g = document.querySelector(".sc-grid"); return g ? getComputedStyle(g).gridTemplateColumns.split(" ").length : null; })(),
      }));
      metrics[`${name}-${tag}`] = m;
      if (w === 375) ok(`${name}-${tag}: scrollWidth<=375`, m.sw <= 375, m.sw);
      ok(`${name}-${tag}: font system-ui, no serif`, /^system-ui/.test(m.ff) && m.serif === 0, m.ff + " serif=" + m.serif);
    };

    // (a) cards
    let p = await open(); await settle(p); await pre(p, "cards");
    const cardsN = await p.locator('[data-testid="scenario-card"]').count();
    ok(`cards-${tag}: >=3 real cards`, cardsN >= 3, cardsN);
    await shot(p, "cards");
    const ax = await new AxeBuilder({ page: p }).withRules(["color-contrast"]).analyze();
    ok(`axe color-contrast cards-${tag}`, ax.violations.length === 0, ax.violations.map((v) => v.nodes.map((n) => n.html.slice(0, 90)).join("|")).join(";"));
    const axAll = await new AxeBuilder({ page: p }).analyze();
    ok(`axe all rules cards-${tag}`, axAll.violations.length === 0, axAll.violations.map((v) => v.id + ":" + v.nodes.length).join(","));
    // focus ring
    const ring = async (loc, label) => {
      for (let i = 0; i < 60; i++) { await p.keyboard.press("Tab"); if (await loc.evaluate((e) => e === document.activeElement).catch(() => false)) break; }
      const f = await loc.evaluate((e) => { const s = getComputedStyle(e); return { on: e === document.activeElement, o: s.outlineStyle, w: s.outlineWidth, bs: s.boxShadow }; });
      ok(`focus ring ${label}-${tag}`, f.on && ((f.o !== "none" && parseFloat(f.w) >= 2) || f.bs !== "none"), JSON.stringify(f));
    };
    await p.evaluate(() => document.activeElement?.blur()); await p.mouse.click(2, 2).catch(() => {});
    await p.goto(BASE + "/scenarios"); await settle(p);
    await ring(p.getByRole("button", { name: /Thêm kịch bản/ }).first(), "add");
    if (w === 1280 && scheme === "light") await p.screenshot({ path: `${OUT}/focus-add-${tag}.png` });
    await ring(p.getByRole("button", { name: /^Bảng$/ }), "toggle");
    if (w === 1280 && scheme === "light") await p.screenshot({ path: `${OUT}/focus-toggle-${tag}.png` });
    await ring(p.locator('[data-testid="scenario-card"]').first().getByRole("button").first(), "card-i");
    if (w === 1280 && scheme === "light") await p.screenshot({ path: `${OUT}/focus-card-${tag}.png` });

    // (e) how computed
    const hb = p.locator('[data-testid="scenario-card"]').first().getByRole("button", { name: /Cách tính/ }).first();
    await hb.click(); await p.waitForSelector("dialog[open]");
    await pre(p, "how"); await shot(p, "how");
    const axh = await new AxeBuilder({ page: p }).withRules(["color-contrast"]).analyze();
    ok(`axe color-contrast how-${tag}`, axh.violations.length === 0, axh.violations.map((v) => v.nodes.map((n) => n.html.slice(0, 90)).join("|")).join(";"));
    await p.keyboard.press("Escape");

    // (d) form with validation error
    await p.getByRole("button", { name: /Thêm kịch bản/ }).first().click();
    const d = p.locator("dialog.scenario-panel"); await d.waitFor();
    await d.getByLabel(/^Tên/).fill("E2E form").catch(() => {});
    await d.getByRole("button", { name: /^Lưu$/ }).click();
    await p.waitForTimeout(500);
    ok(`form-${tag}: validation error shown`, (await d.locator('[role=alert], .err, [aria-invalid="true"]').count()) > 0);
    await pre(p, "form"); await shot(p, "form");
    const axf = await new AxeBuilder({ page: p }).withRules(["color-contrast"]).analyze();
    ok(`axe color-contrast form-${tag}`, axf.violations.length === 0, axf.violations.map((v) => v.nodes.map((n) => n.html.slice(0, 90)).join("|")).join(";"));
    await ring(d.locator("input,button,select").nth(1), "form-field");
    if (w === 1280 && scheme === "light") await p.screenshot({ path: `${OUT}/focus-form-${tag}.png` });
    await p.keyboard.press("Escape");

    // (c) table
    await p.getByRole("button", { name: /^Bảng$/ }).click(); await p.waitForSelector("table"); await settle2(p);
    await pre(p, "table"); await shot(p, "table");
    const axt = await new AxeBuilder({ page: p }).withRules(["color-contrast"]).analyze();
    ok(`axe color-contrast table-${tag}`, axt.violations.length === 0, axt.violations.map((v) => v.nodes.map((n) => n.html.slice(0, 90)).join("|")).join(";"));
    const tm = await p.evaluate(() => { const td = [...document.querySelectorAll("table tbody tr:first-child td")].map((e) => getComputedStyle(e)); const th = document.querySelector("table tbody tr:first-child th, table tbody tr:first-child td:first-child"); return { ta: td.map((s) => s.textAlign), tn: td.map((s) => s.fontVariantNumeric), pos: th && getComputedStyle(th).position }; });
    metrics[`table-${tag}`] = { ...metrics[`table-${tag}`], ...tm };
    await ctx.pages()[0]?.evaluate(() => localStorage.clear());
    await p.close();

    // mocks
    const empty = (pp) => pp.route("**/api/scenarios", (r) => r.request().method() === "GET" ? r.fulfill(J([])) : r.continue());
    p = await open(empty); await pre(p, "empty"); await shot(p, "empty");
    const axe_ = await new AxeBuilder({ page: p }).withRules(["color-contrast"]).analyze(); ok(`axe color-contrast empty-${tag}`, axe_.violations.length === 0, axe_.violations.map((v) => v.nodes.map((n) => n.html.slice(0, 90)).join("|")).join(";")); await p.close();
    for (const k of ["running", "failed"]) {
      p = await open((pp) => pp.route("**/api/jobs/current", (r) => r.fulfill(J(JOBS[k]))));
      await p.waitForSelector('[data-testid="crawl-status"]', { timeout: 8000 }).catch(() => {});
      ok(`crawl-${k}-${tag}: status line visible`, await p.locator('[data-testid="crawl-status"]').count() === 1, "no status line (done is shown only after a running state seen)");
      await settle(p); await pre(p, "crawl-" + k); await shot(p, "crawl-" + k);
      const axc = await new AxeBuilder({ page: p }).withRules(["color-contrast"]).analyze(); ok(`axe color-contrast crawl-${k}-${tag}`, axc.violations.length === 0, axc.violations.map((v) => v.nodes.map((n) => n.html.slice(0, 90)).join("|")).join(";")); await p.close();
    }
    p = await open((pp) => pp.route("**/api/scenarios", (r) => r.request().method() === "GET" ? r.abort("connectionrefused") : r.continue()), "/scenarios", "main");
    await p.waitForTimeout(3000); await pre(p, "api-error"); await shot(p, "api-error");
    const axa = await new AxeBuilder({ page: p }).withRules(["color-contrast"]).analyze(); ok(`axe color-contrast api-error-${tag}`, axa.violations.length === 0, axa.violations.map((v) => v.nodes.map((n) => n.html.slice(0, 90)).join("|")).join(";")); await p.close();
    p = await open((pp) => pp.route("**/api/scenarios", async (r) => { if (r.request().method() === "GET") { await new Promise((x) => setTimeout(x, 6000)); } r.continue().catch(() => {}); }), "/scenarios", "main");
    await p.waitForTimeout(800); await pre(p, "loading"); await shot(p, "loading"); await p.close();
    p = await open((pp) => pp.route("**/api/bars/1d/status", (r) => r.fulfill(J({ last_trading_date: null, as_of: null, source: "vci", symbols: 0 }))));
    await p.waitForTimeout(800); await pre(p, "nobars"); await shot(p, "nobars");
    const axn = await new AxeBuilder({ page: p }).withRules(["color-contrast"]).analyze(); ok(`axe color-contrast nobars-${tag}`, axn.violations.length === 0, axn.violations.map((v) => v.nodes.map((n) => n.html.slice(0, 90)).join("|")).join(";")); await p.close();
    await ctx.close();
  }
} finally {
  const dp = await (await mk(1280, 900, "light")).newPage();
  await clean(dp);
  ok("cleanup: no E2E scenarios left", (await api(dp, "/scenarios")).j.filter((s) => s.name.startsWith("E2E")).length === 0);
  await b.close();
  fs.writeFileSync(OUT + "/metrics.json", JSON.stringify({ metrics, res }, null, 1));
  console.log(res.filter((r) => r.pass).length + " pass / " + res.filter((r) => !r.pass).length + " fail");
}
async function settle2(p) { await p.waitForTimeout(1500); }
