import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import "../../i18n";
import raw from "./fixtures/envelope-001.json";
import type { Scenario } from "./api";
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
  it("shows the money lines with sign, arrow and the approximate flag", async () => {
    const card = within(await show(env001));
    for (const s of ["10.000.000 ₫", "10.610.975 ₫", "▲ +610.975 ₫", "▲ +6,11 %", "635.975 ₫"])
      expect(card.getByText(s)).toBeInTheDocument();
    expect(card.getByText(/Mua một lần/)).toBeInTheDocument();
    expect(card.getByTestId("approximate-flag")).toHaveTextContent("Gần đúng");
  });

  it("has no approximate flag when approximate is false", async () => {
    await show({ ...env001, approximate: false, flags: [] });
    expect(screen.queryByTestId("approximate-flag")).toBeNull();
  });

  it("benchmarks: available shows pct and pp; unavailable shows n/a + date, never 0 %", async () => {
    const b = structuredClone(env001.result.benchmarks);
    if (!b[0].available) throw new Error("fixture");
    b[0].pl_pct.value = "5.0000";
    b[0].diff_pp.value = "1.1100";
    const card = within(await show(withResult({ benchmarks: b })));
    const [vn, e1] = card.getAllByTestId("bench");
    expect(vn).toHaveTextContent("▲ +5,00 %");
    expect(vn).toHaveTextContent("(+1,11 điểm %)");
    expect(within(vn).getByText("VN-Index")).toHaveAttribute("title", "không đầu tư được");
    expect(e1).toHaveTextContent("n/a");
    expect(e1).toHaveTextContent("06/10/2014");
    expect(e1).not.toHaveTextContent("0 %");
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
    expect(card.getByText("Ngày mua dời sang 19/10/2026")).toBeInTheDocument();
    expect(card.getByText(/Mỗi tháng 2\.000\.000 ₫ \(ngày 15\)/)).toBeInTheDocument();
    expect(card.getByText("▼ −1.000 ₫")).toBeInTheDocument();
    expect(card.getByText(/thiếu 3 phiên/)).toBeInTheDocument();
    expect(card.getByText("04/03/2026, 05/03/2026, 06/03/2026")).toBeInTheDocument();
  });

  it("failing computation shows the reason and Edit only on that card", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ error: { code: "NO_DATA", message: "x" } }), { status: 422 }))));
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={qc}><ScenarioCard scenario={lump} onEdit={() => {}} /></QueryClientProvider>);
    expect(await screen.findByText("Không tính được: Không có dữ liệu cho yêu cầu này.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sửa" })).toBeInTheDocument();
  });
});
