// Real-stack e2e (FE tester). Run: PW_DIR=/tmp/pw node e2e/real-stack.mjs  (playwright + @axe-core/playwright installed in PW_DIR)
// Needs the stack on BASE (default http://127.0.0.1:8080). Creates scenarios named "E2E ..." and deletes them at the end.
import { createRequire } from "node:module";
const req = createRequire((process.env.PW_DIR || "/tmp/pw") + "/");
const { chromium } = req("playwright");
const AxeBuilder = req("@axe-core/playwright").default;
const BASE = process.env.BASE || "http://127.0.0.1:8080";
const res = [];
const ok = (name, cond, info = "") => { res.push({ name, pass: !!cond, info: String(info).slice(0, 300) }); console.log(cond ? "PASS" : "FAIL", name, cond ? "" : info); };

const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1280, height: 900 } });
const p = await ctx.newPage();
const errs = []; p.on("pageerror", (e) => errs.push(e.message));
const goto = async () => { await p.goto(BASE + "/scenarios"); await p.waitForSelector("h1,h2", { timeout: 10000 }); };
const api = (path, init) => p.evaluate(async ([path, init]) => { const r = await fetch("/api" + path, init); return { s: r.status, j: await r.json().catch(() => null) }; }, [path, init]);

async function fill(f) {
  await p.getByRole("button", { name: /Thêm kịch bản|Add scenario/ }).first().click();
  const d = p.locator("dialog.scenario-panel");
  await d.waitFor();
  if (f.name) await d.getByLabel(/^(Tên|Name)/).fill(f.name);
  const cb = d.getByRole("combobox"); await cb.fill(f.symbol);
  await p.getByRole("option").first().waitFor(); await cb.press("Enter");
  if (f.dca) await d.getByLabel(/Mua định kỳ|Monthly DCA/).check();
  await d.locator('input[inputmode="numeric"]').fill(f.amount);
  await d.locator('input[type="date"]').first().fill(f.start);
  if (f.end) { await d.getByLabel(/Hôm nay|Today/).uncheck(); await d.locator('input[type="date"]').nth(1).fill(f.end); }
  return d;
}
const card = (n) => p.locator(`[data-testid="scenario-card"][aria-label="${n}"]`);
const nameVisible = async (n) => (await card(n).innerText()).includes(n);

// pre-clean leftovers of an aborted run (the page crashes while one with a null-benchmark result exists)
await p.goto(BASE + "/"); for (const s of (await api("/scenarios")).j.filter((s) => s.name.startsWith("E2E"))) await api("/scenarios/" + s.id, { method: "DELETE" });
process.on("uncaughtException", async (e) => { console.log("ABORT", e.message.split("\n")[0]); try { for (const s of (await api("/scenarios")).j.filter((s) => s.name.startsWith("E2E"))) await api("/scenarios/" + s.id, { method: "DELETE" }); } catch {} process.exit(2); });
await goto();
await p.waitForFunction(() => !/Đang tải|Loading/.test(document.querySelector('[data-testid="top-bar"]')?.textContent || ""), null, { timeout: 8000 }).catch(() => {});
ok("shell: disclaimer both lines", /không phải lời khuyên đầu tư/.test(await p.locator('[data-testid="disclaimer"]').innerText()) && /not investment advice/.test(await p.locator('[data-testid="disclaimer"]').innerText()));
ok("shell: freshness chip", /Dữ liệu đến/.test(await p.locator('[data-testid="top-bar"]').innerText()), await p.locator('[data-testid="top-bar"]').innerText());
const a0 = await new AxeBuilder({ page: p }).analyze();
ok("axe empty page: 0 violations", a0.violations.length === 0, a0.violations.map((v) => v.id + ":" + v.nodes.length + ":" + v.nodes[0].html.slice(0, 80)).join(","));

