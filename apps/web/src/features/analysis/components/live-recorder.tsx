"use client";

import { useState } from "react";
import { Loader2, Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useLiveTranscription, type LiveLanguage } from "../use-live-transcription";
import { Results } from "./results";

const LANGUAGES: { value: LiveLanguage; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "fr", label: "Français" },
  { value: "en", label: "English" },
];

export function LiveRecorder() {
  const live = useLiveTranscription();
  const [language, setLanguage] = useState<LiveLanguage>("auto");
  const isListening = live.status === "listening";
  const isBusy = live.status === "connecting" || live.status === "finishing";

  let caption = "Tap to start speaking";
  if (live.status === "connecting") caption = "Connecting…";
  if (isListening) caption = live.speaking ? "Hearing you…" : "Listening… tap to stop";
  if (live.status === "finishing") caption = "Finishing up…";

  return (
    <div className="space-y-8">
      <div className="flex flex-col items-center gap-5 rounded-2xl border bg-card px-6 py-10 shadow-sm">
        <div className="text-center">
          <p className="font-serif text-6xl tracking-tight tabular-nums">{live.totalWords}</p>
          <p className="mt-1 text-xs uppercase tracking-wider text-muted-foreground">words</p>
        </div>

        <Button
          type="button"
          size="icon"
          onClick={isListening ? live.stop : () => void live.start(language)}
          disabled={isBusy}
          aria-label={isListening ? "Stop recording" : "Start recording"}
          className={cn(
            "size-20 rounded-full transition-colors",
            live.speaking && "bg-destructive hover:bg-destructive/90",
          )}
        >
          {isBusy ? (
            <Loader2 className="size-7 animate-spin" />
          ) : isListening ? (
            <Square className="size-6" />
          ) : (
            <Mic className="size-7" />
          )}
        </Button>

        <p role="status" className="text-sm text-muted-foreground">
          {caption}
        </p>

        {live.status === "idle" && (
          <div className="flex gap-2" role="group" aria-label="Language">
            {LANGUAGES.map(({ value, label }) => (
              <Button
                key={value}
                type="button"
                size="sm"
                variant={language === value ? "default" : "outline"}
                onClick={() => setLanguage(value)}
              >
                {label}
              </Button>
            ))}
          </div>
        )}

        {live.error && (
          <p role="alert" className="max-w-md text-center text-sm text-destructive">
            {live.error}
          </p>
        )}
      </div>

      {live.segments.length > 0 && (
        <div className="space-y-2 rounded-xl border bg-card p-5">
          <p className="text-xs uppercase tracking-wider text-muted-foreground">
            Transcript{live.result ? ` · ${live.result.audio_seconds}s` : ""}
          </p>
          <p className="text-sm leading-relaxed">{live.segments.join(" ")}</p>
        </div>
      )}

      {live.result && <Results result={live.result} />}
    </div>
  );
}