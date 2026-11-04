import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export type Period = "day" | "month" | "year";
export type Stats = components["schemas"]["StatsResponse"];

export function useStats(period: Period) {
  return useQuery({
    queryKey: ["stats", period],
    queryFn: async (): Promise<Stats> => {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const { data, error } = await api.GET("/stats", {
        params: { query: { period, timezone } },
      });
      if (error || !data) throw new Error("Could not load stats");
      return data;
    },
    placeholderData: keepPreviousData,
  });
}