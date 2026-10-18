import { formatPct, formatPp, formatVnd } from "../../lib/format";
import type { Figure } from "./result";

export function figureText(fig: Figure, lang: string): string {
  const en = lang === "en";
  switch (fig.unit) {
    case "vnd": return formatVnd(fig.value);
    case "pct": return formatPct(fig.value);
    case "pp": return formatPp(fig.value, lang);
    case "shares": return `${fig.value} ${en ? "sh" : "cp"}`;
    case "days": return `${fig.value} ${en ? "days" : "ngày"}`;
    default: return fig.value;
  }
}

const NUM = new Intl.NumberFormat("vi-VN");
/** Heuristic for `how.inputs` (unit unknown): integers as plain VND/qty, 4-dp strings as %, else as sent. */
export function inputText(v: string): string {
  if (/^-?\d+$/.test(v)) return NUM.format(Number(v));
  if (/^-?\d+\.\d{4}$/.test(v)) return formatPct(v);
  return v;
}
