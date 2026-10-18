import type { ReactElement } from "react";
import { Navigate, Outlet, createBrowserRouter, useLocation } from "react-router-dom";
import { Disclaimer } from "../components/Disclaimer";
import { TopBar } from "../components/TopBar";
import { Placeholder } from "./Placeholder";

export interface AppRoute {
  path: string;
  element: ReactElement;
  nameKey: string;
  analysis: boolean; // analysis routes carry the disclaimer banner (FE-disclaimer)
}

export const ROUTES: AppRoute[] = [
  { path: "/scenarios", element: <Placeholder name="scenarios" />, nameKey: "nav.scenarios", analysis: true },
  { path: "/data-quality", element: <Placeholder name="data-quality" />, nameKey: "nav.data-quality", analysis: false },
  { path: "/rules", element: <Placeholder name="rules" />, nameKey: "nav.rules", analysis: false },
];

function Layout() {
  const { pathname } = useLocation();
  return (
    <>
      <TopBar />
      {ROUTES.find((r) => r.path === pathname)?.analysis && <Disclaimer />}
      <main>
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
