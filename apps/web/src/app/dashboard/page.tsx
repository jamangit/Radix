import { AuthGate } from "@/features/auth/components/auth-gate";
import { UserMenu } from "@/features/auth/components/user-menu";
import { AnalyzeSection } from "@/features/analysis/components/analyze-section";
import { Recap } from "@/features/analysis/components/recap";

export default function DashboardPage() {
  return (
    <AuthGate>
      <main className="mx-auto w-full max-w-5xl space-y-12 px-4 py-12">
        <header className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <h1 className="font-serif text-3xl tracking-tight">Your words</h1>
            <p className="text-sm text-muted-foreground">
              Track how much you speak and how rich your vocabulary is.
            </p>
          </div>
          <UserMenu />
        </header>

        <Recap />

        <AnalyzeSection />
      </main>
    </AuthGate>
  );
}