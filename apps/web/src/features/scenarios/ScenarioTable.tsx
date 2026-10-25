import { useState } from "react";
import { useTranslation } from "react-i18next";
import { formatDate, formatPct, formatPp, formatVnd } from "../../lib/format";
import type { Scenario } from "./api";
import type { WhatIfEnvelope } from "./result";
import "./table.css";

/** `env` set = computed; `error` = translated reason; neither = still loading. */
export interface Row { scenario: Scenario; env?: WhatIfEnvelope; error?: string }

type Cell = { text: string; num: number | null };
const NA: Cell = { text: "n/a", num: null };
// Number() is for ordering only; displayed text comes from the formatters.
const vnd = (v: string): Cell => ({ text: formatVnd(v), num: Number(v) });
// P/L only: explicit "+" like the card's signedVnd (formatVnd signs negatives only).
const signedVnd = (v: string): Cell => ({ text: Number(v) > 0 ? `+${formatVnd(v)}` : formatVnd(v), num: Number(v) });

function bench(env: WhatIfEnvelope, name: string, lang: string): Cell {
  const b = env.result.benchmarks.find((x) => x.name === name);
  if (!b || !b.available) return NA;
  return { text: formatPp(b.diff_pp.value, lang), num: Number(b.diff_pp.value) };
}

const COLS = ["invested", "value", "pl_vnd", "pl_pct", "vs_vnindex", "vs_e1"] as const;
type Col = (typeof COLS)[number];

function cells(r: Row, lang: string): Record<Col, Cell> {
  const e = r.env;
  if (!e) return { invested: NA, value: NA, pl_vnd: NA, pl_pct: NA, vs_vnindex: NA, vs_e1: NA };
  const x = e.result;
  return {
    invested: vnd(x.position.invested_vnd.value),
    value: vnd(x.value.liquidation_vnd.value),
    pl_vnd: signedVnd(x.returns.pl_vnd.value),
    pl_pct: { text: formatPct(x.returns.pl_pct.value), num: Number(x.returns.pl_pct.value) },
    vs_vnindex: bench(e, "VN-Index", lang),
    vs_e1: bench(e, "E1VFVN30", lang),
  };
}

// Sign comes from the number, not the text: a formatter that omits "+" must not turn a gain into "=".
const arrow = (n: number) => (n > 0 ? "▲" : n < 0 ? "▼" : "=");
const cls = (n: number) => (n > 0 ? "up" : n < 0 ? "down" : "zero");

export function ScenarioTable({ rows }: { rows: Row[] }) {
  const { t, i18n } = useTranslation();
  const [sort, setSort] = useState<{ col: Col; dir: "asc" | "desc" }>({ col: "pl_pct", dir: "desc" });
  const lang = i18n.language;

  const data = rows.map((r) => ({ r, c: cells(r, lang) }));
  // null (failed, loading, n/a) always last, whichever the direction
  data.sort((a, b) => {
    const x = a.c[sort.col].num, y = b.c[sort.col].num;
    if (x === null || y === null) return x === y ? 0 : x === null ? 1 : -1;
    return sort.dir === "asc" ? x - y : y - x;
  });

  const th = (col: Col) => (
    <th key={col} className="num" aria-sort={sort.col === col ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}>
      <button type="button" className="th-btn" onClick={() => setSort({ col, dir: sort.col === col && sort.dir === "desc" ? "asc" : "desc" })}>
        {t(`table.${col}`)}{sort.col === col ? (sort.dir === "asc" ? " ▲" : " ▼") : <span className="sort-hint" aria-hidden="true"> ↕</span>}
      </button>
    </th>
  );

  return (
    <div>
      <div className="sc-tablewrap" data-testid="scenario-table">
        <table>
          <thead>
            <tr>
              <th className="sticky">{t("table.name")}</th>
              <th>{t("table.symbol")}</th><th>{t("table.style")}</th><th>{t("table.start")}</th><th>{t("table.end")}</th>
              {COLS.map(th)}
              <th>{t("table.flag")}</th>
            </tr>
          </thead>
          <tbody>
            {data.map(({ r, c }) => {
              const s = r.scenario;
              const ok = !!r.env;
              const cell = (col: Col) => <td key={col} className="num">{c[col].text}</td>;
              const signed = (col: Col) => {
                const { text, num } = c[col];
                return <td key={col} className="num">{num === null ? text : <span className={cls(num)}>{arrow(num)} {text}</span>}</td>;
              };
              return (
                <tr key={s.id}>
                  <th scope="row" className="sticky">{s.name}</th>
                  <td>{s.symbol}</td>
                  <td>{t(s.style === "dca" ? "table.dca" : "table.lump")}</td>
                  <td>{formatDate(s.buy_date)}</td>
                  <td>{s.sell_date ? formatDate(s.sell_date) : r.env ? formatDate(r.env.result.dates.sell) : t("table.today")}</td>
                  {cell("invested")}
                  {ok ? cell("value") : <td className="num" role={r.error ? "alert" : undefined}>{r.error ? t("card.error", { reason: r.error }) : "…"}</td>}
                  {signed("pl_vnd")}{signed("pl_pct")}{cell("vs_vnindex")}{cell("vs_e1")}
                  <td>{r.env?.approximate && <span className="flag" role="img" title={t("table.approximate")} aria-label={t("table.approximate")}>⚠</span>}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="sc-tablefoot">{t("table.footer")}</p>
    </div>
  );
}
