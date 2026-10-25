import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSymbolSearch } from "./api";

interface Props {
  value: string; // picked symbol, "" until a listbox row is chosen
  onPick: (symbol: string) => void;
  invalid?: boolean;
  describedBy?: string;
}

/** Type-ahead over GET /symbols?q=; only a listbox row counts as a value (ux "must exist"). */
export function SymbolCombobox({ value, onPick, invalid, describedBy }: Props) {
  const { t } = useTranslation();
  const id = useId();
  const [text, setText] = useState(value);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const { data = [] } = useSymbolSearch(open ? text : "");
  const show = open && text.trim() !== "" && data.length > 0;

  const pick = (i: number) => {
    const row = data[i];
    if (!row) return;
    setText(row.symbol);
    setOpen(false);
    onPick(row.symbol);
  };

  return (
    <div style={{ position: "relative" }}>
      <input
        role="combobox"
        aria-label={t("form.symbol")}
        aria-expanded={show}
        aria-controls={`${id}-list`}
        aria-autocomplete="list"
        aria-activedescendant={show ? `${id}-${active}` : undefined}
        aria-invalid={invalid || undefined}
        aria-describedby={describedBy}
        autoComplete="off"
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setOpen(true);
          setActive(0);
          if (value) onPick(""); // editing the text drops the previous pick
        }}
        onKeyDown={(e) => {
          if (!show) return;
          if (e.key === "ArrowDown" || e.key === "ArrowUp") {
            e.preventDefault();
            setActive((a) => (a + (e.key === "ArrowDown" ? 1 : data.length - 1)) % data.length);
          } else if (e.key === "Enter") {
            e.preventDefault(); // choose the row, do not submit the form
            pick(active);
          } else if (e.key === "Escape") {
            e.stopPropagation(); // first Esc closes the list, the next cancels the form
            setOpen(false);
          }
        }}
      />
      <ul id={`${id}-list`} role="listbox" hidden={!show} className="combo-list">
        {show &&
          data.map((r, i) => (
            <li
              key={r.symbol}
              id={`${id}-${i}`}
              role="option"
              aria-selected={i === active}
              onMouseDown={(e) => { e.preventDefault(); pick(i); }}
            >
              {r.symbol} · {r.exchange}
            </li>
          ))}
      </ul>
    </div>
  );
}
