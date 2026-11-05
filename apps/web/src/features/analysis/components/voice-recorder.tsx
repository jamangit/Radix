"use client";

import { Loader2, Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useRecorder } from "../use-recorder";
import { useTranscribe } from "../use-transcribe";
import { Results } from "./results";

function formatTime(total: number): string {
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function VoiceRecorder() {
  const recorder = useRecorder();
  const mutation = useTranscribe();
  const isRecording = recorder.status === "recording";
  const errorMessage = recorder.error ?? (mutation.error ? mutation.error.message : null);

  const toggle = async () => {
    if (isRecording) {
      const audio = await recorder.stop();
      if (audio && audio.size > 0) mutation.mutate(audio);
      return;
    }
    mutation.reset();
    await recorder.start();
  };

  let caption = "Tap to start speaking";
  if (isRecording) caption = `Recording… ${formatTime(recorder.seconds)} · tap to stop`;
  if (mutation.isPending) caption = "Transcribing… this can take a few seconds";

  return (
    <div className="space-y-8">
      <div className="flex flex-col items-center gap-4 rounded-2xl border bg-card px-6 py-12 shadow-sm">
        <Button
          type="button"
          size="icon"
          onClick={toggle}
          disabled={mutation.isPending}
          aria-label={isRecording ? "Stop recording" : "Start recording"}
          className={cn(
            "size-20 rounded-full",
            isRecording && "animate-pulse bg-destructive hover:bg-destructive/90",
          )}
        >
          {mutation.isPending ? (
            <Loader2 className="size-7 animate-spin" />
          ) : isRecording ? (
            <Square className="size-6" />
          ) : (
            <Mic className="size-7" />
          )}
        </Button>
        <p role="status" className="text-sm text-muted-foreground">
          {caption}
        </p>
        {errorMessage && (
          <p role="alert" className="text-sm text-destructive">
            {errorMessage}
          </p>
        )}
      </div>

      {mutation.data && (
        <>
          <div className="space-y-2 rounded-xl border bg-card p-5">
            <p className="text-xs uppercase tracking-wider text-muted-foreground">
              Transcript · {mutation.data.audio_seconds}s · {mutation.data.language.toUpperCase()}
            </p>
            <p className="text-sm leading-relaxed">{mutation.data.transcript}</p>
          </div>
          <Results result={mutation.data} />
        </>
      )}
    </div>
  );
}