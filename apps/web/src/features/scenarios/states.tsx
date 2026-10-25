import { useTranslation } from "react-i18next";

export function Empty({ onAdd }: { onAdd: () => void }) {
  const { t } = useTranslation();
  return (
    <div data-testid="state-empty" className="sc-card sc-center">
      <p>{t("page.empty")}</p>
      <p className="muted fs-sm">{t("page.empty_example")}</p>
      <button type="button" className="btn btn-primary" onClick={onAdd}>{t("page.add")}</button>
    </div>
  );
}

export function NoBars() {
  const { t } = useTranslation();
  return (
    <div data-testid="state-no-bars" className="sc-card sc-center">
      <p>{t("page.no_bars")} <code>make backfill</code></p>
    </div>
  );
}

export function Skeleton() {
  const { t } = useTranslation();
  return (
    <div className="sc-card skeleton" role="status" aria-busy="true" data-testid="card-skeleton">
      <span className="visually-hidden">{t("state.loading")}</span>
      <div className="sk" /><div className="sk" /><div className="sk" /><div className="sk" />
    </div>
  );
}
