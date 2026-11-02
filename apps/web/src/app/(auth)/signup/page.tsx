import Link from "next/link";
import { SignupForm } from "@/features/auth/components/signup-form";

export default function SignupPage() {
  return (
    <>
      <div className="mb-8 space-y-2 text-center">
        <h1 className="font-serif text-2xl tracking-tight">Create your account</h1>
        <p className="text-sm text-muted-foreground">Start measuring the words you speak.</p>
      </div>
      <div className="rounded-2xl border bg-card p-6 shadow-sm">
        <SignupForm />
      </div>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-foreground underline-offset-4 hover:underline">
          Sign in
        </Link>
      </p>
    </>
  );
}