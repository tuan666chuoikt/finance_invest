import { formatDate, formatVnd } from "../../lib/format";

/** "FPT · 10.000.000 ₫ · 12/10/2025" (ux/scenario-dashboard.md "Form"). */
export const defaultName = (symbol: string, amount: number, start: string): string =>
  `${symbol} · ${formatVnd(amount)} · ${formatDate(start)}`;
