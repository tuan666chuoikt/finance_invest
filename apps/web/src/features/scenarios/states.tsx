import { useTranslation } from "react-i18next";

export function Empty({ onAdd }: { onAdd: () => void }) {
  const { t } = useTranslation();
  return (
    <div data-testid="state-empty" style={{ padding: 16 }}>
      <p>{t("page.empty")}</p>
      <button type="button" onClick={onAdd}>{t("page.add")}</button>
      <p>{t("page.empty_example")}</p>
    </div>
  );
}

export function NoBars() {
  const { t } = useTranslation();
  return (
    <div data-testid="state-no-bars" style={{ padding: 16 }}>
      {t("page.no_bars")} <code>make backfill</code>
    </div>
  );
}

export function Skeleton() {
  const { t } = useTranslation();
  return (
    <div className="sc-card" aria-busy="true" aria-label={t("state.loading")} data-testid="card-skeleton"
      style={{ minHeight: 220, opacity: 0.5 }} />
  );
}
