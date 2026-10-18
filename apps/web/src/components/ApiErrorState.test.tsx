import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "../i18n";
import { ApiErrorState } from "./ApiErrorState";

test("shows the message and retries on click", async () => {
  const onRetry = vi.fn();
  render(<ApiErrorState onRetry={onRetry} />);
  expect(screen.getByRole("alert")).toHaveTextContent(/docker compose/);
  await userEvent.click(screen.getByRole("button", { name: /\S/ }));
  expect(onRetry).toHaveBeenCalledOnce();
});
