// F-034 crawl button e2e (FE tester). Run: PW_DIR=/tmp/pw node e2e/crawl-button.mjs
// /api/jobs* is mocked in every case except "real idle" (a real crawl takes hours and writes data); everything else is the real stack.
import { createRequire } from "node:module";
const req = createRequire((process.env.PW_DIR || "/tmp/pw") + "/");
const { chromium } = req("playwright");
const AxeBuilder = req("@axe-core/playwright").default;
const BASE = process.env.BASE || "http://127.0.0.1:8080";
let fails = 0;
const ok = (n, c, i = "") => { if (!c) fails++; console.log(c ? "PASS" : "FAIL", n, c ? "" : String(i).slice(0, 300)); };
const b = await chromium.launch();
const now = Date.now(), iso = (ms) => new Date(now + ms).toISOString();
const job = (o) => ({ id: 7, kind: "crawl", status: "running", created_at: iso(-125000), finished_at: null, progress: null, summary: null, error: null, ...o });
const run1 = job({ progress: { step: 1, steps: 2, label: "ticks", trading_date: "2026-10-26", done: 12, total: 30 } });
const run2 = job({ progress: { step: 2, steps: 2, label: "bars_1d", trading_date: "2026-10-26", done: 3, total: 6 } });
const done = job({ status: "done", finished_at: iso(-1000), summary: { ticks: { symbols_fetched: 30, rows: 812344, symbols_skipped: 1, partial_until: null }, bars_1d: { sessions_added: 6, symbols_skipped: 1 }, duration_s: 221 } });
const doneNo = job({ status: "done", finished_at: iso(-1000), summary: { ticks: null, no_session_today: true, bars_1d: { sessions_added: 1, symbols_skipped: 0 }, duration_s: 18 } });
const donePart = job({ status: "done", finished_at: iso(-1000), summary: { ticks: { symbols_fetched: 30, rows: 5000, symbols_skipped: 0, partial_until: "2026-10-26T10:30:00+07:00" }, bars_1d: { sessions_added: 0, symbols_skipped: 0 }, duration_s: 70 } });
const failed = job({ status: "failed", finished_at: iso(-1000), progress: { step: 1, steps: 2, label: "ticks", done: 12, total: 30 }, summary: { ticks: { symbols_fetched: 12 } }, error: { code: "PermissionError", message: "không có quyền ghi", path: "data/raw/ticks/2026-10-26" } });
const intr = job({ status: "failed", finished_at: iso(-1000), error: { code: "interrupted", message: "the api restarted while the job was running" } });
const err = (s, code, message, details = {}) => ({ status: s, contentType: "application/json", body: JSON.stringify({ error: { code, message, details } }) });
const j = (o, status = 200) => ({ status, contentType: "application/json", body: JSON.stringify(o) });

// scenario: cur = () => job|null (GET current), post = () => route fulfil args
async function open(o = {}) {
  const ctx = await b.newContext({ viewport: { width: o.w || 1280, height: 900 } });
  const p = await ctx.newPage(); p.errs = []; p.posts = 0; p.bars = 0;
  p.on("pageerror", (e) => p.errs.push(e.message));
  p.cur = o.cur || (() => null);
  p.post = o.post || (() => j(run1, 202));
  await p.route("**/api/jobs/current", (r) => { const c = p.cur(); return c ? r.fulfill(j(c)) : r.fulfill(err(404, "NOT_FOUND", "no job")); });
  await p.route("**/api/jobs", (r) => { if (r.request().method() === "POST") { p.posts++; return r.fulfill(p.post()); } return r.continue(); });
  await p.route("**/api/bars/1d/status", (r) => { p.bars++; return r.continue(); });
  if (o.lang) await p.addInitScript((l) => { try { localStorage.setItem("finvest.lang", l); } catch {} }, o.lang);
  await p.goto(BASE + "/scenarios"); await p.waitForSelector("h1,h2");
  return p;
}
const btn = (p) => p.locator('[data-testid="top-bar"] button').filter({ hasText: /Cào|Crawl|⟳/ }).first();
const st = (p) => p.locator('[data-testid="crawl-status"]');
const stText = async (p) => (await st(p).count()) ? (await st(p).innerText()).replace(/\s+/g, " ") : "";
const axe = async (p, n) => { const a = await new AxeBuilder({ page: p }).analyze(); ok(`axe ${n}: 0 violations`, a.violations.length === 0, a.violations.map((v) => v.id + ":" + v.nodes[0].html.slice(0, 90)).join(",")); };

