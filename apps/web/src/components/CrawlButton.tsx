import { useTranslation } from "react-i18next";
import { formatDateTime } from "../lib/format";
import type { Job } from "../app/useCrawlJob";

// Icon-only below 480 px; the accessible name stays on aria-label.
const CSS = `.cb-spin{display:inline-block;animation:cb-spin 1s linear infinite}@keyframes cb-spin{to{transform:rotate(360deg)}}
@media (max-width:479px){.cb-label{display:none}}`;

export function CrawlButton({ job, running, onClick }: { job: Job | null; running: boolean; onClick: () => void }) {
  const { t } = useTranslation();
  const label = running ? t("crawl.running") : t("crawl.idle");
  const last = job && job.status !== "running"
    ? t("crawl.last", { at: formatDateTime(job.finished_at ?? job.created_at), result: t(`crawl.last.${job.status}`) })
    : undefined;
  return (
    <button type="button" disabled={running} aria-busy={running} aria-label={label} title={last} onClick={onClick}>
      <style>{CSS}</style>
      {running ? <span className="cb-spin" aria-hidden="true">⟳</span> : <span aria-hidden="true">⟳</span>}
      <span className="cb-label"> {label.replace(/^⟳ /, "")}</span>
    </button>
  );
}
