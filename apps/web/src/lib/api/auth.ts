import type { LoginInput, SignupInput } from "@/features/auth/schemas";
import { api } from "./client";

export class AuthError extends Error {}

export function authErrorMessage(error: unknown): string {
  return error instanceof AuthError ? error.message : "Something went wrong. Please try again.";
}

export async function login(input: LoginInput) {
  const { data, response } = await api.POST("/auth/login", { body: input });
  if (!data) {
    throw new AuthError(
      response.status === 401 ? "Invalid email or password." : "Something went wrong. Please try again.",
    );
  }
  return data;
}

export async function signup({ name, email, password }: SignupInput) {
  const { data, response } = await api.POST("/auth/signup", {
    body: { name, email, password },
  });
  if (!data) {
    throw new AuthError(
      response.status === 409
        ? "An account with this email already exists."
        : "Something went wrong. Please try again.",
    );
  }
  return data;
}

export async function logout() {
  await api.POST("/auth/logout");
}

export async function fetchCurrentUser() {
  const { data } = await api.GET("/auth/me");
  return data ?? null;
}