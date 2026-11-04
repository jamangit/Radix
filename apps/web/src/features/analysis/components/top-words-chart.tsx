"use client";

import { Bar, BarChart, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const MAX_LABEL_LENGTH = 12;

function truncate(word: string): string {
  return word.length > MAX_LABEL_LENGTH ? `${word.slice(0, MAX_LABEL_LENGTH - 1)}…` : word;
}

type WordTickProps = { x?: number; y?: number; payload?: { value: string } };

function WordTick({ x = 0, y = 0, payload }: WordTickProps) {
  const word = payload?.value ?? "";

  return (
    <text x={x} y={y} dy={4} textAnchor="end" fontSize={13} fill="var(--muted-foreground)">
      <title>{word}</title>
      {truncate(word)}
    </text>
  );
}

export function TopWordsChart({ data }: { data: { word: string; count: number }[] }) {
  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 32 }} accessibilityLayer={false}>
          <XAxis type="number" hide domain={[0, "dataMax"]} allowDecimals={false} />
          <YAxis
            type="category"
            dataKey="word"
            width={110}
            interval={0}
            tickLine={false}
            axisLine={false}
            tick={<WordTick />}
          />
          <Tooltip cursor={{ fill: "var(--muted)" }} />
          <Bar dataKey="count" fill="var(--primary)" radius={[0, 6, 6, 0]}>
            <LabelList dataKey="count" position="right" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}