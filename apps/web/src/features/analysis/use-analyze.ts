import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export type AnalysisResult = components["schemas"]["AnalysisResult"];
export type AnalyzeRequest = components["schemas"]["AnalyzeRequest"];

export function useAnalyze() {
  return useMutation({
    mutationFn: async (body: AnalyzeRequest): Promise<AnalysisResult> => {
      const { data, error } = await api.POST("/analyze", { body });
      if (error || !data) throw new Error("Analysis failed");
      return data;
    },
  });
}