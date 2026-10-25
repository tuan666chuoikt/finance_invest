import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "../../api/client";
import { formatDate, parseVndInput } from "../../lib/format";
import { useSaveScenario, useSymbol } from "./api";
import type { Scenario, ScenarioIn } from "./api";
import { SymbolCombobox } from "./SymbolCombobox";
import { defaultName } from "./defaultName";

const MAX_VND = 100_000_000_000;
const NUM = new Intl.NumberFormat("vi-VN");
const group = (n: number | null) => (n === null ? "" : NUM.format(n));
// Server field names -> form field names.
const FIELD: Record<string, string> = { name: "name", symbol: "symbol", amount_vnd: "amount", buy_date: "start", sell_date: "end", style: "style" };

/** One year before `last`, string math only (no Date: time-zone shifts). 29 Feb -> 28 Feb. */
function yearBefore(last: string): string {
  const [y, m, d] = last.split("-");
  return `${Number(y) - 1}-${m}-${m === "02" && d === "29" ? "28" : d}`;
}

interface Props {
  scenario?: Scenario; // present = edit mode
  onClose: () => void;
}

// shortcut: the below-one-lot hint is not live here; it appears on the card after the first computation
// (engine flag below_one_lot + details.min_amount). Upgrade when the start close is exposed to the form.
export function ScenarioForm({ scenario, onClose }: Props) {
  const { t } = useTranslation();
  const trigger = useRef(document.activeElement as HTMLElement | null);
  const save = useSaveScenario();
  const [name, setName] = useState(scenario?.name ?? "");
  const [symbol, setSymbol] = useState(scenario?.symbol ?? "");
  const [style, setStyle] = useState<ScenarioIn["style"]>(scenario?.style ?? "lump_sum");
  const [amount, setAmount] = useState(group(scenario?.amount_vnd ?? 10_000_000));
  const [start, setStart] = useState(scenario?.buy_date ?? "");
  const [touched, setTouched] = useState(!!scenario);
  const [today, setToday] = useState(scenario ? scenario.sell_date == null : true);
  const [end, setEnd] = useState(scenario?.sell_date ?? "");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const bars = useSymbol(symbol || null).data?.bars_1d ?? null;

  useEffect(() => {
    if (!touched && bars) setStart(yearBefore(bars.last) < bars.first ? bars.first : yearBefore(bars.last));
  }, [bars, touched]);

  const close = () => { onClose(); trigger.current?.focus(); };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const amt = parseVndInput(amount);
    const err: Record<string, string> = {};
    if (!symbol) err.symbol = t("form.err.symbol");
    if (amt === null || amt <= 0) err.amount = t("form.err.amount_min");
    else if (amt > MAX_VND) err.amount = t("form.err.amount_max");
    if (!start) err.start = t("form.err.start");
    else if (bars && (start < bars.first || start > bars.last)) {
      err.start = t("form.err.start_range", { first: bars.first.split("-").reverse().join("/"), last: bars.last.split("-").reverse().join("/") });
    }
    if (!today && end && start && end < start) err.end = t("form.err.end");
    if (!today && !end) err.end = t("form.err.end_required");
    if (name.length > 60) err.name = t("form.err.name");
    setErrors(err);
    if (Object.keys(err).length) return;
    const body: ScenarioIn = {
      name: name.trim() || defaultName(symbol, amt!, start),
      symbol, style, amount_vnd: amt!, buy_date: start, sell_date: today ? null : end,
    };
    save.mutate({ id: scenario?.id, body }, {
      onSuccess: close,
      onError: (ex) => {
        const d = ex instanceof ApiError ? ex.details : {};
        const code = ex instanceof ApiError ? ex.code : "INTERNAL";
        const noData = code === "NO_DATA";
        const field = code === "SYMBOL_UNKNOWN" || d.symbol ? "symbol" : noData ? "start" : FIELD[String(d.field)] ?? "form";
        const first = d.first_available;
        setErrors({
          [field]: noData && typeof first === "string"
            ? t("error.NO_DATA_before", { symbol, date: formatDate(first) })
            : t(`error.${code}`, { defaultValue: t("error.INTERNAL") }),
        });
      },
    });
  };

  const msg = (f: string) => errors[f] && <p id={`err-${f}`} role="alert" className="field-error">{errors[f]}</p>;
  const d = (f: string) => (errors[f] ? { "aria-invalid": true, "aria-describedby": `err-${f}` } : {});

  return (
    <dialog open aria-label={t(scenario ? "form.title_edit" : "form.title_add")} className="scenario-panel"
      onKeyDown={(e) => { if (e.key === "Escape") close(); }}>
      <form onSubmit={onSubmit} noValidate>
        <header className="panel-head">
          <h2>{t(scenario ? "form.title_edit" : "form.title_add")}</h2>
          <button type="button" className="btn-icon" aria-label={t("form.cancel")} onClick={close}>✕</button>
        </header>
        <div className="panel-body">
          {msg("form")}
          <div className="field">
            <label htmlFor="sc-name">{t("form.name")}</label>
            <input id="sc-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder={symbol && start ? defaultName(symbol, parseVndInput(amount) ?? 0, start) : ""} {...d("name")} />
            {msg("name")}
          </div>
          <div className="field">
            <label>{t("form.symbol")}
              <SymbolCombobox value={symbol} onPick={setSymbol} invalid={!!errors.symbol} describedBy="err-symbol" />
            </label>
            {msg("symbol")}
          </div>
          <fieldset className="field">
            <legend>{t("form.style")}</legend>
            {(["lump_sum", "dca"] as const).map((s) => (
              <label key={s} className="radio-row"><input type="radio" name="style" checked={style === s} onChange={() => setStyle(s)} />{t(`form.style_${s}`)}</label>
            ))}
          </fieldset>
          <div className="field">
            <label htmlFor="sc-amount">{t(style === "dca" ? "form.amount_monthly" : "form.amount")}</label>
            <span className="input-wrap">
              <input id="sc-amount" className="amount" inputMode="numeric" value={amount} onChange={(e) => setAmount(group(parseVndInput(e.target.value)))} {...d("amount")} />
              <span className="suffix" aria-hidden="true">₫</span>
            </span>
            {msg("amount")}
          </div>
          <div className="field">
            <label htmlFor="sc-start">{t("form.start")}</label>
            <input id="sc-start" type="date" value={start} min={bars?.first} max={bars?.last} onChange={(e) => { setStart(e.target.value); setTouched(true); }} {...d("start")} />
            {msg("start")}
          </div>
          <div className="field">
            <label className="inline-check"><input type="checkbox" checked={today} onChange={(e) => setToday(e.target.checked)} />{t("form.today")}</label>
            {!today && (
              <>
                <label htmlFor="sc-end">{t("form.end")}</label>
                <input id="sc-end" type="date" value={end} min={start || undefined} onChange={(e) => setEnd(e.target.value)} {...d("end")} />
              </>
            )}
            {msg("end")}
          </div>
        </div>
        <footer className="panel-foot">
          <button type="button" className="btn" onClick={close}>{t("form.cancel")}</button>
          <button type="submit" className="btn btn-primary" disabled={save.isPending}>{t("form.save")}</button>
        </footer>
      </form>
    </dialog>
  );
}
