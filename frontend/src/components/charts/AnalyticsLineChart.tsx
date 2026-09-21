import { useState } from "react";
import {
  ChartSeries,
  formatAxisMoney,
  formatAxisPct,
  formatPeriodLabel,
  formatTooltipMoney,
  linePath,
} from "./analyticsChartUtils";

export type ChartPointMeta = {
  period: string;
  kind?: string;
  tooltipLines: string[];
};

type Props = {
  title: string;
  subtitle?: string;
  points: ChartPointMeta[];
  series: ChartSeries[];
  loading?: boolean;
  valueFormat?: "money" | "percent";
  forecastDividerIndex?: number;
  emptyMessage?: string;
};

export default function AnalyticsLineChart({
  title,
  subtitle,
  points,
  series,
  loading,
  valueFormat = "money",
  forecastDividerIndex = -1,
  emptyMessage = "No data for this cohort.",
}: Props) {
  const width = 640;
  const height = 160;
  const padX = 44;
  const padY = 22;
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  if (loading) {
    return (
      <div className="analytics-chart-panel">
        <h3 className="analytics-chart-title">{title}</h3>
        <p className="muted small">Loading…</p>
      </div>
    );
  }

  if (points.length === 0) {
    return (
      <div className="analytics-chart-panel">
        <h3 className="analytics-chart-title">{title}</h3>
        <p className="muted small">{emptyMessage}</p>
      </div>
    );
  }

  const flat = series.flatMap((s) => s.values.filter((v): v is number => v != null));
  const rawMin = Math.min(...flat);
  const rawMax = Math.max(...flat);
  const pad = (rawMax - rawMin) * 0.08 || (valueFormat === "percent" ? 1 : rawMax * 0.05 || 1);
  const minY = valueFormat === "percent" ? rawMin - pad : rawMin * 0.92;
  const maxY = valueFormat === "percent" ? rawMax + pad : rawMax * 1.05;
  const formatAxis = valueFormat === "percent" ? formatAxisPct : formatAxisMoney;
  const active = activeIndex != null ? points[activeIndex] : null;

  return (
    <div className="analytics-chart-panel">
      <h3 className="analytics-chart-title">{title}</h3>
      {subtitle && <p className="muted small analytics-chart-sub">{subtitle}</p>}
      {active && (
        <div className="chart-tooltip chart-tooltip-compact" role="status">
          <strong>
            {formatPeriodLabel(active.period)}
            {active.kind === "forecast" ? " (forecast)" : ""}
          </strong>
          {active.tooltipLines.map((line) => (
            <span key={line}>{line}</span>
          ))}
        </div>
      )}
      <div className="value-chart-canvas">
        <svg
          className="value-chart-svg analytics-chart-svg"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label={title}
          onMouseLeave={() => setActiveIndex(null)}
        >
          {forecastDividerIndex > 0 && points.length > 1 && (
            <line
              x1={
                padX +
                ((forecastDividerIndex - 0.5) / (points.length - 1)) * (width - padX * 2)
              }
              y1={padY}
              x2={
                padX +
                ((forecastDividerIndex - 0.5) / (points.length - 1)) * (width - padX * 2)
              }
              y2={height - padY}
              className="chart-forecast-divider"
            />
          )}
          <line
            x1={padX}
            y1={height - padY}
            x2={width - padX}
            y2={height - padY}
            className="chart-axis"
          />
          <text x={padX - 8} y={padY} className="chart-axis-label" textAnchor="end">
            {formatAxis(maxY)}
          </text>
          <text
            x={padX - 8}
            y={height - padY}
            className="chart-axis-label"
            textAnchor="end"
          >
            {formatAxis(minY)}
          </text>
          {series.map((s) => (
            <path
              key={s.id}
              d={linePath(s.values, width, height, padX, padY, minY, maxY)}
              className={`chart-line ${s.className}${s.dashed ? " chart-line-dashed" : ""}`}
              fill="none"
            />
          ))}
          {points.map((p, i) => {
            const stepX =
              points.length > 1 ? (width - padX * 2) / (points.length - 1) : 0;
            const x = padX + i * stepX;
            const anchor = series[0]?.values[i] ?? 0;
            const y =
              padY +
              (height - padY * 2) * (1 - ((anchor ?? 0) - minY) / (maxY - minY || 1));
            const showLabel =
              i === 0 ||
              i === points.length - 1 ||
              i % Math.max(1, Math.floor(points.length / 6)) === 0;
            return (
              <g key={`${p.period}-${i}`}>
                <circle
                  cx={x}
                  cy={y}
                  r={7}
                  className="chart-hit"
                  onMouseEnter={() => setActiveIndex(i)}
                  tabIndex={0}
                  onFocus={() => setActiveIndex(i)}
                />
                {showLabel && (
                  <text
                    x={x}
                    y={height - 5}
                    className={`chart-x-label${p.kind === "forecast" ? " chart-x-forecast" : ""}`}
                    textAnchor="middle"
                  >
                    {formatPeriodLabel(p.period)}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
      <ul className="chart-legend chart-legend-compact">
        {series.map((s) => (
          <li key={s.id}>
            <span className={`swatch ${s.className.replace("chart-line-", "swatch-")}`} />{" "}
            {s.label}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function moneyTooltip(label: string, n: number) {
  return `${label} ${formatTooltipMoney(n)}`;
}

export function pctTooltip(label: string, n: number | null | undefined) {
  if (n == null || Number.isNaN(n)) return `${label} —`;
  return `${label} ${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}
