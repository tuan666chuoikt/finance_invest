import { useState, type KeyboardEvent, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import { formatDate, formatVnd } from "../../lib/format";

export type CurvePoint = { date: string; market_value: number; invested: number };
type Props = { points: CurvePoint[]; symbol: string; width?: number; height?: number };

const PAD = 4;

export function Sparkline({ points, symbol, width = 300, height = 48 }: Props) {
  const { t } = useTranslation();
  const [active, setActive] = useState<number | null>(null);
  if (points.length === 0) return null;

  const n = points.length;
  const all = points.flatMap((p) => [p.market_value, p.invested]);
  const lo = Math.min(...all);
  const span = Math.max(...all) - lo; // 0 for a flat series: draw a mid-line instead of dividing by 0
  const x = (i: number) => (n === 1 ? width / 2 : PAD + (i * (width - 2 * PAD)) / (n - 1));
  const y = (v: number) => (span === 0 ? height / 2 : height - PAD - ((v - lo) * (height - 2 * PAD)) / span);
  const f = (v: number) => Number(v.toFixed(2));

  const line = points.map((p, i) => `${f(x(i))},${f(y(p.market_value))}`).join(" ");
  // step path: horizontal to the contribution date, then one vertical segment
  const step = points.reduce(
    (d, p, i) => (i === 0 ? `M${f(x(0))} ${f(y(p.invested))}`
      : p.invested !== points[i - 1].invested ? `${d} H${f(x(i))} V${f(y(p.invested))}` : d),
    "",
  ) + ` H${f(x(n - 1))}`;

  const mv = points.map((p) => p.market_value);
  const aria = t("curve.aria", {
    symbol, from: formatDate(points[0].date), to: formatDate(points[n - 1].date),
    max: formatVnd(Math.max(...mv)), min: formatVnd(Math.min(...mv)),
  });

  const onKey = (e: KeyboardEvent) => {
    const to = { ArrowRight: (active ?? 0) + 1, ArrowLeft: (active ?? 0) - 1, Home: 0, End: n - 1 }[e.key];
    if (to === undefined) return;
    e.preventDefault();
    setActive(Math.min(n - 1, Math.max(0, to)));
  };
  const onMove = (e: MouseEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    if (r.width) setActive(Math.round(Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * (n - 1)));
  };

  const cur = active === null ? null : points[active];
  return (
    <div style={{ position: "relative" }}>
      <svg
        viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-label={aria}
        tabIndex={0} style={{ width: "100%", height, display: "block" }}
        onKeyDown={onKey} onFocus={() => setActive((a) => a ?? 0)} onBlur={() => setActive(null)}
        onMouseMove={onMove} onMouseLeave={() => setActive(null)}
      >
        <path d={step} fill="none" stroke="var(--chart-invested, currentColor)" strokeWidth={1}
          strokeDasharray="4 3" opacity={0.7} vectorEffect="non-scaling-stroke" />
        <polyline points={line} fill="none" stroke="var(--chart-line, currentColor)" strokeWidth={2}
          vectorEffect="non-scaling-stroke" />
        {active !== null && <line x1={x(active)} x2={x(active)} y1={0} y2={height} stroke="currentColor" strokeWidth={1} vectorEffect="non-scaling-stroke" />}
      </svg>
      <div role="status" style={{ fontSize: 12, minHeight: "1.2em" }}>
        {cur && `${formatDate(cur.date)} · ${formatVnd(cur.market_value)}`}
      </div>
    </div>
  );
}
