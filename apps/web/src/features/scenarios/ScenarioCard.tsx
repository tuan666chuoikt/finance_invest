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

function Bench({ b, buy }: { b: Benchmark; buy: string }) {
  const { t, i18n } = useTranslation();
  if (!b.available)
    return (
      <li data-testid="bench" className="muted">
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
      <div className="muted fs-sm">
        {t("card.dates" + (s.sell_date ? "" : "_today"), { from: formatDate(s.buy_date), to: formatDate(s.sell_date ?? r.dates.sell) })}
        {r.dates.shifts.map((x) => (
          <small key={x.field + x.from} className="note">
            {t(x.field === "buy_date" ? "card.shift_buy" : "card.shift_sell", { to: formatDate(x.to) })}
          </small>
        ))}
      </div>
      {env.approximate && (
        <div data-testid="approximate-flag" className="chip chip-warn"><span aria-hidden="true">⚠ ≈ </span>{t("card.approximate")}</div>
      )}
      <dl>
        <div className="row"><dt>{t("card.invested")}</dt><dd className="num">{formatVnd(r.position.invested_vnd.value)}</dd></div>
        <div className="row headline">
          <dt>{t("card.value")}</dt>
          <dd className="num headline">{formatVnd(r.value.liquidation_vnd.value)} <InfoButton figure={r.value.liquidation_vnd} envelope={env} name="liquidation_vnd" /></dd>
        </div>
        <div className="row">
          <dt>{t("card.pl")}</dt>
          <dd className="num">
            <span className={cls(pl)}>{arrow(pl)} {pl}</span>{" "}
            <span className={cls(pct)}>{arrow(pct)} {pct}</span>{" "}
            <InfoButton figure={r.returns.pl_vnd} envelope={env} name="pl_vnd" />
          </dd>
        </div>
        <div className="row"><dt>{t("card.cash")}</dt><dd className="num">{formatVnd(r.position.cash.value)}</dd></div>
      </dl>
      {env.flags.includes("below_one_lot") && <small className="note">{t(dca ? "card.below_lot_dca" : "card.below_lot_lump")}</small>}
      <div className="spark"><Sparkline points={r.equity_curve} symbol={s.symbol} /></div>
      {r.benchmarks.length > 0 && <ul className="bench">{r.benchmarks.map((b) => <Bench key={b.name} b={b} buy={r.dates.buy} />)}</ul>}
      {r.missing_sessions.length > 0 && (
        <small className="note-warn">
          {t("card.missing", { count: r.missing_sessions.length })}{" "}
          <details>
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
      <div className="row head">
        <div>
          <h2>{s.name || defaultName(s.symbol, s.amount_vnd, s.buy_date)}</h2>
          <small className="muted">
            {s.symbol} · {s.style === "dca"
              ? t("card.dca", { amount: formatVnd(s.amount_vnd), day: Number(s.buy_date.slice(8)) })
              : t("card.lump")}
          </small>
        </div>
        <CardMenu scenario={s} onEdit={onEdit} />
      </div>
      {q.data ? <Body s={s} env={q.data} /> : (
        <div role="alert" className="card-error">
          <p>{t("card.error", { reason })}</p>
          <button type="button" className="btn" onClick={onEdit}>{t("card.edit")}</button>
        </div>
      )}
    </article>
  );
}
