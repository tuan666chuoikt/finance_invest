import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

// Hand-typed per platform.md §2.5 GET /bars/1d/status.
export interface BarsStatus {
  last_trading_date: string | null;
  as_of: string | null;
  source: string;
  symbols: number;
}

export const useBarsStatus = () =>
  useQuery({ queryKey: ["bars-status"], queryFn: () => api<BarsStatus>("/bars/1d/status"), refetchInterval: 60_000 });
