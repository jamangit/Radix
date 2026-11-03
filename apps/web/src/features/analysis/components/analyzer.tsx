"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAnalyze, type AnalyzeRequest } from "../use-analyze";
import { Results } from "./results";

type Language = NonNullable<AnalyzeRequest["language"]>;
type LanguageChoice = Language | "auto";

const LANGUAGE_NAMES: Record<Language, string> = { fr: "French", en: "English" };

const CHOICES: { value: LanguageChoice; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "fr", label: "Français" },
  { value: "en", label: "English" },
];

export function Analyzer() {
  const [text, setText] = useState("");
  const [choice, setChoice] = useState<LanguageChoice>("auto");
  const mutation = useAnalyze();
  const result = mutation.data;

  const run = (next: LanguageChoice) => {
    setChoice(next);
    mutation.mutate({ text, language: next === "auto" ? null : next });
  };

  const canSubmit = text.trim().length > 0 && !mutation.isPending;

  return (
    <div className="space-y-8">
      <div className="space-y-4 rounded-2xl border bg-card p-6 shadow-sm">
        <Textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Paste or write a text here…"
          className="min-h-44 resize-y"
          maxLength={50_000}
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex gap-2" role="group" aria-label="Language">
            {CHOICES.map(({ value, label }) => (
              <Button
                key={value}
                type="button"
                size="sm"
                variant={choice === value ? "default" : "outline"}
                onClick={() => setChoice(value)}
              >
                {label}
              </Button>
            ))}
          </div>
          <Button disabled={!canSubmit} onClick={() => run(choice)}>
            {mutation.isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
            Analyze
          </Button>
        </div>
        {mutation.isError && (
          <p role="alert" className="text-sm text-destructive">
            Something went wrong. Please try again.
          </p>
        )}
      </div>

      {result?.language_mismatch && (
        <div
          role="status"
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-accent px-4 py-3 text-sm"
        >
          <p>
            This text looks like {LANGUAGE_NAMES[result.detected_language]}, but it was analyzed as{" "}
            {LANGUAGE_NAMES[result.language]}.
          </p>
          <Button size="sm" variant="outline" onClick={() => run(result.detected_language)}>
            Analyze as {LANGUAGE_NAMES[result.detected_language]}
          </Button>
        </div>
      )}

      {result && (
        <>
          <p className="text-xs uppercase tracking-wider text-muted-foreground">
            Analyzed as {LANGUAGE_NAMES[result.language]}
          </p>
          <Results result={result} />
        </>
      )}
    </div>
  );
}