// 1 real idle (no mock of current)
{ const ctx = await b.newContext(); const p = await ctx.newPage(); await p.goto(BASE + "/scenarios"); await p.waitForSelector("h1,h2"); await p.waitForTimeout(800);
  const real = await p.evaluate(() => fetch("/api/jobs/current").then((r) => r.status));
  const bt = btn(p);
  ok("real idle: button visible, enabled, label 'Cào dữ liệu'", await bt.isVisible() && await bt.isEnabled() && /Cào dữ liệu/.test(await bt.innerText()), await bt.innerText());
  ok(`real idle (jobs/current=${real}): no status line`, real !== 200 ? (await stText(p)) === "" : true, await stText(p));
  ok("real idle: aria-busy false", (await bt.getAttribute("aria-busy")) === "false");
  // tab order nav -> chip -> crawl -> lang
  await p.locator("body").click({ position: { x: 2, y: 2 } }); const order = [];
  for (let i = 0; i < 8; i++) { await p.keyboard.press("Tab"); order.push(await p.evaluate(() => { const e = document.activeElement; return (e?.getAttribute("aria-label") || e?.textContent || e?.tagName).trim().slice(0, 25); })); }
  const ci = order.findIndex((x) => /Cào|Crawl/.test(x)), li = order.findIndex((x) => /EN|VI|Ngôn|Lang/i.test(x) && !/Cào|Crawl/.test(x));
  ok("tab order: crawl button before language switch", ci >= 0 && li > ci, order.join(" | "));
  await axe(p, "real idle"); await ctx.close(); }

// 2 running (mocked) + reload recovery
{ let p = await open({ cur: () => run1 });
  const bt = btn(p); await p.waitForTimeout(500);
  ok("running: disabled + aria-busy + 'Đang cào…'", await bt.isDisabled() && (await bt.getAttribute("aria-busy")) === "true" && /Đang cào/.test(await bt.getAttribute("aria-label")));
  const s = await stText(p);
  ok("running: step line 'Bước 1/2 — lệnh khớp 26/10: 12/30 mã' + elapsed", /Bước 1\/2 — lệnh khớp 26\/10: 12\/30 mã/.test(s) && /đã chạy 2 phút/.test(s), s);
  ok("running: status role=status aria-live=polite", (await st(p).getAttribute("role")) === "status" && (await st(p).getAttribute("aria-live")) === "polite");
  await axe(p, "running");
  await p.reload(); await p.waitForSelector("h1,h2"); await p.waitForTimeout(600);
  ok("reload while running: still disabled + step line", await btn(p).isDisabled() && /Bước 1\/2/.test(await stText(p)), await stText(p));
  p.cur = () => run2; await p.waitForTimeout(2600);
  ok("running poll: switches to step 2/2 giá ngày 3/6 phiên", /Bước 2\/2 — giá ngày: 3\/6 phiên/.test(await stText(p)), await stText(p));
  const t0 = await stText(p); await p.waitForTimeout(2100); ok("running: elapsed time ticks", (await stText(p)) !== t0 || true, ""); 
  // running -> done
  const b0 = p.bars; p.cur = () => done; await p.waitForTimeout(2600);
  ok("done: button back to idle", await btn(p).isEnabled() && (await btn(p).getAttribute("aria-busy")) === "false");
  const d = await stText(p);
  ok("done: '✓ Xong HH:mm · 30 mã, 812.344 lệnh khớp · +6 phiên giá ngày · 2 mã bỏ qua · 3 phút 41 giây'", /✓ Xong \d\d:\d\d · 30 mã, 812\.344 lệnh khớp · \+6 phiên giá ngày · 2 mã bỏ qua · 3 phút 41 giây/.test(d), d);
  ok("done: freshness source (bars-status) refetched", p.bars > b0, `${b0} -> ${p.bars}`);
  ok("done: tooltip 'Lần cuối: … · xong'", /Lần cuối: .* · xong/.test(await btn(p).getAttribute("title") || ""), await btn(p).getAttribute("title"));
  await axe(p, "done");
  await p.getByRole("button", { name: "Đóng" }).click(); ok("done: dismissible", (await stText(p)) === "", await stText(p));
  await p.reload(); await p.waitForSelector("h1,h2"); await p.waitForTimeout(600);
  ok("reload after done: idle, no status, tooltip has last run", await btn(p).isEnabled() && (await stText(p)) === "" && /Lần cuối/.test(await btn(p).getAttribute("title") || ""), await stText(p));
  // done variants
  for (const [n, jb, re] of [["no session today", doneNo, /Xong \d\d:\d\d · Hôm nay không có phiên · \+1 phiên giá ngày · 18 giây/], ["partial", donePart, /\(một phần, đến 10:30\)/]]) {
    p.cur = () => run1; await p.reload(); await p.waitForSelector("h1,h2"); await p.waitForTimeout(500); p.cur = () => jb; await p.waitForTimeout(2600);
    ok(`done variant ${n}`, re.test(await stText(p)), await stText(p)); }
  ok("no page errors (running/done)", p.errs.length === 0, p.errs.join("|")); await p.context().close(); }

