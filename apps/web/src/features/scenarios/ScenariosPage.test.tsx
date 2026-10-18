import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import "../../i18n";
import env001 from "./fixtures/envelope-001.json";
import type { Scenario } from "./api";
import { ScenariosPage } from "./ScenariosPage";

const sc = (id: number, symbol: string): Scenario => ({
  id, name: `${symbol} test`, symbol, style: "lump_sum", amount_vnd: 10_000_000, buy_date: "2026-10-12", sell_date: null,
  created_at: "2026-10-19T09:00:00+07:00", updated_at: "2026-10-19T09:00:00+07:00",
});
const json = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status }));
const BARS = { last_trading_date: "2026-10-15", as_of: "2026-10-15T16:45:00+07:00", source: "vci", symbols: 1612 };

let scenarios: Scenario[];
let bars: unknown;
let down: boolean;
let deleted: string[];

beforeEach(() => {
  scenarios = [sc(2, "XYZ"), sc(1, "FPT")];
  bars = BARS;
  down = false;
  deleted = [];
  vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
    if (down) return Promise.reject(new TypeError("offline"));
    if (url === "/api/bars/1d/status") return json(bars);
    if (url === "/api/scenarios") return json(scenarios);
    if (url.startsWith("/api/scenarios/") && init?.method === "DELETE") {
      deleted.push(url);
      scenarios = scenarios.filter((s) => `/api/scenarios/${s.id}` !== url);
      return Promise.resolve(new Response(null, { status: 204 }));
    }
    if (url === "/api/whatif") {
      return JSON.parse(init!.body as string).symbol === "FPT"
        ? json(env001)
        : json({ error: { code: "NO_DATA", message: "no bars" } }, 422);
    }
    return json({});
  }));
});
afterEach(() => vi.unstubAllGlobals());

function page() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={qc}><ScenariosPage /></QueryClientProvider>);
  return userEvent.setup();
}

// Cards load independently: wait until no skeleton is left.
const loaded = async () => {
  await waitFor(() => expect(screen.queryAllByTestId("card-skeleton")).toHaveLength(0));
  return screen.getAllByTestId("scenario-card");
};

describe("ScenariosPage", () => {
  it("renders both cards: one failure never blanks the grid", async () => {
    page();
    await screen.findAllByTestId("scenario-card");
    const cards = await loaded();
    expect(cards).toHaveLength(2);
    expect(within(cards[0]).getByText(/Không tính được: Không có dữ liệu/)).toBeInTheDocument();
    expect(within(cards[0]).getByRole("button", { name: "Sửa" })).toBeInTheDocument();
    for (const s of ["10.000.000 ₫", "10.610.975 ₫", "▲ +610.975 ₫", "▲ +6,11 %", "635.975 ₫"])
      expect(within(cards[1]).getByText(s)).toBeInTheDocument();
    expect(cards.filter((c) => within(c).queryByTestId("approximate-flag"))).toHaveLength(1);
    expect(screen.getByText("Dữ liệu đến 15/10/2026 · nguồn VCI")).toBeInTheDocument();
  });

  it("shows skeletons while loading", () => {
    page();
    expect(screen.getAllByTestId("card-skeleton")).toHaveLength(3);
  });

  it("empty state with the example line; Add opens the form", async () => {
    scenarios = [];
    const user = page();
    expect(await screen.findByText("Chưa có kịch bản nào.")).toBeInTheDocument();
    expect(screen.getByText(/VD: FPT/)).toBeInTheDocument();
    await user.click(screen.getAllByRole("button", { name: "+ Thêm kịch bản" })[1]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("no bars yet: back-fill command shown, Add disabled, N does nothing", async () => {
    bars = { last_trading_date: null, as_of: null, source: "vci", symbols: 0 };
    const user = page();
    expect(await screen.findByText("make backfill")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "+ Thêm kịch bản" })).toBeDisabled();
    await user.keyboard("n");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("API down: error state with retry", async () => {
    down = true;
    page();
    expect(await screen.findByText(/Không kết nối được máy chủ/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Thử lại" })).toBeInTheDocument();
  });

  it("N opens the form outside fields", async () => {
    const user = page();
    await loaded();
    await user.keyboard("n");
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  it("menu: Esc closes it; Delete asks to confirm, then the card disappears", async () => {
    const user = page();
    await screen.findAllByTestId("scenario-card");
    const cards = await loaded();
    const menu = within(cards[1]).getByRole("button", { name: /Tuỳ chọn/ });
    await user.click(menu);
    expect(screen.getByRole("menu")).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("menu")).toBeNull();
    expect(menu).toHaveFocus();

    await user.click(menu);
    await waitFor(() => expect(screen.getByRole("menuitem", { name: "Sửa" })).toHaveFocus());
    await user.keyboard("{ArrowDown}");
    expect(screen.getByRole("menuitem", { name: "Xoá" })).toHaveFocus();
    await user.keyboard("{Enter}");
    const dlg = screen.getByRole("dialog");
    expect(within(dlg).getByText("Xoá kịch bản FPT test?")).toBeInTheDocument();
    await user.click(within(dlg).getByRole("button", { name: "Xoá" }));
    await waitFor(() => expect(screen.getAllByTestId("scenario-card")).toHaveLength(1));
    expect(deleted).toEqual(["/api/scenarios/1"]);
  });
});
