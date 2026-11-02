import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="relative grid min-h-dvh place-items-center px-4 py-12">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(50%_40%_at_50%_0%,color-mix(in_oklab,var(--primary)_8%,transparent),transparent)]" />
      <div className="relative w-full max-w-sm">
        <Link href="/login" className="mb-10 block text-center font-serif text-3xl tracking-tight">
          Radix
        </Link>
        {children}
      </div>
    </main>
  );
}