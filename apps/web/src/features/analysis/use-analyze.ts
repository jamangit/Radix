import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export type AnalysisResult = components["schemas"]["AnalyzeResponse"];
export type AnalyzeRequest = components["schemas"]["AnalyzeRequest"];

export function useAnalyze() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: AnalyzeRequest): Promise<AnalysisResult> => {
      const { data, error } = await api.POST("/analyze", { body });
      if (error || !data) throw new Error("Analysis failed");
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["stats"] }),
  });
}