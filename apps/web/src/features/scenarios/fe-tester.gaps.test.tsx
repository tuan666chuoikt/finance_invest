// FE tester (sprint-03): gaps found against the real stack. `it.fails` = a known bug (U#): the test flips red when it is fixed,
// then drop `.fails`. Report: .finvest/sprints/sprint-03/4-test.fe.md
import { Component, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import i18n from "../../i18n";
import { routeObjects } from "../../app/routes";
import raw from "./fixtures/envelope-001.json";
import type { Scenario } from "./api";
import { ScenarioCard } from "./ScenarioCard";
import type { WhatIfEnvelope } from "./result";

class Boundary extends Component<{ children: ReactNode }, { bad: boolean }> {
  state = { bad: false };
  static getDerivedStateFromError() { return { bad: true }; }
  render() { return this.state.bad ? <p>boundary</p> : this.props.children; }
}
const env = raw as WhatIfEnvelope;
const sc: Scenario = {
  id: 1, name: "Quỹ hưu trí", symbol: "FPT", style: "lump_sum", amount_vnd: 10_000_000, buy_date: "2026-10-12", sell_date: null,
  created_at: "2026-10-19T09:00:00+07:00", updated_at: "2026-10-19T09:00:00+07:00",
};
const qc = () => new QueryClient({ defaultOptions: { queries: { retry: false } } });
function show(e: unknown, s: Scenario = sc) {
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify(e), { status: 200 }))));
  render(<QueryClientProvider client={qc()}><ScenarioCard scenario={s} onEdit={() => {}} /></QueryClientProvider>);
  return screen.findByTestId("scenario-card");
}
const patch = (p: object, flags?: string[]) => ({ ...env, flags: flags ?? env.flags, result: { ...env.result, ...p } });
afterEach(() => { vi.unstubAllGlobals(); void i18n.changeLanguage("vi"); });

describe("real-stack shapes", () => {
  it("U1: VN-Index unavailable with first_available=null (real API while VNINDEX is empty) does not throw", async () => {
    const b = [{ name: "VN-Index", investable: false, available: false, first_available: null }];
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify(patch({ benchmarks: b })), { status: 200 }))));
    render(<QueryClientProvider client={qc()}><Boundary><ScenarioCard scenario={sc} onEdit={() => {}} /></Boundary></QueryClientProvider>);
    // currently formatDate(null) throws and, in the app, the router error boundary blanks the whole page
    const card = within(await screen.findByTestId("scenario-card"));
    expect(card.getByTestId("bench")).toHaveTextContent("n/a");
  });

  it("below_one_lot flag: lump and DCA notes", async () => {
    let c = within(await show(patch({}, ["approximate", "below_one_lot"])));
    expect(c.getByText(/Ít hơn 1 lô — không mua được/)).toBeInTheDocument();
    vi.unstubAllGlobals(); document.body.innerHTML = "";
    c = within(await show(patch({}, ["approximate", "below_one_lot"]), { ...sc, style: "dca" }));
    expect(c.getByText(/sẽ tích luỹ đến khi đủ 1 lô/)).toBeInTheDocument();
  });

  it("U3: the user-given scenario name is visible on the card (UX: card shows name)", async () => {
    const card = await show(env);
    expect(card).toHaveTextContent("Quỹ hưu trí");
  });

  it("U5: English plural for one missing session reads '1 session missing'", async () => {
    await i18n.changeLanguage("en");
    const r = { ...env.result, missing_sessions: ["2026-01-02"] };
    await show({ ...env, result: r });
    expect(screen.queryByText(/1 sessions missing/)).toBeNull();
    expect(screen.getByText(/1 session missing/)).toBeTruthy();
  });
});

describe("a11y structure", () => {
  it("U2: the disclaimer sits inside a landmark (axe 'region' rule)", async () => {
    vi.stubGlobal("fetch", () => Promise.resolve(new Response("{}", { status: 500 })));
    render(<QueryClientProvider client={qc()}><RouterProvider router={createMemoryRouter(routeObjects, { initialEntries: ["/scenarios"] })} /></QueryClientProvider>);
    const d = await screen.findByTestId("disclaimer");
    expect(d.closest('main,[role="main"],header,[role="banner"],nav,[role="region"][aria-label],section[aria-label],aside[aria-label]')).not.toBeNull();
  });
});
