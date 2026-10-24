import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import type { Job } from "../app/useCrawlJob";
import { formatDateTime } from "../lib/format";

const NUM = new Intl.NumberFormat("vi-VN");
const hhmm = (iso: string) => formatDateTime(iso).slice(-5);
type Rec = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any -- Job.summary/error/progress are untyped JSON in the OpenAPI

function duration(t: TFunction, s: number) {
  const m = Math.floor(s / 60);
  return [m && t("crawl.minute", { n: m }), (s % 60 || !m) && t("crawl.second", { n: s % 60 })].filter(Boolean).join(" ");
}

function text(t: TFunction, job: Job, now: number): string | null {
  const p: Rec = job.progress ?? {}, s: Rec = job.summary ?? {}, e: Rec = job.error ?? {};
  if (job.status === "running") {
    const bits = [];
    if (p.step) {
      bits.push(
        t("crawl.step", {
          step: p.step, steps: p.steps, done: p.done, total: p.total,
          what: p.step === 1 ? t("crawl.step1", { date: String(p.trading_date ?? "").split("-").reverse().slice(0, 2).join("/") }) : t("crawl.step2"),
          unit: t(p.step === 1 ? "crawl.unit.symbols" : "crawl.unit.sessions"),
        }),
      );
    }
    bits.push(t("crawl.elapsed", { time: duration(t, Math.max(0, Math.round((now - Date.parse(job.created_at)) / 1000))) }));
    return bits.join(" · ");
  }
  if (job.status === "done") {
    const tk = s.ticks as Rec | null, b = (s.bars_1d ?? {}) as Rec;
    const parts = [
      s.no_session_today || !tk
        ? t("crawl.done.nosession")
        : t("crawl.done.ticks", { symbols: NUM.format(tk.symbols_fetched), rows: NUM.format(tk.rows) }) +
          (tk.partial_until ? " " + t("crawl.done.partial", { at: hhmm(tk.partial_until) }) : ""),
      t("crawl.done.sessions", { n: b.sessions_added ?? 0 }),
    ];
    const skipped = (tk?.symbols_skipped ?? 0) + (b.symbols_skipped ?? 0);
    if (skipped) parts.push(t("crawl.done.skipped", { n: skipped }));
    if (typeof s.duration_s === "number") parts.push(duration(t, s.duration_s));
    return t("crawl.done", { at: hhmm(job.finished_at ?? job.created_at), parts: parts.join(" · ") });
  }
  const where = [e.path && t("crawl.error.path", { path: e.path }), e.source && t("crawl.error.source", { source: e.source }),
    e.http_status && t("crawl.error.http", { code: e.http_status })].filter(Boolean);
  const tk = (s.ticks ?? null) as Rec | null;
  if (tk?.symbols_fetched != null && p.total) where.push(t("crawl.error.saved", { done: tk.symbols_fetched, total: p.total }));
  return [t("crawl.error", { message: e.message ?? "", code: e.code ?? "?" }), ...where].join(" · ");
}

export function CrawlStatus({ job, refused, startError }: { job: Job | null; refused: string | null; startError?: { code: string; message: string } | null }) {
  const { t } = useTranslation();
  const [now, setNow] = useState(Date.now());
  const [dismissed, setDismissed] = useState<number | null>(null);
  const [sawRunning, setSawRunning] = useState(false);
  const running = job?.status === "running";
  useEffect(() => {
    if (!running) return;
    const i = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(i);
  }, [running]);
  useEffect(() => {
    if (running) setSawRunning(true);
  }, [running]);
  // A done job from an earlier visit is not news (the button tooltip has it); a failure always shows.
  const shown = job && ["running", "done", "failed"].includes(job.status) && dismissed !== job.id && (job.status !== "done" || sawRunning || running);
  const cause = startError && (startError.code === "UNREACHABLE" ? t("crawl.unreachable") : startError.message);
  const lines = [startError && t("crawl.start_failed", { cause }), refused !== null && t("crawl.refused", { at: refused ? hhmm(refused) : "?" }), shown && text(t, job, now)].filter(Boolean);
  if (!lines.length) return null;
  return (
    <div role="status" aria-live="polite" data-testid="crawl-status" style={{ flexBasis: "100%" }}>
      {lines.join(" · ")}
      {shown && !running && (
        <button type="button" onClick={() => setDismissed(job!.id)} aria-label={t("crawl.dismiss")}>
          ×
        </button>
      )}
    </div>
  );
}
