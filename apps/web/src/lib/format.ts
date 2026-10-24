// All numbers are vi-VN in both UI languages (ux/app-shell.md); no money math here, formatting only.
const NUM = new Intl.NumberFormat("vi-VN");
const MINUS = "−"; // U+2212, not hyphen
const TZ = "Asia/Ho_Chi_Minh";

export const formatVnd = (n: number | string): string => {
  const v = Number(n);
  return `${v < 0 ? MINUS : ""}${NUM.format(Math.abs(v))} ₫`;
};

/** Round a decimal string to 2 dp half-away-from-zero without float math: "+6,11". */
function signed2(s: string): string {
  const m = /^(-?)(\d+)(?:\.(\d*))?$/.exec(s.trim());
  if (!m) return s;
  const frac = ((m[3] ?? "") + "000").slice(0, 3);
  let scaled = BigInt(m[2] + frac.slice(0, 2));
  if (frac[2] >= "5") scaled += 1n;
  const body = `${NUM.format(scaled / 100n)},${String(scaled % 100n).padStart(2, "0")}`;
  if (scaled === 0n) return body;
  return (m[1] ? MINUS : "+") + body;
}

export const formatPct = (s: string): string => `${signed2(s)} %`;
export const formatPp = (s: string, lang: string): string => `${signed2(s)} ${lang === "en" ? "pp" : "điểm %"}`;

/** Date-only strings are split, never passed to `new Date` (time-zone shift). */
export function formatDate(d: string): string {
  const [y, m, day] = d.split("-");
  return `${day}/${m}/${y}`;
}

export function formatDateTime(iso: string): string {
  const p = Object.fromEntries(
    new Intl.DateTimeFormat("en-GB", {
      timeZone: TZ, day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit", hourCycle: "h23",
    }).formatToParts(new Date(iso)).map((x) => [x.type, x.value]),
  );
  return `${p.day}/${p.month}/${p.year} ${p.hour}:${p.minute}`;
}

/** "10.000.000" -> 10000000; no digits -> null. */
export function parseVndInput(s: string): number | null {
  const d = s.replace(/\D/g, "");
  return d ? Number(d) : null;
}
