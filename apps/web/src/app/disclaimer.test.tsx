import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import i18n from "../i18n";
import { ROUTES, routeObjects } from "./routes";

const VI = "Mô phỏng để học, không phải lời khuyên đầu tư";
const EN = "Educational simulation, not investment advice";

// Layout -> TopBar -> FreshnessChip fetches bars status; stub it so no network is needed.
vi.stubGlobal("fetch", () => Promise.resolve(new Response("{}", { status: 500 })));

function at(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <RouterProvider router={createMemoryRouter(routeObjects, { initialEntries: [path] })} />
    </QueryClientProvider>,
  );
}

describe("disclaimer on analysis routes (F-032)", () => {
  it("/scenarios is an analysis route", () => {
    expect(ROUTES.find((r) => r.path === "/scenarios")?.analysis).toBe(true);
  });

  it.each(ROUTES)("banner present iff analysis: $path", async ({ path, analysis }) => {
    at(path);
    if (analysis) expect(await screen.findByTestId("disclaimer")).toBeInTheDocument();
    else {
      await screen.findByRole("main");
      expect(screen.queryByTestId("disclaimer")).toBeNull();
    }
  });

  it.each(["vi", "en"])("both lines verbatim, nothing focusable, in %s", async (lng) => {
    await i18n.changeLanguage(lng);
    at("/scenarios");
    const banner = await screen.findByTestId("disclaimer");
    expect(banner).toHaveTextContent(VI);
    expect(banner).toHaveTextContent(EN);
    expect(banner.querySelector("a,button,input,select,textarea,[tabindex]")).toBeNull();
  });

  it.each(ROUTES.filter((r) => r.analysis))("exactly one role=note, inside main, reads with spaces around the dot: $path", async ({ path }) => {
    await i18n.changeLanguage("vi");
    at(path);
    const banner = await screen.findByTestId("disclaimer");
    expect(screen.getAllByRole("note")).toHaveLength(1);
    expect(banner.closest("main")).not.toBeNull();
    expect(banner.textContent?.startsWith("ⓘ ")).toBe(true);
    expect(banner.textContent).toContain("đầu tư · Educational");
  });
});