// U1 probe (unpatched): a saved scenario while VN-Index is empty (first_available:null) must not crash the page.
{
  const q = await api("/scenarios", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "E2E probe", symbol: "FPT", style: "lump_sum", amount_vnd: 50000000, buy_date: "2025-03-03", sell_date: null }) });
  await goto(); await p.waitForTimeout(2500);
  const crashed = /Unexpected Application Error/.test(await p.locator("body").innerText());
  ok("U1 unpatched: page survives VN-Index benchmark with first_available=null", !crashed, "page shows 'Unexpected Application Error' (" + errs.join("|").slice(0, 120) + ")");
  await api("/scenarios/" + q.j.id, { method: "DELETE" }); errs.length = 0;
  // the rest of the run patches ONLY first_available:null -> a date so the other flows can be exercised
  await p.route("**/api/whatif", async (route) => { const r = await route.fetch(); const j = await r.json(); for (const x of j.result?.benchmarks ?? []) if (x.available === false && x.first_available == null) x.first_available = "2025-01-02"; await route.fulfill({ response: r, json: j }); });
  await goto();
}

// 1 lump-sum FPT
let d = await fill({ name: "E2E FPT lump", symbol: "FPT", amount: "50000000", start: "2025-03-03" });
await d.getByRole("button", { name: /Lưu|Save/ }).click();
let c = card("E2E FPT lump"); await c.waitFor({ timeout: 15000 }).catch(async (e) => { console.log("DBG", errs, (await p.locator("body").innerText()).slice(0, 600)); throw e; });
await p.waitForFunction(() => /Giá trị nếu bán/.test(document.querySelector('[data-testid="scenario-card"]')?.textContent || ""), null, { timeout: 15000 }).catch(() => {});
let txt = await c.innerText(); console.log(txt);
ok("lump FPT: liquidation 30.152.493 ₫", txt.includes("30.152.493"), txt);
ok("lump FPT: P/L −39,70 % (2dp, U+2212)", /−39,70 %/.test(txt), txt);
ok("U3 card shows the user-given scenario name (UX: card shows name)", await nameVisible("E2E FPT lump"), txt.split("\n")[0]);
ok("lump FPT: invested 50.000.000", txt.includes("50.000.000"));
ok("lump FPT: approximate flag on card", await c.locator('[data-testid="approximate-flag"]').count() === 1);
ok("lump FPT: down arrow cue", /▼/.test(txt), txt);
const sc = (await api("/scenarios")).j; const fpt = sc.find((s) => s.name === "E2E FPT lump");
const wi = await api("/whatif", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ symbol: "FPT", style: "lump_sum", amount_vnd: 50000000, buy_date: "2025-03-03", sell_date: null }) });
console.log("whatif probe", wi?.s, JSON.stringify(wi?.j)?.slice(0, 700));
const body = JSON.stringify(wi?.j || {});
ok("API: 400 shares", /"shares"\s*:\s*(400|"400")/.test(body), body.slice(0, 200));
ok("API: -39.6950", body.includes("-39.6950"), body.slice(0, 200));

// how computed
await c.getByRole("button", { name: /Cách tính|How computed/ }).first().click();
const hd = p.locator("dialog[open]").filter({ hasText: /Công thức|Formula/ });
ok("how-computed panel opens with formula + rules version", await hd.count() > 0 && /Phiên bản quy tắc|Rules version/.test(await hd.first().innerText()), await hd.first().innerText().catch(() => ""));
const ha = await new AxeBuilder({ page: p }).analyze();
ok("axe with how-panel open: 0 violations", ha.violations.length === 0, ha.violations.map((v) => v.id + ":" + v.nodes.length + ":" + v.nodes[0].html.slice(0, 110)).join(","));
await p.keyboard.press("Escape");
ok("how-computed closes on Esc", await p.locator("dialog[open]").filter({ hasText: /Công thức|Formula/ }).count() === 0);

