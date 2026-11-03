"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { signup } from "@/lib/api/auth";
import { signupSchema, type SignupInput } from "../schemas";
import { Field } from "./field";
import { PasswordInput } from "./password-input";
import { authErrorMessage, login } from "@/lib/api/auth";

export function SignupForm() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupInput>({ resolver: zodResolver(signupSchema) });

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: signup,
    onSuccess: (user) => {
      queryClient.setQueryData(["me"], user);
      router.push("/dashboard");
    },
  });

  return (
    <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-5" noValidate>
      <Field label="Name" htmlFor="name" error={errors.name?.message}>
        <Input id="name" autoComplete="name" placeholder="Your name" className="h-11" {...register("name")} />
      </Field>
      <Field label="Email" htmlFor="email" error={errors.email?.message}>
        <Input id="email" type="email" autoComplete="email" placeholder="you@example.com" className="h-11" {...register("email")} />
      </Field>
      <Field label="Password" htmlFor="password" error={errors.password?.message}>
        <PasswordInput id="password" autoComplete="new-password" placeholder="At least 8 characters" {...register("password")} />
      </Field>
      <Field label="Confirm password" htmlFor="confirmPassword" error={errors.confirmPassword?.message}>
        <PasswordInput id="confirmPassword" autoComplete="new-password" placeholder="Repeat your password" {...register("confirmPassword")} />
      </Field>
      {mutation.isError && (
        <p role="alert" className="text-sm text-destructive">
          {authErrorMessage(mutation.error)}
        </p>
      )}
      <Button type="submit" className="h-11 w-full" disabled={mutation.isPending}>
        {mutation.isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
        Create account
      </Button>
    </form>
  );
}