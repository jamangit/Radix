import { AuthGate } from "@/features/auth/components/auth-gate";
import { UserMenu } from "@/features/auth/components/user-menu";
import { Analyzer } from "@/features/analysis/components/analyzer";

export default function DashboardPage() {
  return (
    <AuthGate>
      <main className="mx-auto w-full max-w-5xl px-4 py-12">
        <header className="mb-10 flex items-start justify-between gap-4">
          <div className="space-y-2">
            <h1 className="font-serif text-3xl tracking-tight">Your words</h1>
            <p className="text-sm text-muted-foreground">
              Paste a text to see how rich your vocabulary is.
            </p>
          </div>
          <UserMenu />
        </header>
        <Analyzer />
      </main>
    </AuthGate>
  );
}