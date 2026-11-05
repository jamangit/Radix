import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { components } from "@/lib/api/schema";

export type TranscribeResult = components["schemas"]["TranscribeResponse"];

function extensionFor(mimeType: string): string {
  return mimeType.includes("mp4") ? "m4a" : "webm";
}

export function useTranscribe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (audio: Blob): Promise<TranscribeResult> => {
      const form = new FormData();
      form.append("audio", audio, `recording.${extensionFor(audio.type)}`);

      const response = await fetch("/api/transcribe", { method: "POST", body: form });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
        throw new Error(typeof body?.detail === "string" ? body.detail : "Transcription failed");
      }
      return (await response.json()) as TranscribeResult;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["stats"] }),
  });
}