import type { AnalysisResult } from "../use-analyze";
import { TopWordsChart } from "./top-words-chart";
import { Stat } from "./stat";

type ResultData = Pick<
  AnalysisResult,
  "total_words" | "unique_words" | "lexical_diversity" | "top_words" | "rare_words"
>;

export function Results({ result }: { result: ResultData }) {
  const format = new Intl.NumberFormat("en-US");

  return (
    <section className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Words" value={format.format(result.total_words)} />
        <Stat label="Unique words" value={format.format(result.unique_words)} />
        <Stat label="Lexical diversity" value={`${Math.round(result.lexical_diversity * 100)}%`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border bg-card p-5">
          <h2 className="mb-4 font-serif text-lg tracking-tight">Most used words</h2>
          {result.top_words.length > 0 ? (
            <TopWordsChart data={result.top_words} />
          ) : (
            <p className="text-sm text-muted-foreground">Not enough meaningful words yet.</p>
          )}
        </div>

        <div className="rounded-xl border bg-card p-5">
          <h2 className="mb-4 font-serif text-lg tracking-tight">Rare words</h2>
          {result.rare_words.length > 0 ? (
            <ul className="divide-y">
              {result.rare_words.map((item) => (
                <li key={item.word} className="flex items-center justify-between py-2.5 text-sm">
                  <span className="font-medium">{item.word}</span>
                  <span className="text-muted-foreground">rarity {item.zipf.toFixed(1)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No unusual words found in this text.</p>
          )}
        </div>
      </div>
    </section>
  );
}