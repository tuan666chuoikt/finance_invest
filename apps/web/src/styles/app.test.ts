import { describe, expect, it } from "vitest";

const rules = () =>
  [...document.styleSheets].flatMap((s) => [...s.cssRules]).map((r) => r.cssText);

describe("app.css base elements", () => {
  it("styles a bare button at 32px", () => {
    const b = document.body.appendChild(document.createElement("button"));
    expect(getComputedStyle(b).height).toBe("32px");
    b.remove();
  });

  it("maps .btn-primary to the light --primary (#1f5fbf = rgb(31, 95, 191))", () => {
    // jsdom ignores media queries and var(), so read the plain rules from the sheet
    const top = [...document.styleSheets].flatMap((s) => [...s.cssRules]).filter((r): r is CSSStyleRule => r instanceof CSSStyleRule);
    const btn = top.find((r) => r.selectorText === ".btn-primary");
    expect(btn?.style.getPropertyValue("background")).toBe("var(--primary)");
    expect(top.find((r) => r.selectorText === ":root")?.style.getPropertyValue("--primary")).toBe("#1f5fbf");
  });

  it("has a :focus-visible ring rule", () => {
    expect(rules().some((t) => t.includes(":focus-visible") && t.includes("outline: 2px solid var(--focus)"))).toBe(true);
  });

  it("keeps the 32px top-bar hit target and nowrap brand/links (base rules)", () => {
    const top = [...document.styleSheets].flatMap((s) => [...s.cssRules]).filter((r): r is CSSStyleRule => r instanceof CSSStyleRule);
    const hit = top.find((r) => r.selectorText?.replace(/\s+/g, " ") === ".tb button, .tb a");
    expect(hit?.style.getPropertyValue("min-height")).toBe("32px");
    expect(top.find((r) => r.selectorText?.replace(/\s+/g, " ") === ".tb-brand, .tb-nav a")?.style.getPropertyValue("white-space")).toBe("nowrap");
  });
});
