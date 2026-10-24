import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import i18n from "../../i18n";
import { ScenarioForm } from "./ScenarioForm";
import type { Scenario } from "./api";
import { defaultName } from "./defaultName";

const json = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status }));
let calls: { url: string; init?: RequestInit }[];
let postReply: () => Promise<Response>;

beforeEach(async () => {
  await i18n.changeLanguage("en");
  calls = [];
  postReply = () => json({ id: 1 }, 201);
  vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
    calls.push({ url, init });
    if (url.startsWith("/api/symbols?")) return json([{ symbol: "FPT", exchange: "HOSE", type: "stock", name_vi: "FPT", name_en: "FPT", delisted_at: null }]);
    if (url === "/api/symbols/FPT")
      return json({ symbol: "FPT", exchange: "HOSE", bars_1d: { first: "2006-12-13", last: "2026-10-17", as_of: "x" } });
    return postReply();
  }));
});
afterEach(() => vi.unstubAllGlobals());

function setup(scenario?: Scenario) {
  const onClose = vi.fn();
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={qc}><button>trigger</button><ScenarioForm scenario={scenario} onClose={onClose} /></QueryClientProvider>);
  return { onClose, user: userEvent.setup() };
}
const posts = () => calls.filter((c) => c.init?.method);

async function pickFpt(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByRole("combobox"), "fp");
  await user.click(await screen.findByRole("option", { name: "FPT · HOSE" }));
}

describe("defaultName", () => {
  it("joins symbol, vi-VN amount and dd/mm/yyyy start", () =>
    expect(defaultName("FPT", 10000000, "2025-10-12")).toBe("FPT · 10.000.000 ₫ · 12/10/2025"));
});

describe("ScenarioForm", () => {
  it("picks FPT, defaults start to last - 1 year, groups the amount and posts", async () => {
    const { user } = setup();
    await pickFpt(user);
    expect(calls.some((c) => c.url === "/api/symbols/FPT")).toBe(true);
    await waitFor(() => expect(screen.getByLabelText("Start")).toHaveValue("2025-10-17"));
    const amount = screen.getByLabelText("Amount (₫)");
    await user.clear(amount);
    await user.type(amount, "10000000");
    expect(amount).toHaveValue("10.000.000");
    await user.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(posts()[0].url).toBe("/api/scenarios");
    expect(JSON.parse(posts()[0].init!.body as string)).toEqual({
      name: "FPT · 10.000.000 ₫ · 17/10/2025", symbol: "FPT", style: "lump_sum",
      amount_vnd: 10000000, buy_date: "2025-10-17", sell_date: null,
    });
  });

  it.each([
    ["empty symbol", "", "Pick a symbol from the list."],
    ["amount 0", "0", "Amount must be a whole number above 0."],
    ["amount too large", "100000000001", "Amount must be at most 100.000.000.000 ₫."],
  ])("%s: message, no request", async (_n, amt, text) => {
    const { user } = setup();
    if (amt !== "") await pickFpt(user);
    const a = screen.getByLabelText("Amount (₫)");
    await user.clear(a);
    if (amt) await user.type(a, amt);
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect((await screen.findAllByRole("alert")).map((x) => x.textContent)).toContain(text);
    expect(posts()).toHaveLength(0);
  });

  it("end before start is refused in Vietnamese too", async () => {
    const { user } = setup();
    await pickFpt(user);
    await waitFor(() => expect(screen.getByLabelText("Start")).toHaveValue("2025-10-17"));
    await user.click(screen.getByLabelText("Today"));
    await user.type(screen.getByLabelText("End"), "2025-10-01");
    await i18n.changeLanguage("vi");
    await user.click(screen.getByRole("button", { name: "Lưu" }));
    expect(await screen.findByText("Ngày kết thúc không được trước ngày bắt đầu.")).toBeInTheDocument();
    expect(posts()).toHaveLength(0);
  });

  it("server 422 SYMBOL_UNKNOWN shows under the symbol", async () => {
    postReply = () => json({ error: { code: "SYMBOL_UNKNOWN", message: "x", details: { symbol: "FPT" } } }, 422);
    const { user, onClose } = setup();
    await pickFpt(user);
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText("Unknown symbol.")).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("server 422 NO_DATA shows the dated reason on the start date and keeps the input", async () => {
    postReply = () => json({ error: { code: "NO_DATA", message: "x", details: { first_available: "2025-01-02" } } }, 422);
    const { user, onClose } = setup();
    await pickFpt(user);
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText("No FPT data before 02/01/2025")).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByRole("combobox")).toHaveValue("FPT");
  });

  it("edit mode pre-fills, PUTs, shows Monthly for DCA", async () => {
    const s: Scenario = { id: 7, name: "Mine", symbol: "FPT", style: "dca", amount_vnd: 2000000, buy_date: "2025-01-15", sell_date: "2026-01-15", created_at: "", updated_at: "" };
    const { user } = setup(s);
    expect(screen.getByLabelText("Monthly (₫)")).toHaveValue("2.000.000");
    expect(screen.getByLabelText("Name")).toHaveValue("Mine");
    expect(screen.getByLabelText("End")).toHaveValue("2026-01-15");
    await user.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(posts()[0]?.url).toBe("/api/scenarios/7"));
    expect(posts()[0].init!.method).toBe("PUT");
  });

  it("Esc cancels and returns focus to the trigger", async () => {
    const trigger = document.createElement("button");
    document.body.append(trigger);
    trigger.focus();
    const { user, onClose } = setup();
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();
    expect(trigger).toHaveFocus();
    trigger.remove();
  });
});
