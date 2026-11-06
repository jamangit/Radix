"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Analyzer } from "./analyzer";
import { LiveRecorder } from "./live-recorder";

type Mode = "voice" | "text";

export function AnalyzeSection() {
  const [mode, setMode] = useState<Mode>("voice");

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-serif text-xl tracking-tight">Analyze</h2>
        <div className="flex gap-2" role="group" aria-label="Input mode">
          <Button size="sm" variant={mode === "voice" ? "default" : "outline"} onClick={() => setMode("voice")}>
            Speak
          </Button>
          <Button size="sm" variant={mode === "text" ? "default" : "outline"} onClick={() => setMode("text")}>
            Type
          </Button>
        </div>
      </div>
      {mode === "voice" ? <LiveRecorder /> : <Analyzer />}
    </section>
  );
}