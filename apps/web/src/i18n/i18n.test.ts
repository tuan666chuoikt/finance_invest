import { vi } from "vitest";
import en from "./en.json";
import viJson from "./vi.json";

const srcFiles = import.meta.glob("../**/*.{ts,tsx}", { query: "?raw", import: "default", eager: true }) as Record<string, string>;

test("key sets are identical and non-empty", () => {
  const k = (o: object) => Object.keys(o).sort();
  expect(k(en).length).toBeGreaterThan(0);
  expect(k(viJson)).toEqual(k(en));
});

test("every literal t('key') in src exists in both files", () => {
  const used = new Set<string>();
  for (const [f, src] of Object.entries(srcFiles)) {
    if (f.includes(".test.")) continue;
    for (const m of src.matchAll(/\bt\(\s*['"]([\w.-]+)['"]/g)) used.add(m[1]);
  }
  const missing = [...used].filter((key) => !(key in en) || !(key in viJson));
  expect(missing).toEqual([]);
});

test("first start is vi; changeLanguage persists and sets <html lang>", async () => {
  localStorage.clear();
  vi_reset();
  const { default: i18n } = await import("./index");
  expect(i18n.language).toBe("vi");
  expect(i18n.t("no.such.key")).toBe("no.such.key");
  await i18n.changeLanguage("en");
  expect(localStorage.getItem("finvest.lang")).toBe("en");
  expect(document.documentElement.lang).toBe("en");
});

function vi_reset() {
  vi.resetModules();
}
