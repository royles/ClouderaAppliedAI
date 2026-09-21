import { useMemo, useState } from "react";
import {
  ChartSeries,
  SERIES_VISUAL,
  formatAxisMoney,
  formatAxisPct,
  formatPeriodLabel,
  formatTooltipMoney,
  linePath,
  seriesHasPoints,
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
  interactive?: boolean;
  onPeriodSelect?: (selection: { period: string; kind?: string }) => void;
};

function LegendSwatch({ visualKey }: { visualKey: ChartSeries["visualKey"] }) {
  const v = SERIES_VISUAL[visualKey];
  return (
    <svg
      className="legend-swatch-svg"
      width="22"
      height="8"
      aria-hidden
      focusable="false"
    >
      <line
        x1="0"
        y1="4"
        x2="22"
        y2="4"
        stroke={v.stroke}
        strokeWidth={v.strokeWidth}
        strokeDasharray={v.strokeDasharray}
        opacity={v.opacity ?? 1}
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function AnalyticsLineChart({
  title,
  subtitle,
  points,
  series,
  loading,
  valueFormat = "money",
  forecastDividerIndex = -1,
  emptyMessage = "No data for this cohort.",
  interactive = false,
  onPeriodSelect,
}: Props) {
  const width = 640;
  const height = 160;
  const padX = 44;
  const padY = 22;
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const visibleSeries = useMemo(
    () => series.filter((s) => seriesHasPoints(s.values)),
    [series],
  );

  if (loading) {
    return (
      <div className="analytics-chart-panel">
        <h3 className="analytics-chart-title">{title}</h3>
        <p className="muted small">Loading…</p>
      </div>
    );
  }

  if (points.length === 0 || visibleSeries.length === 0) {
    return (
      <div className="analytics-chart-panel">
        <h3 className="analytics-chart-title">{title}</h3>
        <p className="muted small">{emptyMessage}</p>
      </div>
    );
  }

  const flat = visibleSeries.flatMap((s) =>
    s.values.filter((v): v is number => v != null),
  );
  const rawMin = Math.min(...flat);
  const rawMax = Math.max(...flat);
  const pad = (rawMax - rawMin) * 0.08 || (valueFormat === "percent" ? 1 : rawMax * 0.05 || 1);
  const minY = valueFormat === "percent" ? rawMin - pad : rawMin * 0.92;
  const maxY = valueFormat === "percent" ? rawMax + pad : rawMax * 1.05;
  const formatAxis = valueFormat === "percent" ? formatAxisPct : formatAxisMoney;
  const active = activeIndex != null ? points[activeIndex] : null;

  const anchorSeries =
    visibleSeries.find((s) => s.visualKey === "book-total") ??
    visibleSeries.find((s) => s.visualKey === "churn-book-actual") ??
    visibleSeries[0];

  return (
    <div className="analytics-chart-panel">
      <h3 className="analytics-chart-title">{title}</h3>
      {subtitle && <p className="muted small analytics-chart-sub">{subtitle}</p>}
      {interactive && onPeriodSelect && (
        <p className="muted small chart-interactive-hint">
          Click a date to open customers contributing to that point on the customer page.
        </p>
      )}
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
          {visibleSeries.map((s) => {
            const v = SERIES_VISUAL[s.visualKey];
            const d = linePath(s.values, width, height, padX, padY, minY, maxY);
            if (!d) return null;
            return (
              <path
                key={s.id}
                d={d}
                fill="none"
                stroke={v.stroke}
                strokeWidth={v.strokeWidth}
                strokeDasharray={v.strokeDasharray}
                opacity={v.opacity ?? 1}
                strokeLinecap="round"
                strokeLinejoin="round"
                vectorEffect="non-scaling-stroke"
              />
            );
          })}
          {points.map((p, i) => {
            const stepX =
              points.length > 1 ? (width - padX * 2) / (points.length - 1) : 0;
            const x = padX + i * stepX;
            const anchor = anchorSeries?.values[i];
            const y =
              anchor != null
                ? padY +
                  (height - padY * 2) * (1 - (anchor - minY) / (maxY - minY || 1))
                : height - padY;
            const showLabel =
              i === 0 ||
              i === points.length - 1 ||
              i % Math.max(1, Math.floor(points.length / 6)) === 0;
            const selectable =
              interactive &&
              onPeriodSelect &&
              p.kind !== "forecast" &&
              anchor != null;
            return (
              <g key={`${p.period}-${i}`}>
                <circle
                  cx={x}
                  cy={y}
                  r={7}
                  className={`chart-hit${selectable ? " chart-hit-selectable" : ""}`}
                  onMouseEnter={() => setActiveIndex(i)}
                  tabIndex={selectable ? 0 : -1}
                  onFocus={() => setActiveIndex(i)}
                  onClick={() => {
                    if (!selectable) return;
                    onPeriodSelect({ period: p.period, kind: p.kind });
                  }}
                  onKeyDown={(e) => {
                    if (!selectable) return;
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onPeriodSelect({ period: p.period, kind: p.kind });
                    }
                  }}
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
        {visibleSeries.map((s) => (
          <li key={s.id}>
            <LegendSwatch visualKey={s.visualKey} />
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
