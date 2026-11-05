import { describe, expect, it } from "vitest";
import { loginSchema, signupSchema } from "./schemas";

describe("loginSchema", () => {
  it("rejects an invalid email", () => {
    const result = loginSchema.safeParse({ email: "not-an-email", password: "secret" });

    expect(result.success).toBe(false);
  });
});

describe("signupSchema", () => {
  const valid = {
    name: "Ada Lovelace",
    email: "ada@example.com",
    password: "correct-horse",
    confirmPassword: "correct-horse",
  };

  it("accepts valid input", () => {
    expect(signupSchema.safeParse(valid).success).toBe(true);
  });

  it("rejects a password shorter than 8 characters", () => {
    const result = signupSchema.safeParse({ ...valid, password: "short", confirmPassword: "short" });

    expect(result.success).toBe(false);
  });

  it("reports a mismatched confirmation on the right field", () => {
    const result = signupSchema.safeParse({ ...valid, confirmPassword: "something-else" });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0]?.path).toEqual(["confirmPassword"]);
    }
  });
});