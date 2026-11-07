"use client";

import { useState } from "react";
import { Loader2, Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { METER_FLOOR_DB } from "../audio-quality";
import { useLiveTranscription, type LiveLanguage } from "../use-live-transcription";
import { Results } from "./results";

const LANGUAGES: { value: LiveLanguage; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "fr", label: "Français" },
  { value: "en", label: "English" },
];

// Same default as the server's QUALITY_MIN_LEVEL_DB: below it, the voice is considered faint.
const FAINT_LEVEL_DB = -45;

function LevelMeter({ level }: { level: number }) {
  const percent = Math.max(0, Math.min(100, ((level - METER_FLOOR_DB) / -METER_FLOOR_DB) * 100));

  return (
    <div
      role="meter"
      aria-label="Microphone level"
      aria-valuemin={METER_FLOOR_DB}
      aria-valuemax={0}
      aria-valuenow={Math.round(level)}
      className="h-1.5 w-48 overflow-hidden rounded-full bg-muted"
    >
      <div
        className={cn(
          "h-full rounded-full transition-[width] duration-100",
          level < FAINT_LEVEL_DB ? "bg-muted-foreground/50" : "bg-primary",
        )}
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}

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

        {isListening && <LevelMeter level={live.level} />}

        {live.hint && (
          <p
            role="status"
            className="max-w-md rounded-lg border bg-accent px-4 py-2 text-center text-sm"
          >
            {live.hint}
          </p>
        )}

        {live.quality && (
          <p className="text-xs text-muted-foreground">
            Last phrase · level {live.quality.level_db} dB · signal-to-noise {live.quality.snr_db} dB
          </p>
        )}

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