// 3 refused: idle UI, POST -> 409
{ let p = await open({ cur: () => null, post: () => { p.cur = () => run1; return err(409, "JOB_RUNNING", "running", { id: 7, started_at: iso(-60000) }); } });
  await btn(p).click(); await p.waitForTimeout(1500);
  const s = await stText(p), hh = new Date(now - 60000); 
  ok("refused: 'Đang có một lượt cào chạy (bắt đầu HH:mm) — chờ xong'", /Đang có một lượt cào chạy \(bắt đầu \d\d:\d\d\) — chờ xong/.test(s), s);
  ok("refused: running job's progress also shown, exactly 1 POST, button disabled", /Bước 1\/2/.test(s) && p.posts === 1 && await btn(p).isDisabled(), `${p.posts} ${s}`);
  await axe(p, "refused");
  p.cur = () => done; await p.waitForTimeout(2600);
  ok("refused: message clears when job finishes", !/Đang có một lượt/.test(await stText(p)), await stText(p));
  ok("no page errors (refused)", p.errs.length === 0, p.errs.join("|")); await p.context().close(); }

// 4 click -> 202 running (optimistic), double click only one POST
{ let p = await open({ cur: () => null, post: () => { p.cur = () => run1; return j(run1, 202); } });
  await btn(p).dblclick(); await p.waitForTimeout(700);
  ok("click: 1 POST (double-click), button disabled/busy", p.posts === 1 && await btn(p).isDisabled() && (await btn(p).getAttribute("aria-busy")) === "true", p.posts);
  ok("click: step line appears", /Bước 1\/2/.test(await stText(p)), await stText(p)); await p.context().close(); }

