// One-off 768 px shot (cards + table + how). Run: PW_DIR=/tmp/pw OUT=<dir> node e2e/w768.mjs
import { createRequire } from "node:module";
const { chromium } = createRequire((process.env.PW_DIR || "/tmp/pw") + "/")("playwright");
const BASE = process.env.BASE || "http://127.0.0.1:8080", OUT = process.env.OUT;
const b = await chromium.launch();
const p = await (await b.newContext({ viewport: { width: 768, height: 1000 }, colorScheme: "light" })).newPage();
await p.goto(BASE + "/");
const post = (o) => p.evaluate(async (o) => (await fetch("/api/scenarios", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(o) })).json(), o);
const ids = [];
for (const [n, s, st] of [["E2E a", "FPT", "lump_sum"], ["E2E b", "HPG", "dca"], ["E2E c", "ACB", "lump_sum"]]) ids.push((await post({ name: n, symbol: s, style: st, amount_vnd: 20000000, buy_date: "2025-03-03", sell_date: "2026-10-16" })).id);
try {
  await p.goto(BASE + "/scenarios"); await p.waitForSelector(".sc-card"); await p.waitForTimeout(800);
  const m = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, cols: new Set([...document.querySelectorAll(".sc-card")].map((e) => Math.round(e.getBoundingClientRect().left))).size }));
  console.log("768", JSON.stringify(m));
  await p.screenshot({ path: OUT + "/cards-768-light.png" });
  await p.getByRole("button", { name: /^Bảng$/ }).click(); await p.waitForSelector("table"); await p.waitForTimeout(500);
  await p.screenshot({ path: OUT + "/table-768-light.png" });
} finally { for (const i of ids) await p.evaluate((i) => fetch("/api/scenarios/" + i, { method: "DELETE" }), i); await b.close(); }
