import type { ReactElement } from "react";
import { Navigate, Outlet, createBrowserRouter, useLocation } from "react-router-dom";
import { CrawlStatus } from "../components/CrawlStatus";
import { Disclaimer } from "../components/Disclaimer";
import { TopBar } from "../components/TopBar";
import { ScenariosPage } from "../features/scenarios/ScenariosPage";
import { Placeholder } from "./Placeholder";
import { useCrawlJob } from "./useCrawlJob";

export interface AppRoute {
  path: string;
  element: ReactElement;
  nameKey: string;
  analysis: boolean; // analysis routes carry the disclaimer banner (FE-disclaimer)
}

export const ROUTES: AppRoute[] = [
  { path: "/scenarios", element: <ScenariosPage />, nameKey: "nav.scenarios", analysis: true },
  { path: "/data-quality", element: <Placeholder name="data-quality" />, nameKey: "nav.data-quality", analysis: false },
  { path: "/rules", element: <Placeholder name="rules" />, nameKey: "nav.rules", analysis: false },
];

// Crawl state is lifted here so the status line can sit inside <main> while the button stays in the header.
export function Layout() {
  const crawl = useCrawlJob();
  const analysis = ROUTES.find((r) => r.path === useLocation().pathname)?.analysis;
  return (
    <>
      <TopBar crawl={crawl} />
      <main className="page">
        {analysis && <Disclaimer />}
        <CrawlStatus job={crawl.job} refused={crawl.refused} startError={crawl.startError} />
        <Outlet />
      </main>
    </>
  );
}

export const routeObjects = [
  {
    element: <Layout />,
    children: [
      { path: "/", element: <Navigate to="/scenarios" replace /> },
      ...ROUTES.map(({ path, element }) => ({ path, element })),
    ],
  },
];

export const router = createBrowserRouter(routeObjects);
