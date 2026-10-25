import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, describe, expect, it } from "vitest";
import "../../i18n";
import raw from "./fixtures/envelope-001.json";
import { InfoButton } from "./HowComputed";
import { isFigure, type Figure, type WhatIfEnvelope } from "./result";

// JSON imports widen literals (unit: string), so `satisfies` cannot hold; a cast keeps the shape check.
const env = raw as WhatIfEnvelope;

beforeAll(() => {
  // jsdom has no <dialog> modal support
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); this.dispatchEvent(new Event("close")); };
});

const leaves = (x: unknown, key = ""): [string, Figure][] =>
  isFigure(x) ? [[key, x]]
  : x && typeof x === "object" ? Object.entries(x).flatMap(([k, v]) => leaves(v, k)) : [];

describe("HowComputed", () => {
  it("shows the liquidation breakdown and the approximate paragraph", async () => {
    const f = env.result.value.liquidation_vnd;
    render(<InfoButton figure={f} envelope={env} name="liquidation_vnd" />);
    await userEvent.click(screen.getByRole("button", { name: /Cách tính|How computed/ }));
    const d = screen.getByRole("dialog");
    for (const s of ["635.975", "100.000", "15.000", "10.000", "10.610.975 ₫", "2026.10.15", "source_adjusted", "VN§5"])
      expect(within(d).getAllByText(new RegExp(s.replace(/[.§₫]/g, "\\$&"))).length).toBeGreaterThan(0);
    expect(within(d).getByText(/giá đã điều chỉnh/)).toBeInTheDocument();
  });

  it("omits the approximate paragraph when approximate is false", async () => {
    render(<InfoButton figure={env.result.value.liquidation_vnd} envelope={{ ...env, approximate: false }} name="liquidation_vnd" />);
    await userEvent.click(screen.getByRole("button"));
    expect(screen.queryByText(/giá đã điều chỉnh/)).toBeNull();
  });

  it("every figure lists every how.inputs key", async () => {
    const all = leaves(env.result);
    expect(all.length).toBeGreaterThan(10);
    for (const [k, f] of all) {
      const { unmount } = render(<InfoButton figure={f} envelope={env} name={k} />);
      await userEvent.click(screen.getByRole("button"));
      const d = screen.getByRole("dialog");
      for (const input of Object.keys(f.how.inputs)) expect(within(d).getByText(input)).toBeInTheDocument();
      unmount();
    }
  });

  it("Esc closes and focus returns to the (i) button", async () => {
    render(<InfoButton figure={env.result.position.cash} envelope={env} name="cash" />);
    const btn = screen.getByRole("button");
    await userEvent.click(btn);
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(btn).toHaveFocus();
  });

  it("drawer opened from a headline cell does not inherit its weight or alignment", async () => {
    render(<dl className="sc-card"><dd className="headline"><InfoButton figure={env.result.value.liquidation_vnd} envelope={env} name="liquidation_vnd" /></dd></dl>);
    await userEvent.click(screen.getByRole("button"));
    const note = screen.getByText(/giá đã điều chỉnh/);
    const cs = getComputedStyle(note);
    expect(cs.fontWeight).toBe("400");
    expect(cs.textAlign).not.toBe("right");
    expect(getComputedStyle(note.closest("dialog")!.querySelector("code.formula")!).display).toBe("block");
  });
});
