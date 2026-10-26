import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import i18n from "../../i18n";
import raw from "./fixtures/envelope-001.json";
import type { Scenario } from "./api";
import { defaultName } from "./defaultName";
import { ScenarioCard } from "./ScenarioCard";
import type { WhatIfEnvelope } from "./result";

export const env001 = raw as WhatIfEnvelope;
const lump: Scenario = {
  id: 1, name: "FPT test", symbol: "FPT", style: "lump_sum", amount_vnd: 10_000_000, buy_date: "2026-10-12", sell_date: null,
  created_at: "2026-10-19T09:00:00+07:00", updated_at: "2026-10-19T09:00:00+07:00",
};

function show(env: WhatIfEnvelope, s: Scenario = lump) {
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify(env), { status: 200 }))));
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={qc}><ScenarioCard scenario={s} onEdit={() => {}} /></QueryClientProvider>);
  return screen.findByTestId("scenario-card");
}
const withResult = (patch: object): WhatIfEnvelope => ({ ...env001, result: { ...env001.result, ...patch } });
afterEach(() => vi.unstubAllGlobals());

describe("ScenarioCard", () => {
  it.each(["FPT 50tr 2025", "FPT DCA thử"])("shows the stored name as a heading: %s", async (name) => {
    await show(env001, { ...lump, name });
    expect(screen.getByRole("heading", { name, level: 2 })).toBeInTheDocument();
  });

  it("falls back to the default name when unnamed", async () => {
    await show(env001, { ...lump, name: "" });
    expect(screen.getByRole("heading", { name: defaultName("FPT", 10_000_000, "2026-10-12") })).toBeInTheDocument();
  });

  it("shows the money lines with sign, arrow and the approximate flag", async () => {
    const card = within(await show(env001));
    for (const s of ["10.000.000 ₫", "10.610.975 ₫", "▲ +610.975 ₫", "▲ +6,11 %", "635.975 ₫"])
      expect(card.getByText(s)).toBeInTheDocument();
    expect(card.getByText(/Mua một lần/)).toBeInTheDocument();
    expect(card.getByTestId("approximate-flag")).toHaveTextContent("Gần đúng");
    expect(card.getByTestId("approximate-flag")).toHaveClass("chip-warn");
    expect(card.getByText("Giá trị nếu bán").nextElementSibling).toHaveClass("headline");
  });

  it("has no approximate flag when approximate is false", async () => {
    await show({ ...env001, approximate: false, flags: [] });
    expect(screen.queryByTestId("approximate-flag")).toBeNull();
  });

  it("benchmark with first_available null renders n/a without throwing", async () => {
    const bm = [{ name: "VN-Index", investable: false, available: false, first_available: null }];
    const card = await show(withResult({ benchmarks: bm }));
    expect(within(card).getByTestId("bench")).toHaveTextContent(/^VN-Index — n\/a$/);
  });

  it("benchmarks: available shows pct and pp; unavailable shows n/a + date, never 0 %", async () => {
    const b = structuredClone(env001.result.benchmarks);
    if (!b[0].available) throw new Error("fixture");
    b[0].pl_pct.value = "5.0000";
    b[0].diff_pp.value = "1.1100";
    if (b[1].available) throw new Error("fixture");
    b[1].first_available = "2026-10-13"; // after dates.buy => dated wording
    const card = within(await show(withResult({ benchmarks: b })));
    const [vn, e1] = card.getAllByTestId("bench");
    expect(vn).toHaveTextContent("▲ +5,00 %");
    expect(vn).toHaveTextContent("(+1,11 điểm %)");
    expect(within(vn).getByText("VN-Index")).toHaveAttribute("title", "không đầu tư được");
    expect(e1).toHaveTextContent("n/a");
    expect(e1).toHaveTextContent("13/10/2026");
    expect(e1).not.toHaveTextContent("0 %");
  });

  it("benchmark listed on/before buy but unavailable says data missing in period, no date", async () => {
    const b = structuredClone(env001.result.benchmarks);
    const card = within(await show(withResult({ benchmarks: b })));
    const e1 = card.getAllByTestId("bench")[1];
    expect(e1).toHaveTextContent(/E1VFVN30 — n\/a: thiếu dữ liệu trong kỳ/);
    expect(e1.textContent).not.toMatch(/\d{2}\/\d{2}\/\d{4}/);
  });

  it("no benchmark lines when the list is empty", async () => {
    await show(withResult({ benchmarks: [] }));
    expect(screen.queryByTestId("bench")).toBeNull();
  });

  it("shift notice, DCA header, missing sessions and negative P/L", async () => {
    const r = structuredClone(env001.result);
    r.returns.pl_vnd.value = "-1000";
    r.returns.pl_pct.value = "-0.0100";
    const dca: Scenario = { ...lump, style: "dca", amount_vnd: 2_000_000, buy_date: "2026-01-15" };
    const card = within(await show({
      ...env001,
      result: {
        ...r,
        dates: { ...r.dates, shifts: [{ field: "buy_date", from: "2026-10-17", to: "2026-10-19", reason: "non_trading" }] },
        missing_sessions: ["2026-03-04", "2026-03-05", "2026-03-06"],
      },
    }, dca));
    expect(card.getByText(/Ngày mua dời sang ngày giao dịch kế tiếp: 1 lần/)).toBeInTheDocument();
    expect(card.getByText(/Mỗi tháng 2\.000\.000 ₫ \(ngày 15\)/)).toBeInTheDocument();
    expect(card.getByText("▼ −1.000 ₫")).toBeInTheDocument();
    expect(card.getByText(/thiếu 3 phiên/)).toBeInTheDocument();
    expect(card.getByText("04/03/2026, 05/03/2026, 06/03/2026")).toBeInTheDocument();
  });

  it("DCA with 5 shifts renders one shift line and the dates inside details", async () => {
    const shifts = ["02", "03", "04", "05", "06"].map((m) => ({ field: "buy_date" as const, from: `2026-${m}-15`, to: `2026-${m}-16`, reason: "non_trading" as const }));
    const dca: Scenario = { ...lump, style: "dca", amount_vnd: 2_000_000, buy_date: "2026-01-15" };
    const card = within(await show({ ...env001, result: { ...structuredClone(env001.result), dates: { ...env001.result.dates, shifts } } }, dca));
    const line = card.getByTestId("dca-shifts");
    expect(line).toHaveTextContent("Ngày mua dời sang ngày giao dịch kế tiếp: 5 lần");
    expect(card.getAllByText(/Ngày mua dời sang/)).toHaveLength(1);
    expect(line.querySelector("details")).toContainElement(card.getByText("Xem"));
    expect(line.querySelectorAll("details li")).toHaveLength(5);
  });

  it("failing computation shows the reason and Edit only on that card", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ error: { code: "NO_DATA", message: "x" } }), { status: 422 }))));
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={qc}><ScenarioCard scenario={lump} onEdit={() => {}} /></QueryClientProvider>);
    expect(await screen.findByText("Không tính được: Không có dữ liệu cho yêu cầu này.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sửa" })).toBeInTheDocument();
  });

  it("NO_DATA with first_available names the symbol and date", async () => {
    const body = { error: { code: "NO_DATA", message: "x", details: { first_available: "2025-01-02" } } };
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify(body), { status: 422 }))));
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={qc}><ScenarioCard scenario={lump} onEdit={() => {}} /></QueryClientProvider>);
    expect(await screen.findByText("Không tính được: Không có dữ liệu FPT trước 02/01/2025")).toBeInTheDocument();
  });

  it.each([[1, "1 session missing"], [2, "2 sessions missing"]])("EN plural: %i", async (n, text) => {
    await i18n.changeLanguage("en");
    await show(withResult({ missing_sessions: ["2026-03-04", "2026-03-05"].slice(0, n) }));
    expect(screen.getByText(new RegExp(text))).toBeInTheDocument();
    await i18n.changeLanguage("vi");
  });

  it("negative P/L never renders an ASCII hyphen before a digit", async () => {
    const card = await show(withResult({ returns: { ...env001.result.returns, pl_vnd: { ...env001.result.returns.pl_vnd, value: "-19847507" }, pl_pct: { ...env001.result.returns.pl_pct, value: "-1.5" } } }));
    expect(card.textContent).toContain("−19.847.507 ₫");
    expect(card.textContent).not.toMatch(/-\d/);
  });

  it("skeleton is a named status region without aria-label", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    const qc = new QueryClient();
    render(<QueryClientProvider client={qc}><ScenarioCard scenario={lump} onEdit={() => {}} /></QueryClientProvider>);
    const sk = screen.getByRole("status");
    expect(sk).toHaveAttribute("aria-busy", "true");
    expect(sk).not.toHaveAttribute("aria-label");
    expect(sk).toHaveTextContent("Đang tải…");
  });
});
