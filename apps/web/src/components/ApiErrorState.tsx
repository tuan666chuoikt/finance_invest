import { useTranslation } from "react-i18next";

/** Pages render this when their query throws ApiError code UNREACHABLE. */
export function ApiErrorState({ onRetry }: { onRetry: () => void }) {
  const { t } = useTranslation();
  return (
    <div role="alert" className="api-error">
      <p>{t("error.UNREACHABLE")}</p>
      <button type="button" className="btn" onClick={onRetry}>
        {t("state.retry")}
      </button>
    </div>
  );
}
