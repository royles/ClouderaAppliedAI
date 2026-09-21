import { useMemo, useState } from "react";
import { ValueHistoryPoint } from "../api";

type Props = {
  title: string;
  subtitle?: string;
  points: ValueHistoryPoint[];
  loading?: boolean;
  refreshing?: boolean;
  className?: string;
};

function formatPeriodLabel(period: string) {
  if (period.length >= 7) {
    const [y, m] = period.split("-");
    const month = new Date(Number(y), Number(m) - 1, 1).toLocaleString("en-GB", {
      month: "short",
    });
    return `${month} ${y?.slice(2)}`;
  }
  return period;
}

function formatAxisMoney(n: number) {
  if (n >= 1_000_000) return `₪${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `₪${(n / 1_000).toFixed(0)}K`;
  return `₪${n.toFixed(0)}`;
}

function formatTooltipMoney(n: number) {
  return new Intl.NumberFormat("en-IL", {
    style: "currency",
    currency: "ILS",
    maximumFractionDigits: 0,
  }).format(n);
}

function linePath(
  values: number[],
  width: number,
  height: number,
  padX: number,
  padY: number,
  minY: number,
  maxY: number,
): string {
  if (values.length === 0) return "";
  const span = maxY - minY || 1;
  const stepX = values.length > 1 ? (width - padX * 2) / (values.length - 1) : 0;
  return values
    .map((v, i) => {
      const x = padX + i * stepX;
      const y = padY + (height - padY * 2) * (1 - (v - minY) / span);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

function pointCoords(
  index: number,
  value: number,
  count: number,
  width: number,
  height: number,
  padX: number,
  padY: number,
  minY: number,
  maxY: number,
) {
  const span = maxY - minY || 1;
  const stepX = count > 1 ? (width - padX * 2) / (count - 1) : 0;
  const x = padX + index * stepX;
  const y = padY + (height - padY * 2) * (1 - (value - minY) / span);
  return { x, y };
}

export default function CustomerValueChart({
  title,
  subtitle,
  points,
  loading,
  refreshing,
  className,
}: Props) {
  const wrapClass = [
    "value-chart-wrap",
    "in-panel",
    refreshing ? "value-chart-refreshing" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  const width = 640;
  const height = 168;
  const padX = 44;
  const padY = 22;
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const chartMetrics = useMemo(() => {
    if (points.length === 0) return null;
    const totals = points.map((p) => p.total_value);
    const investments = points.map((p) => p.investment_value);
    const coverage = points.map((p) => p.coverage_value);
    const allY = [...totals, ...investments, ...coverage];
    const minY = Math.min(...allY) * 0.95;
    const maxY = Math.max(...allY) * 1.05;
    const first = points[0].total_value;
    const last = points[points.length - 1].total_value;
    const delta = last - first;
    const deltaPct = first > 0 ? (delta / first) * 100 : 0;
    return { totals, investments, coverage, minY, maxY, first, last, delta, deltaPct };
  }, [points]);

  if (loading) {
    return (
      <div className={wrapClass}>
        <h2 className="subsection-title">{title}</h2>
        <p className="muted small">Loading value history…</p>
      </div>
    );
  }

  if (!chartMetrics || points.length === 0) {
    return (
      <div className={wrapClass}>
        <h2 className="subsection-title">{title}</h2>
        <p className="muted small">No historical value snapshots for this selection.</p>
      </div>
    );
  }

  const { totals, investments, coverage, minY, maxY, last, delta, deltaPct } =
    chartMetrics;
  const active = activeIndex != null ? points[activeIndex] : null;

  return (
    <div className={wrapClass}>
      {refreshing && (
        <p className="value-chart-refresh-label muted small">Updating chart…</p>
      )}
      <div className="panel-head value-chart-head">
        <div>
          <h2 className="subsection-title">{title}</h2>
          {subtitle && <p className="muted small">{subtitle}</p>}
        </div>
        <div className="value-chart-kpi">
          <span className="label">Latest total</span>
          <strong>{formatAxisMoney(last)}</strong>
          <span className={`small ${delta >= 0 ? "delta-up" : "delta-down"}`}>
            {delta >= 0 ? "+" : ""}
            {formatAxisMoney(delta)} ({deltaPct >= 0 ? "+" : ""}
            {deltaPct.toFixed(1)}%) vs start
          </span>
        </div>
      </div>

      {active && (
        <div className="chart-tooltip" role="status">
          <strong>{formatPeriodLabel(active.period)}</strong>
          <span>Total {formatTooltipMoney(active.total_value)}</span>
          <span>Investments {formatTooltipMoney(active.investment_value)}</span>
          <span>Coverage {formatTooltipMoney(active.coverage_value)}</span>
        </div>
      )}

      <div className="value-chart-canvas">
        <svg
          className="value-chart-svg"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label="Customer value over time"
          onMouseLeave={() => setActiveIndex(null)}
        >
          <line
            x1={padX}
            y1={height - padY}
            x2={width - padX}
            y2={height - padY}
            className="chart-axis"
          />
          <text x={padX - 6} y={padY} className="chart-axis-label" textAnchor="end">
            {formatAxisMoney(maxY)}
          </text>
          <text
            x={padX - 6}
            y={height - padY}
            className="chart-axis-label"
            textAnchor="end"
          >
            {formatAxisMoney(minY)}
          </text>
          <path
            d={linePath(coverage, width, height, padX, padY, minY, maxY)}
            className="chart-line chart-line-coverage"
            fill="none"
          />
          <path
            d={linePath(investments, width, height, padX, padY, minY, maxY)}
            className="chart-line chart-line-investment"
            fill="none"
          />
          <path
            d={linePath(totals, width, height, padX, padY, minY, maxY)}
            className="chart-line chart-line-total"
            fill="none"
          />
          {points.map((p, i) => {
            const { x, y } = pointCoords(
              i,
              p.total_value,
              points.length,
              width,
              height,
              padX,
              padY,
              minY,
              maxY,
            );
            return (
              <g key={p.period}>
                <circle
                  cx={x}
                  cy={y}
                  r={activeIndex === i ? 5 : 8}
                  className="chart-hit"
                  onMouseEnter={() => setActiveIndex(i)}
                  onFocus={() => setActiveIndex(i)}
                  tabIndex={0}
                  aria-label={`${formatPeriodLabel(p.period)} total ${formatTooltipMoney(p.total_value)}`}
                />
                {activeIndex === i && (
                  <circle cx={x} cy={y} r={3.5} className="chart-point-active" />
                )}
                <text
                  x={x}
                  y={height - 6}
                  className="chart-x-label"
                  textAnchor="middle"
                >
                  {formatPeriodLabel(p.period)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <ul className="chart-legend">
        <li>
          <span className="swatch swatch-total" /> Total customer value
        </li>
        <li>
          <span className="swatch swatch-investment" /> Investment accumulation
        </li>
        <li>
          <span className="swatch swatch-coverage" /> Coverage & savings (policy status)
        </li>
      </ul>
    </div>
  );
}
