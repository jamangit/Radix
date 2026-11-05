import { expect, test } from "@playwright/test";

test("a new user can sign up, analyze a text and sign out", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;
  const password = "correct-horse-battery";

  await page.goto("/signup");
  await page.getByLabel("Name", { exact: true }).fill("E2E User");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByRole("heading", { name: "Your words" })).toBeVisible();
  await page.getByRole("button", { name: "Type", exact: true }).click();

  await page
    .getByPlaceholder("Paste or write a text here…")
    .fill("Le chat mange la souris. Le chat dort.");
  await page.getByRole("button", { name: "Analyze", exact: true }).click();
  await expect(page.getByText("Analyzed as French")).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login/);
});

test("login shows an error for wrong credentials", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email", { exact: true }).fill("nobody@example.com");
  await page.getByLabel("Password", { exact: true }).fill("wrong-password");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page.locator("form").getByRole("alert")).toHaveText("Invalid email or password.");
});