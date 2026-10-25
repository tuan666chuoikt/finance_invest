import { useTranslation } from "react-i18next";
import { useBarsStatus } from "../app/useBarsStatus";
import { formatDate, formatDateTime } from "../lib/format";

const DAY = 86_400_000;

/** Today's date in Asia/Ho_Chi_Minh as yyyy-mm-dd. */
const hcmToday = (now: Date) => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh" }).format(now);

/**
 * shortcut: weekday rule (no holiday calendar), replace with GET /session when it exists (S04).
 * Stale = last_trading_date is before the previous weekday (Mon -> Fri, Sat/Sun -> Fri, else yesterday).
 */
export function isStale(lastTradingDate: string, now = new Date()): boolean {
  const t = Date.parse(`${hcmToday(now)}T00:00:00Z`); // UTC midnight of the HCM calendar day, math only
  const dow = new Date(t).getUTCDay();
  const back = dow === 0 ? 2 : dow === 6 ? 1 : dow === 1 ? 3 : 1;
  return lastTradingDate < new Date(t - back * DAY).toISOString().slice(0, 10);
}

export function FreshnessChip() {
  const { t } = useTranslation();
  const { data, isError } = useBarsStatus();
  let text: string;
  let short = "";
  let stale = false;
  if (isError) text = t("chip.unavailable");
  else if (!data) text = t("state.loading");
  else if (!data.last_trading_date || !data.as_of) text = t("state.empty");
  else {
    const dt = formatDateTime(data.as_of);
    text = t("chip.as_of", { dt, src: data.source.toUpperCase() });
    short = dt.replace(/\/\d{4}/, ""); // dd/mm hh:mm for narrow screens
    stale = isStale(data.last_trading_date);
    if (stale) text += ` · ${t("chip.stale", { date: formatDate(data.last_trading_date) })}`;
  }
  return (
    <a href="/data-quality" data-testid="freshness-chip" data-stale={stale} className={"chip" + (stale ? " chip-warn" : "")} title={text}>
      {short ? (
        <>
          <span className="chip-long">{text}</span>
          <span className="chip-short">{(stale ? "⚠ " : "") + short}</span>
        </>
      ) : (
        text
      )}
    </a>
  );
}
