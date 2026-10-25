import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import i18n from "../i18n";
import { Layout } from "../app/routes";
import { MemoryRouter } from "react-router-dom";

const J = (o: object) => ({ id: 7, kind: "crawl", created_at: "2026-10-26T16:10:03+07:00", finished_at: null, progress: null, summary: null, error: null, status: "running", ...o });
const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status });
let current: () => Response;
let post: () => Response;
let fetchMock: ReturnType<typeof vi.fn>;
const calls = (m: string, part: string) => fetchMock.mock.calls.filter(([u, i]) => u.includes(part) && (i?.method ?? "GET") === m).length;

function setup() {
  fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith("/jobs/current")) return current();
    if (url.endsWith("/jobs") && init?.method === "POST") return post();
    return json({ last_trading_date: null, as_of: null, source: "vci", symbols: 0 });
  });
  vi.stubGlobal("fetch", fetchMock);
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter>
        <Layout />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
const flush = () => act(async () => { await vi.advanceTimersByTimeAsync(0); });
const btn = () => screen.getByRole("button", { name: /Cào dữ liệu|Đang cào|Crawl data|Crawling/ });
const status = () => screen.getByRole("status");

beforeEach(async () => {
  await i18n.changeLanguage("vi");
  vi.useFakeTimers({ shouldAdvanceTime: true });
  current = () => json({ error: { code: "NOT_FOUND", message: "x" } }, 404);
  post = () => json(J({}), 202);
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

test("idle without job, click starts, polls every 2 s, progress then done", async () => {
  setup();
  await flush();
  expect(screen.queryByRole("status")).toBeNull();
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  await user.click(btn());
  expect(calls("POST", "/jobs")).toBe(1);
  expect(btn()).toBeDisabled();
  expect(btn()).toHaveAttribute("aria-busy", "true");
  const before = calls("GET", "/jobs/current");
  current = () => json(J({ progress: { step: 1, steps: 2, done: 12, total: 30, trading_date: "2026-10-26" } }));
  await act(async () => { await vi.advanceTimersByTimeAsync(4000); });
  expect(calls("GET", "/jobs/current") - before).toBe(2);
  expect(status()).toHaveTextContent(/1\/2.*12\/30/);
  const bars = calls("GET", "/bars/1d/status");
  current = () =>
    json(J({ status: "done", finished_at: "2026-10-26T16:14:00+07:00", summary: {
      ticks: { symbols_fetched: 30, rows: 812344, symbols_skipped: 2, partial_until: null }, bars_1d: { sessions_added: 6, symbols_skipped: 0 },
      no_session_today: false, duration_s: 221 } }));
  await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
  for (const s of ["30 mã", "812.344", "+6 phiên", "2 mã bỏ qua", "3 phút 41 giây"]) expect(status()).toHaveTextContent(s);
  expect(btn()).toBeEnabled();
  expect(calls("GET", "/bars/1d/status")).toBeGreaterThan(bars);
  const n = calls("GET", "/jobs/current");
  await act(async () => { await vi.advanceTimersByTimeAsync(6000); });
  expect(calls("GET", "/jobs/current")).toBe(n); // polling stopped
  await user.click(screen.getByRole("button", { name: "Đóng" }));
  expect(screen.queryByRole("status")).toBeNull();
});

test("failed shows code and path, button enabled", async () => {
  current = () => json(J({ status: "failed", error: { code: "PermissionError", message: "không ghi được", path: "data/raw/ticks/2026-10-26" } }));
  setup();
  await flush();
  expect(status()).toHaveTextContent("PermissionError");
  expect(status()).toHaveTextContent("data/raw/ticks/2026-10-26");
  expect(status().textContent?.match(/✕/g)).toHaveLength(1);
  expect(btn()).toBeEnabled();
});

test("409 shows refused text and posts once", async () => {
  post = () => json({ error: { code: "JOB_RUNNING", message: "m", details: { id: 7, started_at: "2026-10-26T16:10:03+07:00" } } }, 409);
  setup();
  await flush();
  await userEvent.setup({ advanceTimers: vi.advanceTimersByTime }).click(btn());
  await flush();
  expect(status()).toHaveTextContent("bắt đầu 16:10");
  expect(calls("POST", "/jobs")).toBe(1);
});

test("mounting with a running job resumes Running; names exist in EN", async () => {
  current = () => json(J({ progress: { step: 2, steps: 2, done: 3, total: 6, trading_date: "2026-10-26" } }));
  setup();
  await flush();
  expect(btn()).toBeDisabled();
  expect(status()).toHaveTextContent("Bước 2/2");
  await act(() => i18n.changeLanguage("en"));
  expect(screen.getByRole("button", { name: "Crawling…" })).toBeDisabled();
  expect(status()).toHaveTextContent("Step 2/2");
});

test("start failure shows its cause (500) or unreachable, in EN", async () => {
  await i18n.changeLanguage("en");
  post = () => json({ error: { code: "INTERNAL", message: "boom" } }, 500);
  setup();
  await flush();
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  await user.click(btn());
  await flush();
  expect(status()).toHaveTextContent("Could not start: boom");
  expect(btn()).toBeEnabled();
  post = () => { throw new TypeError("down"); };
  await user.click(btn());
  await flush();
  expect(status()).toHaveTextContent("Could not start: cannot reach the server");
  post = () => json(J({}), 202);
  await user.click(btn());
  await flush();
  expect(status()).not.toHaveTextContent("Could not start");
});

test("two clicks in the same tick send one POST", async () => {
  setup();
  await flush();
  act(() => { fireEvent.click(btn()); fireEvent.click(btn()); });
  await flush();
  expect(calls("POST", "/jobs")).toBe(1);
});
