import { Analyzer } from "@/features/analysis/components/analyzer";

export default function DashboardPage() {
  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-12">
      <header className="mb-10 space-y-2">
        <h1 className="font-serif text-3xl tracking-tight">Your words</h1>
        <p className="text-sm text-muted-foreground">Paste a text to see how rich your vocabulary is.</p>
      </header>
      <Analyzer />
    </main>
  );
}