import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import "../../i18n";
import { Sparkline } from "./Sparkline";

const pts = [
  { date: "2025-10-12", market_value: 10000000, invested: 10000000 },
  { date: "2025-10-13", market_value: 9985975, invested: 10000000 },
  { date: "2025-10-14", market_value: 10800000, invested: 10000000 },
];
const step = [
  ...pts, { date: "2025-10-15", market_value: 10900000, invested: 11000000 },
  { date: "2025-10-16", market_value: 11000000, invested: 11000000 },
];

describe("Sparkline", () => {
  it("renders nothing for empty points", () => {
    const { container } = render(<Sparkline points={[]} symbol="FPT" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("maps lowest value to bottom padding (height 48, pad 4 -> y 44)", () => {
    const { container } = render(<Sparkline points={pts} symbol="FPT" />);
    // hand-computed: span 814025; y = 44 - (v-9985975)*40/814025
    expect(container.querySelector("polyline")!.getAttribute("points")).toBe("4,43.31 150,44 296,4");
    expect(container.querySelector("path")!.getAttribute("d")).toBe("M4 43.31 H296"); // constant: no vertical
  });

  it("invested step has exactly one vertical segment", () => {
    const { container } = render(<Sparkline points={step} symbol="FPT" />);
    expect(container.querySelector("path")!.getAttribute("d")!.match(/V/g)).toHaveLength(1);
  });

  it("names the curve with vi-VN max and min", () => {
    render(<Sparkline points={pts} symbol="FPT" />);
    expect(screen.getByLabelText(
      "Đường giá trị FPT từ 12/10/2025 đến 14/10/2025, cao nhất 10.800.000 ₫, thấp nhất 9.985.975 ₫",
    )).toBeInTheDocument();
  });

  it("focus then ArrowRight moves the status to the second date", async () => {
    render(<Sparkline points={pts} symbol="FPT" />);
    await userEvent.tab();
    expect(screen.getByRole("status")).toHaveTextContent("12/10/2025 · 10.000.000 ₫");
    await userEvent.keyboard("{ArrowRight}");
    expect(screen.getByRole("status")).toHaveTextContent("13/10/2025 · 9.985.975 ₫");
  });
});
