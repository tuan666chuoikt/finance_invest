import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import i18n from "../i18n";
import { isStale } from "./FreshnessChip";
import { TopBar } from "./TopBar";

const OK = { last_trading_date: "2026-10-16", as_of: "2026-10-16T15:42:00+07:00", source: "vci", symbols: 1612 };
const NONE = { last_trading_date: null, as_of: null, source: "vci", symbols: 0 };

function setup(status: object) {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(status), { status: 200 })));
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter>
        <TopBar />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(async () => {
  localStorage.clear();
  await i18n.changeLanguage("vi");
  // Fri 2026-10-16 18:00 HCM: the 16th is current, not stale.
  vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-16T11:00:00Z") });
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

test("chip shows date and source in both languages", async () => {
  setup(OK);
  const chip = await screen.findByTestId("freshness-chip", {}, { timeout: 3000 });
  await vi.waitFor(() => expect(chip).toHaveTextContent("16/10/2026 15:42"));
  expect(chip).toHaveTextContent("Dữ liệu đến");
  expect(chip).toHaveTextContent("VCI");
  expect(chip).toHaveAttribute("data-stale", "false");
  await userEvent.setup({ advanceTimers: () => {} }).click(screen.getByRole("button", { name: "EN" }));
  expect(chip).toHaveTextContent("Data as of 16/10/2026 15:42");
  expect(chip).toHaveTextContent("VCI");
});

test("null status shows No data yet", async () => {
  await i18n.changeLanguage("en");
  setup(NONE);
  expect(await screen.findByText("No data yet")).toBeInTheDocument();
});

test("older than previous weekday is stale with warning", async () => {
  vi.setSystemTime(new Date("2026-10-20T05:00:00Z")); // Tue; previous weekday is Mon the 19th
  setup(OK);
  await vi.waitFor(() => expect(screen.getByTestId("freshness-chip")).toHaveAttribute("data-stale", "true"));
  expect(screen.getByTestId("freshness-chip")).toHaveTextContent("⚠");
});

test("isStale weekday rule", () => {
  const d = (s: string) => new Date(`${s}T05:00:00Z`);
  expect(isStale("2026-10-16", d("2026-10-19"))).toBe(false); // Mon, last = Fri
  expect(isStale("2026-10-16", d("2026-10-17"))).toBe(false); // Sat
  expect(isStale("2026-10-15", d("2026-10-19"))).toBe(true);
  expect(isStale("2026-10-19", d("2026-10-20"))).toBe(false); // Tue, last = Mon
  expect(isStale("2026-10-16", d("2026-10-20"))).toBe(true);
});

test("language switch: click, nav labels, storage, Alt+L, Alt+L in input", async () => {
  setup(OK);
  const user = userEvent.setup({ advanceTimers: () => {} });
  const en = screen.getByRole("button", { name: "EN" });
  await user.click(en);
  expect(en).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("link", { name: "Data quality" })).toBeInTheDocument();
  expect(localStorage.getItem("finvest.lang")).toBe("en");
  await user.keyboard("{Alt>}l{/Alt}");
  expect(screen.getByRole("button", { name: "VI" })).toHaveAttribute("aria-pressed", "true");
  const input = document.body.appendChild(document.createElement("input"));
  input.focus();
  await user.keyboard("{Alt>}l{/Alt}");
  expect(screen.getByRole("button", { name: "VI" })).toHaveAttribute("aria-pressed", "true");
});

test("menu button toggles aria-expanded", async () => {
  setup(OK);
  const btn = screen.getByText("Menu");
  expect(btn).toHaveAttribute("aria-expanded", "false");
  await userEvent.setup({ advanceTimers: () => {} }).click(btn);
  expect(btn).toHaveAttribute("aria-expanded", "true");
});
