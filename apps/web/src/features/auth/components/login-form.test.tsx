import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthError, login } from "@/lib/api/auth";
import { LoginForm } from "./login-form";

const { push } = vi.hoisted(() => ({ push: vi.fn() }));

vi.mock("next/navigation", () => ({ useRouter: () => ({ push, replace: vi.fn() }) }));
vi.mock("@/lib/api/auth", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api/auth")>()),
  login: vi.fn(),
}));

const loginMock = vi.mocked(login);

function renderForm() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <LoginForm />
    </QueryClientProvider>,
  );
}

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows validation errors and does not call the API", async () => {
    const user = userEvent.setup();
    renderForm();

    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Enter a valid email address")).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it("signs in and redirects to the dashboard", async () => {
    const user = userEvent.setup();
    loginMock.mockResolvedValue({ id: "1", email: "ada@example.com", name: "Ada" });
    renderForm();

    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Password"), "correct-horse");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/dashboard"));
    expect(loginMock.mock.calls[0]?.[0]).toEqual({
      email: "ada@example.com",
      password: "correct-horse",
    });
  });

  it("displays the error returned by the API", async () => {
    const user = userEvent.setup();
    loginMock.mockRejectedValue(new AuthError("Invalid email or password."));
    renderForm();

    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
    expect(push).not.toHaveBeenCalled();
  });
});