// 2 DCA HPG
d = await fill({ name: "E2E HPG dca", symbol: "HPG", dca: true, amount: "2000000", start: "2025-03-03" });
await d.getByRole("button", { name: /Lưu|Save/ }).click();
c = card("E2E HPG dca"); await c.waitFor({ timeout: 15000 });
await p.waitForFunction(() => [...document.querySelectorAll('[data-testid="scenario-card"]')].some((e) => /HPG/.test(e.getAttribute("aria-label")||"")||/HPG/.test(e.textContent) && /Giá trị nếu bán/.test(e.textContent)), null, { timeout: 15000 }).catch(() => {});
txt = await c.innerText(); console.log(txt);
ok("DCA HPG: card shows monthly + day", /Mỗi tháng 2\.000\.000 ₫ \(ngày 3\)/.test(txt), txt);
ok("DCA HPG: value + cash left shown", /Giá trị nếu bán/.test(txt) && /Tiền mặt còn/.test(txt), txt);
ok("DCA HPG: approximate flag", await c.locator('[data-testid="approximate-flag"]').count() === 1);

// below one lot
d = await fill({ name: "E2E FPT tiny", symbol: "FPT", amount: "10000000", start: "2025-03-03" });
await d.getByRole("button", { name: /Lưu|Save/ }).click();
c = card("E2E FPT tiny"); await c.waitFor({ timeout: 15000 });
await p.waitForTimeout(2500);
txt = await c.innerText(); console.log(txt);
ok("below-one-lot note on card", /Ít hơn 1 lô/.test(txt), txt);
ok("below-one-lot: no crash / value shown", !/Không tính được/.test(txt), txt);

// refused pre-2025
d = await fill({ name: "E2E old", symbol: "FPT", amount: "10000000", start: "2020-01-02" });
await d.getByRole("button", { name: /Lưu|Save/ }).click();
await p.waitForTimeout(3500);
const afterTxt = await p.locator("body").innerText();
const stillForm = await p.locator("dialog.scenario-panel").count();
const oldCard = await card("E2E old").count();
console.log("pre-2025: form open", stillForm, "card", oldCard);
if (oldCard) console.log(await card("E2E old").innerText());
const shownMsg = stillForm ? await p.locator("dialog.scenario-panel [role=alert]").allInnerTexts() : [];
ok("pre-2025: no page crash", errs.length === 0 && (await p.locator("h1,h2").count()) > 0, errs.join("|"));
ok("pre-2025: clear message (form error or card error) not a raw code", (shownMsg.join(" ") + (oldCard ? await card("E2E old").innerText() : "")).trim().length > 0 && !/no_trading_day_near_buy|^\s*VALIDATION\s*$/.test(shownMsg.join(" ")), JSON.stringify(shownMsg) + " card=" + oldCard);
await p.screenshot({ path: "/tmp/pw/pre2025.png" });
if (stillForm) await p.keyboard.press("Escape");

// table view + axe + card view
await p.getByRole("button", { name: /Bảng|Table/ }).first().click();
await p.waitForSelector("table");
const rows = await p.locator("table tbody tr").count();
ok("table view lists scenarios", rows >= 3, rows);
ok("table: footer + approximate on rows", /không dự báo|does not predict/.test(await p.locator("body").innerText()) && (await p.locator("table").innerText()).match(/Xấp xỉ|Gần đúng|Approximate/g)?.length >= 3);
const tt = await p.locator("table tbody").innerText();
ok("U7 table P/L ₫ uses the same minus sign (U+2212) as P/L %", !/(^|\s)-\d/.test(tt), tt);
const at = await new AxeBuilder({ page: p }).analyze();
ok("axe table view: 0 violations", at.violations.length === 0, at.violations.map((v) => v.id + ":" + v.nodes.length + ":" + v.nodes[0].html.slice(0, 110)).join(","));
await p.getByRole("button", { name: /Thẻ|Cards/ }).first().click();

