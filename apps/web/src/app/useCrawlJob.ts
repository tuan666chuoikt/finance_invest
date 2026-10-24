import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { components } from "../api/types";

export type Job = components["schemas"]["Job"];

export function useCrawlJob() {
  const qc = useQueryClient();
  const [refused, setRefused] = useState<string | null>(null); // started_at of the job that blocked us
  const q = useQuery({
    queryKey: ["jobs-current"],
    queryFn: () =>
      api<Job>("/jobs/current").catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null; // never ran
        throw e;
      }),
    refetchInterval: (query) => (query.state.data?.status === "running" ? 2000 : false),
  });
  const job = q.data ?? null;
  const running = job?.status === "running";
  const start = useMutation({
    mutationFn: () => api<Job>("/jobs", { method: "POST", body: JSON.stringify({ kind: "crawl" }) }),
    onSuccess: (j) => {
      setRefused(null);
      qc.setQueryData(["jobs-current"], j);
    },
    onError: (e) => {
      if (e instanceof ApiError && e.status === 409) {
        setRefused(String(e.details.started_at ?? ""));
        void qc.invalidateQueries({ queryKey: ["jobs-current"] }); // pick up the running job
      }
    },
  });
  useEffect(() => {
    if (job && !running) void qc.invalidateQueries({ queryKey: ["bars-status"] });
  }, [job?.id, running, qc]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!running) setRefused(null);
  }, [running]);
  return { job, running: running || start.isPending, start: () => start.mutate(), refused };
}
