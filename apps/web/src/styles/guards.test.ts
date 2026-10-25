import { describe, expect, it } from "vitest";
import tokensCss from "./tokens.css?raw";

const sources = import.meta.glob("/src/**/*.{ts,tsx,css}", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const files = Object.entries(sources).filter(([p]) => !/\.test\.|\/tokens\.css$|\/test\//.test(p));

const decls = (css: string) => new Map([...css.matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)].map((m) => [m[1].slice(2), m[2].trim()]));
const [lightCss, darkCss = ""] = tokensCss.split("@media (prefers-color-scheme: dark)");
const light = decls(lightCss);
const dark = decls(darkCss);

describe("design-token guards (visual-design §9.3)", () => {
  it("every var(--x) used in src is declared in tokens.css", () => {
    const bad: string[] = [];
    for (const [p, src] of files)
      for (const m of src.matchAll(/var\(--([a-z0-9-]+)/g)) if (!light.has(m[1])) bad.push(`--${m[1]} in ${p}`);
    expect([...new Set(bad)], `undefined tokens:\n${bad.join("\n")}`).toEqual([]);
  });

  it("every colour token has a dark value", () => {
    const missing = [...light].filter(([k, v]) => /^(#|rgb)/.test(v) && !dark.has(k)).map(([k]) => `--${k}`);
    expect(missing, `no dark value for: ${missing.join(", ")}`).toEqual([]);
  });

  it("body font is the sans stack, never serif", () => {
    expect(light.get("font-sans")).toMatch(/^system-ui/);
    // jsdom drops a `font` shorthand holding var(), so read the body rule text
    const body = [...document.styleSheets].flatMap((s) => [...s.cssRules]).find((r) => r instanceof CSSStyleRule && r.selectorText === "body");
    expect(body?.cssText).toMatch(/var\(--font-sans\)|font-family: system-ui/);
    const bad = files.filter(([p, s]) => p.endsWith(".css") && /font-family\s*:[^;]*(?<!sans-)serif/.test(s)).map(([p]) => p);
    expect(bad, `serif font-family in: ${bad.join(", ")}`).toEqual([]);
  });
});
