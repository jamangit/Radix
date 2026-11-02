import type { LoginInput, SignupInput } from "@/features/auth/schemas";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Temporary mock: replaced by the generated OpenAPI client once the FastAPI backend exists.
export async function login(input: LoginInput) {
  await wait(700);
  return { user: { email: input.email } };
}

export async function signup(input: SignupInput) {
  await wait(900);
  return { user: { email: input.email, name: input.name } };
}