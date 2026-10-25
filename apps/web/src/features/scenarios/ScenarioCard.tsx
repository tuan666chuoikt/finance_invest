import { useTranslation } from "react-i18next";
import { ApiError } from "../../api/client";
import { formatDate, formatPct, formatPp, formatVnd } from "../../lib/format";
import { useWhatIf, type Scenario } from "./api";
import { CardMenu } from "./CardMenu";
import { InfoButton } from "./HowComputed";
import type { Benchmark, WhatIfEnvelope } from "./result";
import { Sparkline } from "./Sparkline";
import { defaultName } from "./defaultName";
import { Skeleton } from "./states";

const arrow = (text: string) => (text.startsWith("+") ? "▲" : text.startsWith("−") ? "▼" : "=");
const cls = (text: string) => (text.startsWith("+") ? "up" : text.startsWith("−") ? "down" : "zero");
/** Sign for an integer-VND string; display only. */
const signedVnd = (v: string) => (v.startsWith("-") || v === "0" ? formatVnd(v) : `+${formatVnd(v)}`);

const CSS = `
.sc-grid{display:grid;gap:16px;grid-template-columns:1fr}
@media (min-width:768px){.sc-grid{grid-template-columns:repeat(2,1fr)}}
@media (min-width:1024px){.sc-grid{grid-template-columns:repeat(3,1fr)}}
.sc-card{border:1px solid GrayText;border-radius:8px;padding:12px;min-width:0}
.sc-card dl{margin:0}.sc-card .row{display:flex;justify-content:space-between;gap:8px}
.up{color:#15803d}.down{color:#b91c1c}.zero{color:#a16207}
@media (prefers-color-scheme:dark){.up{color:#4ade80}.down{color:#f87171}.zero{color:#facc15}}`;
export const GRID_CSS = CSS;

function Bench({ b, buy }: { b: Benchmark; buy: string }) {
  const { t, i18n } = useTranslation();
  if (!b.available)
    return (
      <li data-testid="bench">
        {!b.first_available
          ? t("card.bench_na_nodate", { name: b.name })
          : b.first_available > buy // ISO dates compare lexicographically
            ? t("card.bench_na", { name: b.name, date: formatDate(b.first_available) })
            : t("card.bench_na_gap", { name: b.name })}
      </li>
    );
  const pct = formatPct(b.pl_pct.value);
  return (
    <li data-testid="bench" className="row">
      <span title={b.investable ? undefined : t("card.non_investable")}>{b.name}</span>
      <span><span className={cls(pct)}>{arrow(pct)} {pct}</span> ({formatPp(b.diff_pp.value, i18n.language)})</span>
    </li>
  );
}

function Body({ s, env }: { s: Scenario; env: WhatIfEnvelope }) {
  const { t, i18n } = useTranslation();
  const r = env.result;
  const pl = signedVnd(r.returns.pl_vnd.value);
  const pct = formatPct(r.returns.pl_pct.value);
  const dca = s.style === "dca";
  return (
    <>
      <div>
        {t("card.dates" + (s.sell_date ? "" : "_today"), { from: formatDate(s.buy_date), to: formatDate(s.sell_date ?? r.dates.sell) })}
        {r.dates.shifts.map((x) => (
          <small key={x.field + x.from} style={{ display: "block" }}>
            {t(x.field === "buy_date" ? "card.shift_buy" : "card.shift_sell", { to: formatDate(x.to) })}
          </small>
        ))}
      </div>
      {env.approximate && (
        <div data-testid="approximate-flag"><span aria-hidden="true">⚠ ≈ </span>{t("card.approximate")}</div>
      )}
      <dl>
        <div className="row"><dt>{t("card.invested")}</dt><dd>{formatVnd(r.position.invested_vnd.value)}</dd></div>
        <div className="row">
          <dt>{t("card.value")}</dt>
          <dd>{formatVnd(r.value.liquidation_vnd.value)} <InfoButton figure={r.value.liquidation_vnd} envelope={env} name="liquidation_vnd" /></dd>
        </div>
        <div className="row">
          <dt>{t("card.pl")}</dt>
          <dd>
            <span className={cls(pl)}>{arrow(pl)} {pl}</span>{" "}
            <span className={cls(pct)}>{arrow(pct)} {pct}</span>{" "}
            <InfoButton figure={r.returns.pl_vnd} envelope={env} name="pl_vnd" />
          </dd>
        </div>
        <div className="row"><dt>{t("card.cash")}</dt><dd>{formatVnd(r.position.cash.value)}</dd></div>
      </dl>
      {env.flags.includes("below_one_lot") && <small>{t(dca ? "card.below_lot_dca" : "card.below_lot_lump")}</small>}
      <Sparkline points={r.equity_curve} symbol={s.symbol} />
      {r.benchmarks.length > 0 && <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>{r.benchmarks.map((b) => <Bench key={b.name} b={b} buy={r.dates.buy} />)}</ul>}
      {r.missing_sessions.length > 0 && (
        <small>
          {t("card.missing", { count: r.missing_sessions.length })}{" "}
          <details style={{ display: "inline" }}>
            <summary aria-label={t("card.missing_list")}>(i)</summary>
            {r.missing_sessions.map((d) => formatDate(d)).join(", ")}
          </details>
        </small>
      )}
    </>
  );
}

export function ScenarioCard({ scenario: s, onEdit }: { scenario: Scenario; onEdit: () => void }) {
  const { t } = useTranslation();
  const q = useWhatIf(s);
  if (q.isPending) return <Skeleton />;
  const code = q.error instanceof ApiError ? q.error.code : "INTERNAL";
  const first = q.error instanceof ApiError ? q.error.details.first_available : undefined;
  const reason = code === "NO_DATA" && typeof first === "string"
    ? t("error.NO_DATA_before", { symbol: s.symbol, date: formatDate(first) })
    : t(`error.${code}`, { defaultValue: t("error.INTERNAL") });
  return (
    <article className="sc-card" data-testid="scenario-card">
      <div className="row" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1em" }}>{s.name || defaultName(s.symbol, s.amount_vnd, s.buy_date)}</h3>
          <small>
            {s.symbol} · {s.style === "dca"
              ? t("card.dca", { amount: formatVnd(s.amount_vnd), day: Number(s.buy_date.slice(8)) })
              : t("card.lump")}
          </small>
        </div>
        <CardMenu scenario={s} onEdit={onEdit} />
      </div>
      {q.data ? <Body s={s} env={q.data} /> : (
        <div role="alert">
          <p>{t("card.error", { reason })}</p>
          <button type="button" onClick={onEdit}>{t("card.edit")}</button>
        </div>
      )}
    </article>
  );
}