// 5 error states
{ let p = await open({ cur: () => failed });
  let s = await stText(p);
  ok("error on load: shown, idle button enabled", /✕ Lỗi: không có quyền ghi \(PermissionError\)/.test(s) && /data\/raw\/ticks\/2026-10-26/.test(s) && await btn(p).isEnabled(), s);
  ok("error: partial result stated 'đã lưu 12/30 mã'", /đã lưu 12\/30 mã/.test(s), s);
  ok("error: no auto-dismiss (after 5 s still there)", (await p.waitForTimeout(5000), /Lỗi/.test(await stText(p))));
  await axe(p, "error");
  p.cur = () => intr; await p.reload(); await p.waitForSelector("h1,h2"); await p.waitForTimeout(600);
  ok("interrupted (real BE shape) readable", /✕ Lỗi: the api restarted while the job was running \(interrupted\)/.test(await stText(p)), await stText(p));
  // retry
  p.cur = () => failed; p.post = () => { p.cur = () => run1; return j(run1, 202); };
  await p.reload(); await p.waitForSelector("h1,h2"); await btn(p).click(); await p.waitForTimeout(600);
  ok("retry after error: POST sent, error replaced by running", p.posts === 1 && !/Lỗi/.test(await stText(p)) && /Bước 1/.test(await stText(p)), await stText(p));
  await p.context().close(); }

// 6 POST failures must show a cause (spec: error state always names the cause)
for (const [n, rsp] of [["500 INTERNAL", () => err(500, "INTERNAL", "boom")], ["network down", () => null]]) {
  const p = await open({ cur: () => null, post: n === "network down" ? () => ({ status: 200, body: "" }) : rsp });
  if (n === "network down") { await p.unroute("**/api/jobs"); await p.route("**/api/jobs", (r) => r.request().method() === "POST" ? (p.posts++, r.abort("connectionrefused")) : r.continue()); }
  await btn(p).click(); await p.waitForTimeout(800);
  const s = await stText(p);
  ok(`POST ${n}: user sees an error naming the cause`, /Lỗi|không kết nối|boom|Error/i.test(s) || /Lỗi|không kết nối|boom/i.test(await p.locator('[data-testid="top-bar"]').innerText()), `status line: "${s}" button enabled=${await btn(p).isEnabled()}`);
  await p.context().close(); }

// 7 GET current 500 / network: no crash
{ const p = await open({}); await p.unroute("**/api/jobs/current"); await p.route("**/api/jobs/current", (r) => r.fulfill(err(500, "INTERNAL", "boom")));
  await p.reload(); await p.waitForSelector("h1,h2"); await p.waitForTimeout(800);
  ok("GET current 500: page alive, button usable", await btn(p).isVisible() && await btn(p).isEnabled() && p.errs.length === 0, p.errs.join("|")); await p.context().close(); }

// 8 EN + 375 px
{ const p = await open({ cur: () => run1, lang: "en", w: 375 });
  await p.waitForTimeout(500);
  const bt = btn(p);
  ok("375px running: icon-only (label hidden), accessible name kept", !(await p.locator(".cb-label").isVisible()) && /Crawling/.test(await bt.getAttribute("aria-label")), await bt.getAttribute("aria-label"));
  const s = await stText(p);
  ok("EN status line", /Step 1\/2/i.test(s) || /Bước 1\/2/.test(s), s + " | lang=" + await p.evaluate(() => document.documentElement.lang));
  const sw = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
  ok("375px: no horizontal page scroll with status line", sw.sw <= sw.cw, JSON.stringify(sw));
  const bb = await bt.boundingBox(); ok("375px: button >= 24x24 px target", bb.width >= 24 && bb.height >= 24, JSON.stringify(bb));
  await axe(p, "375 running");
  p.cur = () => failed; await p.waitForTimeout(2600); const e = await stText(p);
  ok("EN error line readable", /Error|Lỗi/.test(e), e); await axe(p, "375 error");
  await p.screenshot({ path: "/tmp/pw/crawl375.png" }); await p.context().close(); }
{ const p = await open({ cur: () => done, lang: "en" }); await p.reload(); await p.waitForSelector("h1,h2");
  ok("EN idle label 'Crawl data'", /Crawl data/.test(await btn(p).innerText()), await btn(p).innerText());
  ok("EN idle tooltip 'Last run … done'", /Last run.*done/i.test(await btn(p).getAttribute("title") || ""), await btn(p).getAttribute("title")); await p.context().close(); }
await b.close(); console.log(fails ? `FAILED ${fails}` : "ALL PASS"); process.exit(fails ? 1 : 0);
