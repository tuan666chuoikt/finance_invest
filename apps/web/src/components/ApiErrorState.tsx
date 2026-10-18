import { useTranslation } from "react-i18next";

/** Pages render this when their query throws ApiError code UNREACHABLE. */
export function ApiErrorState({ onRetry }: { onRetry: () => void }) {
  const { t } = useTranslation();
  return (
    <div role="alert" style={{ width: "100%", padding: 16 }}>
      <p>{t("error.UNREACHABLE")}</p>
      <button type="button" onClick={onRetry}>
        {t("state.retry")}
      </button>
    </div>
  );
}
