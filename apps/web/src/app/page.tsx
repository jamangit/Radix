"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

export default function SplashPage() {
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(() => router.replace("/login"), 2600);
    return () => clearTimeout(timer);
  }, [router]);

  return (
    <main className="relative flex min-h-dvh items-center justify-center overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_50%_at_50%_40%,color-mix(in_oklab,var(--primary)_10%,transparent),transparent)]" />
      <div className="relative text-center">
        <motion.h1
          initial={{ opacity: 0, y: 12, filter: "blur(8px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
          className="font-serif text-6xl tracking-tight sm:text-7xl"
        >
          Radix
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9, duration: 0.9 }}
          className="mt-4 text-xs uppercase tracking-[0.3em] text-muted-foreground"
        >
          Every word counts
        </motion.p>
      </div>
    </main>
  );
}