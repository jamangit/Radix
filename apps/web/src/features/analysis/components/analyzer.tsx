"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAnalyze, type AnalyzeRequest } from "../use-analyze";
import { Results } from "./results";

type Language = NonNullable<AnalyzeRequest["language"]>;

const LANGUAGES: { value: Language; label: string }[] = [
  { value: "fr", label: "Français" },
  { value: "en", label: "English" },
];

export function Analyzer() {
  const [text, setText] = useState("");
  const [language, setLanguage] = useState<Language>("fr");
  const mutation = useAnalyze();

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
          <Button disabled={!canSubmit} onClick={() => mutation.mutate({ text, language })}>
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

      {mutation.data && <Results result={mutation.data} />}
    </div>
  );
}