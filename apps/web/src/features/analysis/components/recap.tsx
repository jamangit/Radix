"use client";

import { useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { Button } from "@/components/ui/button";
import { useStats, type Period } from "../use-stats";
import { Stat } from "./stat";
import { TopWordsChart } from "./top-words-chart";
import { cn } from "@/lib/utils";

const PERIODS: { value: Period; label: string }[] = [
  { value: "day", label: "Today" },
  { value: "month", label: "This month" },
  { value: "year", label: "This year" },
];

export function Recap() {
  const [period, setPeriod] = useState<Period>("day");
  const { data } = useStats(period);
  const format = new Intl.NumberFormat("en-US");
  const isEmpty = data !== undefined && data.analyses === 0;

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-serif text-xl tracking-tight">Your recap</h2>
        <div className="flex gap-2" role="group" aria-label="Period">
          {PERIODS.map(({ value, label }) => (
            <Button
              key={value}
              size="sm"
              variant={period === value ? "default" : "outline"}
              onClick={() => setPeriod(value)}
            >
              {label}
            </Button>
          ))}
        </div>
      </div>

        <div className={cn("grid gap-4 sm:grid-cols-3", period !== "day" && "lg:grid-cols-4")}>
            <Stat label="Words" value={data ? format.format(data.total_words) : "–"} />
            <Stat label="Vocabulary" value={data ? format.format(data.vocabulary_size) : "–"} />
            <Stat label="Analyses" value={data ? format.format(data.analyses) : "–"} />
            {period !== "day" && (
            <Stat
                label="Words per day"
                value={data ? format.format(data.words_per_day) : "–"}
                hint={
                data
                    ? `over ${data.elapsed_days} ${data.elapsed_days === 1 ? "day" : "days"}`
                    : undefined
                }
            />
            )}
        </div>

      {isEmpty ? (
        <p className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">
          Nothing analyzed in this period yet. Analyze a text below to start your recap.
        </p>
      ) : (
        data && (
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-xl border bg-card p-5">
              <h3 className="mb-4 font-serif text-lg tracking-tight">Words over time</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.series} accessibilityLayer={false}>
                    <XAxis
                      dataKey="label"
                      tickLine={false}
                      axisLine={false}
                      interval="preserveStartEnd"
                      minTickGap={16}
                    />
                    <Tooltip cursor={{ fill: "var(--muted)" }} />
                    <Bar dataKey="words" fill="var(--primary)" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-xl border bg-card p-5">
              <h3 className="mb-4 font-serif text-lg tracking-tight">Most used words</h3>
              <TopWordsChart data={data.top_words} />
            </div>
          </div>
        )
      )}
    </section>
  );
}