import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import type { components } from "../../api/types";
import type { WhatIfEnvelope } from "./result";

export type Scenario = components["schemas"]["Scenario"];
export type ScenarioIn = components["schemas"]["ScenarioIn"];
export type SymbolOut = components["schemas"]["SymbolOut"];
export type SymbolDetail = components["schemas"]["SymbolDetail"];

export const useScenarios = () => useQuery({ queryKey: ["scenarios"], queryFn: () => api<Scenario[]>("/scenarios") });

export function useSaveScenario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id?: number; body: ScenarioIn }) =>
      id === undefined
        ? api<Scenario>("/scenarios", { method: "POST", body: JSON.stringify(body) })
        : api<Scenario>(`/scenarios/${id}`, { method: "PUT", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenarios"] }),
  });
}

export function useDeleteScenario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api<void>(`/scenarios/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenarios"] }),
  });
}

export const useSymbolSearch = (q: string) =>
  useQuery({
    queryKey: ["symbols", q],
    queryFn: () => api<SymbolOut[]>(`/symbols?q=${encodeURIComponent(q)}&limit=20`),
    enabled: q.trim() !== "",
  });

export const useSymbol = (symbol: string | null) =>
  useQuery({
    queryKey: ["symbol", symbol],
    queryFn: () => api<SymbolDetail>(`/symbols/${encodeURIComponent(symbol!)}`),
    enabled: !!symbol,
  });

/** One computation per saved scenario (platform.md §2.5); `sell_date: null` = latest bar. */
export const useWhatIf = (s: ScenarioIn) =>
  useQuery({
    queryKey: ["whatif", s.symbol, s.style, s.amount_vnd, s.buy_date, s.sell_date ?? null],
    queryFn: () =>
      api<WhatIfEnvelope>("/whatif", {
        method: "POST",
        body: JSON.stringify({
          symbol: s.symbol, style: s.style, amount_vnd: s.amount_vnd, buy_date: s.buy_date, sell_date: s.sell_date ?? null,
        }),
      }),
  });
