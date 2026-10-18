import { useQueries } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "../../api/client";
import { ApiErrorState } from "../../components/ApiErrorState";
import { useBarsStatus } from "../../app/useBarsStatus";
import { formatDate } from "../../lib/format";
import { useScenarios, whatIfQuery, type Scenario } from "./api";
import { GRID_CSS, ScenarioCard } from "./ScenarioCard";
import { ScenarioForm } from "./ScenarioForm";
import { ScenarioTable } from "./ScenarioTable";
import { useView, ViewToggle } from "./ViewToggle";
import { Empty, NoBars, Skeleton } from "./states";

export function ScenariosPage() {
  const { t } = useTranslation();
  const bars = useBarsStatus();
  const list = useScenarios();
  // undefined = closed, null = add, Scenario = edit
  const [form, setForm] = useState<Scenario | null | undefined>(undefined);
  const [view, setView] = useView();
  // same query keys as the cards, so switching view reuses the cache
  const results = useQueries({ queries: (list.data ?? []).map(whatIfQuery) });
  const noBars = !!bars.data && bars.data.last_trading_date == null;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement | null;
      if (e.key.toLowerCase() !== "n" || e.altKey || e.ctrlKey || e.metaKey || noBars || form !== undefined) return;
      if (el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable)) return;
      e.preventDefault();
      setForm(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [noBars, form]);

  let body;
  if (list.isError) {
    const code = list.error instanceof ApiError ? list.error.code : "INTERNAL";
    body = code === "UNREACHABLE"
      ? <ApiErrorState onRetry={() => void list.refetch()} />
      : <div role="alert"><p>{t(`error.${code}`, { defaultValue: t("error.INTERNAL") })}</p><button type="button" onClick={() => void list.refetch()}>{t("state.retry")}</button></div>;
  } else if (list.isPending) body = <div className="sc-grid"><Skeleton /><Skeleton /><Skeleton /></div>;
  else if (noBars) body = <NoBars />;
  else if (list.data.length === 0) body = <Empty onAdd={() => setForm(null)} />;
  else if (view === "table") {
    const rows = list.data.map((scenario, i) => {
      const q = results[i];
      const code = q?.error instanceof ApiError ? q.error.code : "INTERNAL";
      return { scenario, env: q?.data, error: q?.isError ? t(`error.${code}`, { defaultValue: t("error.INTERNAL") }) : undefined };
    });
    body = <ScenarioTable rows={rows} />;
  } else body = <div className="sc-grid">{list.data.map((s) => <ScenarioCard key={s.id} scenario={s} onEdit={() => setForm(s)} />)}</div>;

  return (
    <section data-testid="route-scenarios" style={{ padding: 16 }}>
      <style>{GRID_CSS}</style>
      <header style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12 }}>
        <h1 style={{ margin: 0 }}>{t("page.title")}</h1>
        <button type="button" disabled={noBars} onClick={() => setForm(null)}>{t("page.add")}</button>
        <ViewToggle view={view} onChange={setView} />
        {bars.data?.last_trading_date && (
          <span>{t("page.as_of", { date: formatDate(bars.data.last_trading_date), src: bars.data.source.toUpperCase() })}</span>
        )}
      </header>
      {body}
      {form !== undefined && <ScenarioForm scenario={form ?? undefined} onClose={() => setForm(undefined)} />}
    </section>
  );
}