// EN/VI switch
await p.getByRole("button", { name: "EN", exact: true }).click();
await p.waitForTimeout(300);
let bt = await p.locator("body").innerText();
ok("EN: labels switch", /Investment scenarios/.test(bt) && /Value if sold/.test(bt) && /Approximate — adjusted prices/.test(bt), bt.slice(0, 300));
ok("EN: numbers stay vi-VN", bt.includes("30.152.493"));
ok("EN: html lang", await p.evaluate(() => document.documentElement.lang) === "en");
await p.reload(); await p.waitForSelector("h1,h2");
ok("EN persists on reload", /Investment scenarios/.test(await p.locator("body").innerText()));
const ae = await new AxeBuilder({ page: p }).analyze();
ok("axe EN cards: 0 violations", ae.violations.length === 0, ae.violations.map((v) => v.id + ":" + v.nodes.length + ":" + v.nodes[0].html.slice(0, 110)).join(","));

// edit (EN UI)
c = card("E2E FPT tiny");
await c.getByRole("button", { name: /Options for scenario/ }).click();
await p.getByRole("menuitem", { name: "Edit" }).click();
d = p.locator("dialog.scenario-panel"); await d.waitFor();
await d.locator('input[inputmode="numeric"]').fill("50000000");
await d.getByRole("button", { name: "Save" }).click();
await p.waitForTimeout(3000);
const tinyAfter = await card("E2E FPT tiny").innerText();
console.log(tinyAfter);
ok("edit: recomputed to 50M (30.152.493 and no below-lot note)", tinyAfter.includes("30.152.493") && !/Below one lot/.test(tinyAfter), tinyAfter);
const names = (await api("/scenarios")).j.filter((s) => s.name.startsWith("E2E")).length;
ok("edit did not duplicate", names === 4, names);

// 375px
await p.setViewportSize({ width: 375, height: 800 });
await p.waitForTimeout(500);
const sw = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
ok("375px: no horizontal page scroll (cards)", sw.sw <= sw.cw, JSON.stringify(sw));
await p.screenshot({ path: "/tmp/pw/m375.png", fullPage: true });
await p.getByRole("button", { name: /Add scenario/ }).first().click();
const fw = await p.locator("dialog.scenario-panel").boundingBox();
ok("375px: form fills viewport width", fw && fw.width >= 370, JSON.stringify(fw));
await p.screenshot({ path: "/tmp/pw/m375form.png" });
await p.keyboard.press("Escape");
await p.getByRole("button", { name: /Table/ }).first().click();
const sw2 = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
ok("375px: table view no page-level horizontal scroll", sw2.sw <= sw2.cw, JSON.stringify(sw2));
const am = await new AxeBuilder({ page: p }).analyze();
ok("axe 375px table: 0 violations", am.violations.length === 0, am.violations.map((v) => v.id + ":" + v.nodes.length + ":" + v.nodes[0].html.slice(0, 110)).join(","));
await p.getByRole("button", { name: /Cards/ }).first().click();
await p.setViewportSize({ width: 1280, height: 900 });

// delete all E2E via UI (first one via UI confirm, rest via API)
c = card("E2E HPG dca");
await c.getByRole("button", { name: /Options for scenario/ }).click();
await p.getByRole("menuitem", { name: "Delete" }).click();
await p.locator("dialog[open]").filter({ hasText: /Delete scenario/ }).getByRole("button", { name: "Delete" }).click();
await p.waitForTimeout(1200);
ok("delete via confirm removes card", await card("E2E HPG dca").count() === 0);
for (const s of (await api("/scenarios")).j.filter((s) => s.name.startsWith("E2E"))) await api("/scenarios/" + s.id, { method: "DELETE" });
await p.reload(); await p.waitForTimeout(1000);
ok("cleanup: no E2E scenarios left", (await api("/scenarios")).j.filter((s) => s.name.startsWith("E2E")).length === 0);
ok("no uncaught page errors during run", errs.length === 0, errs.join("|"));
await b.close();
const f = res.filter((r) => !r.pass).length;
console.log(`\nTOTAL ${res.length - f} pass / ${f} fail`);
process.exit(f ? 1 : 0);
