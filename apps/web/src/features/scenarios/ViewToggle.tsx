import { useState } from "react";
import { useTranslation } from "react-i18next";

export type View = "cards" | "table";
const KEY = "finvest.scenarios.view";

export function useView(): [View, (v: View) => void] {
  const [view, setView] = useState<View>(() => {
    try { return localStorage.getItem(KEY) === "table" ? "table" : "cards"; } catch { return "cards"; }
  });
  return [view, (v) => { setView(v); try { localStorage.setItem(KEY, v); } catch { /* storage blocked: choice lasts this session */ } }];
}

export function ViewToggle({ view, onChange }: { view: View; onChange: (v: View) => void }) {
  const { t } = useTranslation();
  return (
    <div role="group" aria-label={t("page.view")}>
      {(["cards", "table"] as const).map((v) => (
        <button key={v} type="button" aria-pressed={view === v} onClick={() => onChange(v)}>{t(`page.view_${v}`)}</button>
      ))}
    </div>
  );
}
