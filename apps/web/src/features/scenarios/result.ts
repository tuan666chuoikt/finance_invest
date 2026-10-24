// Mirrors .finvest/architecture/contracts/analytics.md §1.1, §1.4, §2.4. Decimal values stay strings.
export type Unit = "vnd" | "pct" | "pp" | "ratio" | "shares" | "days";

export interface How {
  formula: string;
  inputs: Record<string, string>;
  as_of: string;
  rules_version: string;
  cite: string;
}
export interface Figure {
  value: string;
  unit: Unit;
  how: How;
}
export interface Shift { field: string; from: string; to: string; reason: string }
export interface Contribution {
  date: string; requested: string; amount_vnd: number; qty: number; price: number; fee_vnd: number; cash_after: number;
}
export interface EquityPoint { date: string; market_value: number; invested: number }
export type Benchmark =
  | { name: string; investable: boolean; available: true; value_vnd: Figure; pl_pct: Figure; diff_pp: Figure }
  | { name: string; investable: boolean; available: false; first_available: string | null };

export interface WhatIfResult {
  dates: { buy: string; sell: string; shifts: Shift[] };
  contributions: Contribution[];
  position: { shares: Figure; cash: Figure; invested_vnd: Figure };
  value: { market_value_vnd: Figure; sell_fee_vnd: Figure; sell_tax_vnd: Figure; liquidation_vnd: Figure };
  returns: { pl_vnd: Figure; pl_pct: Figure; cagr_pct: Figure | null; cagr_note?: Figure; holding_days: Figure };
  benchmarks: Benchmark[];
  missing_sessions: string[];
  equity_curve: EquityPoint[];
}
export interface WhatIfEnvelope {
  params: Record<string, unknown>;
  data_snapshot: string;
  rules_version: string;
  price_basis: "nominal" | "source_adjusted";
  approximate: boolean;
  flags: string[];
  disclaimer: string;
  result: WhatIfResult;
}

export const isFigure = (x: unknown): x is Figure => {
  const o = x as Record<string, unknown> | null;
  return typeof o === "object" && o !== null && "value" in o && "unit" in o && "how" in o;
};
