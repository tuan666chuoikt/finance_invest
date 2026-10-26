import { Fragment, useEffect, useState, type ReactNode } from "react";
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

// Parts for the steps that ran (ticks, daily prices, rights events); a failed job keeps them before its error line.
function stepParts(t: TFunction, s: Rec): string[] {
  const tk = s.ticks as Rec | null, b = (s.bars_1d ?? {}) as Rec, ca = s.corporate_actions as Rec | null;
  const parts = [
    s.no_session_today || !tk
      ? t("crawl.done.nosession")
      : t("crawl.done.ticks", { symbols: NUM.format(tk.symbols_fetched), rows: NUM.format(tk.rows) }) +
        (tk.partial_until ? " " + t("crawl.done.partial", { at: hhmm(tk.partial_until) }) : ""),
    t("crawl.done.sessions", { n: b.sessions_added ?? 0 }),
  ];
  if (ca) parts.push(t("crawl.done.events", { n: ca.events_upserted ?? 0, changes: ca.changes ?? 0 }));
  return parts;
}

function text(t: TFunction, job: Job, now: number): ReactNode {
  const p: Rec = job.progress ?? {}, s: Rec = job.summary ?? {}, e: Rec = job.error ?? {};
  if (job.status === "running") {
    const bits = [];
    if (p.step) {
      bits.push(
        t("crawl.step", {
          step: p.step, steps: p.steps, done: p.done, total: p.total,
          what: p.step === 1 ? t("crawl.step1", { date: String(p.trading_date ?? "").split("-").reverse().slice(0, 2).join("/") }) : t(p.step === 3 ? "crawl.step3" : "crawl.step2"),
          unit: t(p.step === 2 ? "crawl.unit.sessions" : "crawl.unit.symbols"),
        }),
      );
    }
    bits.push(t("crawl.elapsed", { time: duration(t, Math.max(0, Math.round((now - Date.parse(job.created_at)) / 1000))) }));
    return bits.join(" · ");
  }
  if (job.status === "done") {
    const parts = stepParts(t, s);
    const b = (s.bars_1d ?? {}) as Rec, tk = s.ticks as Rec | null;
    const skipped = (tk?.symbols_skipped ?? 0) + (b.symbols_skipped ?? 0);
    if (skipped) parts.push(t("crawl.done.skipped", { n: skipped }));
    const deferred = (b.symbols_deferred ?? 0) + ((s.corporate_actions as Rec | null)?.symbols_deferred ?? 0);
    if (deferred > 0) parts.push(t("crawl.done.deferred", { n: deferred }));
    if (typeof s.duration_s === "number") parts.push(duration(t, s.duration_s));
    return t("crawl.done", { at: hhmm(job.finished_at ?? job.created_at), parts: parts.join(" · ") });
  }
  const where = [e.path && t("crawl.error.path", { path: e.path }), e.source && t("crawl.error.source", { source: e.source === "vci_iq" ? "VCI IQ" : e.source }),
    e.http_status && t("crawl.error.http", { code: e.http_status })].filter(Boolean);
  const tk = (s.ticks ?? null) as Rec | null;
  const saved = tk?.symbols_fetched != null && p.total ? t("crawl.error.saved", { done: tk.symbols_fetched, total: p.total }) : null;
  return (
    <>
      {s.bars_1d && stepParts(t, s).join(" · ") + " · "}
      {t("crawl.error", { message: e.message ?? "", code: e.code ?? "?" })}
      {where.map((w, i) => (
        <Fragment key={i}> · <code>{w}</code></Fragment>
      ))}
      {saved && ` · ${saved}`}
    </>
  );
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
  const mod = shown ? (job.status === "failed" ? "error" : job.status) : startError ? "error" : "";
  const p: Rec = job?.progress ?? {};
  const pct = shown && running && p.total ? Math.min(100, Math.round((Number(p.done) / Number(p.total)) * 100)) : null;
  return (
    <div role="status" aria-live="polite" data-testid="crawl-status" className={"status" + (mod ? ` status-${mod}` : "")}>
      {running ? <span className="cb-spin" aria-hidden="true">⟳</span> : mod === "done" ? <span className="status-icon" aria-hidden="true">✓</span> : null}
      <span className="status-text">
        {lines.map((l, i) => (
          <Fragment key={i}>{i > 0 && " · "}{l}</Fragment>
        ))}
      </span>
      {shown && !running && (
        <button type="button" className="btn-icon" onClick={() => setDismissed(job!.id)} aria-label={t("crawl.dismiss")}>
          ×
        </button>
      )}
      {pct !== null && <div className="status-bar" aria-hidden="true" style={{ width: `${pct}%` }} />}
    </div>
  );
}
