import { formatDate, formatDateTime, formatPct, formatPp, formatVnd, parseVndInput } from "./format";

test("formatVnd", () => {
  expect(formatVnd(10610975)).toBe("10.610.975 ₫");
  expect(formatVnd("10000000")).toBe("10.000.000 ₫");
  expect(formatVnd(-19847507)).toBe("−19.847.507 ₫");
  expect(formatVnd("0")).toBe("0 ₫");
});
test("formatPct: sign always, 2 dp, U+2212 for negatives, none for zero", () => {
  expect(formatPct("6.1098")).toBe("+6,11 %");
  expect(formatPct("-2.8338")).toBe("−2,83 %");
  expect(formatPct("0.0000")).toBe("0,00 %");
  expect(formatPct("1.005")).toBe("+1,01 %"); // float toFixed would give 1.00
  expect(formatPct("-0.0004")).toBe("0,00 %");
});
test("formatPp", () => {
  expect(formatPp("1.1098", "vi")).toBe("+1,11 điểm %");
  expect(formatPp("1.1098", "en")).toBe("+1,11 pp");
});
test("dates", () => {
  expect(formatDate("2026-10-23")).toBe("23/10/2026");
  expect(formatDateTime("2026-10-23T15:42:00+07:00")).toBe("23/10/2026 15:42");
  expect(formatDateTime("2026-10-23T23:30:00Z")).toBe("24/10/2026 06:30");
});
test("parseVndInput", () => {
  expect(parseVndInput("10.000.000")).toBe(10000000);
  expect(parseVndInput("")).toBeNull();
});
