"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { login } from "@/lib/api/auth";
import { loginSchema, type LoginInput } from "../schemas";
import { Field } from "./field";
import { PasswordInput } from "./password-input";
import { authErrorMessage, login } from "@/lib/api/auth";

export function LoginForm() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({ resolver: zodResolver(loginSchema) });

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: login,
    onSuccess: (user) => {
      queryClient.setQueryData(["me"], user);
      router.push("/dashboard");
    },
  });

  return (
    <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-5" noValidate>
      <Field label="Email" htmlFor="email" error={errors.email?.message}>
        <Input id="email" type="email" autoComplete="email" placeholder="you@example.com" className="h-11" {...register("email")} />
      </Field>
      <Field label="Password" htmlFor="password" error={errors.password?.message}>
        <PasswordInput id="password" autoComplete="current-password" placeholder="••••••••" {...register("password")} />
      </Field>
      {mutation.isError && (
        <p role="alert" className="text-sm text-destructive">
          {authErrorMessage(mutation.error)}
        </p>
      )}
      <Button type="submit" className="h-11 w-full" disabled={mutation.isPending}>
        {mutation.isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
        Sign in
      </Button>
    </form>
  );
}