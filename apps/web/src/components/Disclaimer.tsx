import { useTranslation } from "react-i18next";
// Literal in both languages on purpose (ux/app-shell.md "Disclaimer banner"): never translated, never dismissible.
export function Disclaimer() {
  const { t } = useTranslation();
  return (
    <aside role="note" aria-label={t("disclaimer.name")} data-testid="disclaimer" className="band">
      <span aria-hidden="true">ⓘ </span>
      <span className="vi">Mô phỏng để học, không phải lời khuyên đầu tư</span>
      <span aria-hidden="true"> · </span>
      <span>Educational simulation, not investment advice</span>
    </aside>
  );
}
