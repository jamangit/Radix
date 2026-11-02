import Link from "next/link";
import { LoginForm } from "@/features/auth/components/login-form";

export default function LoginPage() {
  return (
    <>
      <div className="mb-8 space-y-2 text-center">
        <h1 className="font-serif text-2xl tracking-tight">Welcome back</h1>
        <p className="text-sm text-muted-foreground">Sign in to see how your words add up.</p>
      </div>
      <div className="rounded-2xl border bg-card p-6 shadow-sm">
        <LoginForm />
      </div>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        New to Radix?{" "}
        <Link href="/signup" className="font-medium text-foreground underline-offset-4 hover:underline">
          Create an account
        </Link>
      </p>
    </>
  );
}