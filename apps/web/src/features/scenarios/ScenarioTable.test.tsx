import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import "../../i18n";
import i18n from "../../i18n";
import env001 from "./fixtures/envelope-001.json";
import type { Scenario } from "./api";
import type { WhatIfEnvelope } from "./result";
import { ScenarioTable, type Row } from "./ScenarioTable";
import { ViewToggle, useView } from "./ViewToggle";

const sc = (id: number, symbol: string): Scenario => ({
  id, name: `${symbol} test`, symbol, style: "lump_sum", amount_vnd: 10_000_000, buy_date: "2026-10-12", sell_date: null,
  created_at: "2026-10-19T09:00:00+07:00", updated_at: "2026-10-19T09:00:00+07:00",
});
const a = env001 as unknown as WhatIfEnvelope;
const b = structuredClone(a);
b.result.returns.pl_pct.value = "-2.8338";
b.result.position.invested_vnd.value = "5000000";
b.approximate = false;

const rows = (): Row[] => [
  { scenario: sc(3, "BAD"), error: "No data" },
  { scenario: sc(2, "XYZ"), env: b },
  { scenario: sc(1, "FPT"), env: a },
];
const order = () => screen.getAllByRole("row").slice(1).map((r) => within(r).getAllByRole("rowheader")[0].textContent);

beforeEach(() => { void i18n.changeLanguage("en"); localStorage.clear(); });

describe("ScenarioTable", () => {
  it("benchmark cell is n/a when first_available is null", () => {
    const c = structuredClone(a);
    c.result.benchmarks = [{ name: "VN-Index", investable: false, available: false, first_available: null }];
    render(<ScenarioTable rows={[{ scenario: sc(1, "FPT"), env: c }]} />);
    expect(within(screen.getAllByRole("row")[1]).getAllByText("n/a").length).toBeGreaterThanOrEqual(2);
  });

  it("defaults to P/L % desc with failed rows last", () => {
    render(<ScenarioTable rows={rows()} />);
    expect(order()).toEqual(["FPT test", "XYZ test", "BAD test"]);
    const cells = screen.getAllByRole("row").slice(1, 3).map((r) => r.textContent);
    expect(cells[0]).toContain("6,11 %");
    expect(cells[1]).toContain("−2,83 %");
    expect(screen.getByRole("alert")).toHaveTextContent("Cannot compute");
  });

  it("sorts a numeric column desc then asc, failed stays last", async () => {
    render(<ScenarioTable rows={rows()} />);
    const h = screen.getByRole("columnheader", { name: /Invested/ });
    await userEvent.click(within(h).getByRole("button"));
    expect(h).toHaveAttribute("aria-sort", "descending");
    expect(order()).toEqual(["FPT test", "XYZ test", "BAD test"]);
    await userEvent.click(within(h).getByRole("button"));
    expect(h).toHaveAttribute("aria-sort", "ascending");
    expect(order()).toEqual(["XYZ test", "FPT test", "BAD test"]);
  });

  it("fills the flag column for approximate rows and shows the footer in both languages", async () => {
    render(<ScenarioTable rows={rows()} />);
    expect(screen.getAllByText(/⚠/)).toHaveLength(1);
    expect(screen.getByText("Past ranking does not predict the future.")).toBeInTheDocument();
    await i18n.changeLanguage("vi");
    expect(await screen.findByText(/không dự báo tương lai/)).toBeInTheDocument();
  });
});

describe("ViewToggle", () => {
  const Harness = () => { const [v, set] = useView(); return <ViewToggle view={v} onChange={set} />; };
  it("persists the choice across remount", async () => {
    const { unmount } = render(<Harness />);
    await userEvent.click(screen.getByRole("button", { name: "Table" }));
    unmount();
    render(<Harness />);
    expect(screen.getByRole("button", { name: "Table" })).toHaveAttribute("aria-pressed", "true");
    expect(localStorage.getItem("finvest.scenarios.view")).toBe("table");
  });
});
