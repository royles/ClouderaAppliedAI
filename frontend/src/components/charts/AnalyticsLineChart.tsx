import { useCallback, useMemo, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";
import {
  ChartSeries,
  SERIES_VISUAL,
  formatAxisCount,
  formatAxisMoney,
  formatAxisPct,
  formatPeriodLabel,
  formatTooltipCount,
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
  valueFormat?: "money" | "percent" | "count";
  forecastDividerIndex?: number;
  emptyMessage?: string;
  interactive?: boolean;
  onPeriodSelect?: (selection: { period: string; kind?: string }) => void;
};

function xForIndex(
  index: number,
  pointCount: number,
  width: number,
  padX: number,
): number {
  if (pointCount <= 1) return padX;
  const stepX = (width - padX * 2) / (pointCount - 1);
  return padX + index * stepX;
}

function indexFromSvgX(
  x: number,
  pointCount: number,
  width: number,
  padX: number,
): number {
  if (pointCount <= 1) return 0;
  const stepX = (width - padX * 2) / (pointCount - 1);
  const raw = (x - padX) / stepX;
  return Math.max(0, Math.min(pointCount - 1, Math.round(raw)));
}

function svgPointFromClient(svg: SVGSVGElement, clientX: number, clientY: number) {
  const pt = svg.createSVGPoint();
  pt.x = clientX;
  pt.y = clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return null;
  return pt.matrixTransform(ctm.inverse());
}

function isPeriodSelectable(meta: ChartPointMeta): boolean {
  return meta.kind !== "forecast";
}

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

  const pickIndexFromEvent = useCallback(
    (e: ReactMouseEvent<Element>) => {
      const svg = (e.currentTarget as SVGElement).ownerSVGElement;
      if (!svg) return null;
      const loc = svgPointFromClient(svg, e.clientX, e.clientY);
      if (!loc) return null;
      return indexFromSvgX(loc.x, points.length, width, padX);
    },
    [points.length, width, padX],
  );

  const handlePlotMove = useCallback(
    (e: ReactMouseEvent<SVGRectElement>) => {
      if (!interactive) return;
      const idx = pickIndexFromEvent(e);
      if (idx != null) setActiveIndex(idx);
    },
    [interactive, pickIndexFromEvent],
  );

  const handlePlotClick = useCallback(
    (e: ReactMouseEvent<SVGRectElement>) => {
      if (!interactive || !onPeriodSelect) return;
      const idx = pickIndexFromEvent(e);
      if (idx == null) return;
      const p = points[idx];
      if (!p || !isPeriodSelectable(p)) return;
      onPeriodSelect({ period: p.period, kind: p.kind });
    },
    [interactive, onPeriodSelect, pickIndexFromEvent, points],
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
  const pad =
    (rawMax - rawMin) * 0.08 ||
    (valueFormat === "percent" ? 1 : valueFormat === "count" ? 1 : rawMax * 0.05 || 1);
  const minY =
    valueFormat === "percent"
      ? rawMin - pad
      : valueFormat === "count"
        ? Math.max(0, rawMin - pad)
        : rawMin * 0.92;
  const maxY =
    valueFormat === "percent"
      ? rawMax + pad
      : valueFormat === "count"
        ? rawMax + pad
        : rawMax * 1.05;
  const formatAxis =
    valueFormat === "percent"
      ? formatAxisPct
      : valueFormat === "count"
        ? formatAxisCount
        : formatAxisMoney;
  const active = activeIndex != null ? points[activeIndex] : null;

  const plotWidth = width - padX * 2;
  const plotHeight = height - padY * 2;

  const crosshairX =
    activeIndex != null ? xForIndex(activeIndex, points.length, width, padX) : null;
  const crosshairSelectable =
    activeIndex != null && isPeriodSelectable(points[activeIndex]);

  return (
    <div className="analytics-chart-panel">
      <h3 className="analytics-chart-title">{title}</h3>
      {subtitle && <p className="muted small analytics-chart-sub">{subtitle}</p>}
      {interactive && onPeriodSelect && (
        <p className="muted small chart-interactive-hint">
          Move along the chart to preview a date, then click to filter customers on the
          customer page.
        </p>
      )}
      {active && !interactive && (
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
          className={`value-chart-svg analytics-chart-svg${interactive ? " analytics-chart-svg-interactive" : ""}`}
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label={title}
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
          {crosshairX != null && interactive && (
            <>
              <line
                x1={crosshairX}
                y1={padY}
                x2={crosshairX}
                y2={height - padY}
                className="chart-crosshair"
                pointerEvents="none"
              />
              {activeIndex != null && crosshairSelectable && (
                <circle
                  cx={crosshairX}
                  cy={padY + plotHeight / 2}
                  r={4}
                  className="chart-crosshair-dot"
                  pointerEvents="none"
                />
              )}
            </>
          )}
          {points.map((p, i) => {
            const x = xForIndex(i, points.length, width, padX);
            const showLabel =
              i === 0 ||
              i === points.length - 1 ||
              i % Math.max(1, Math.floor(points.length / 6)) === 0;
            const isActive = activeIndex === i;
            return (
              <g key={`${p.period}-${i}`}>
                {showLabel && (
                  <text
                    x={x}
                    y={height - 5}
                    className={`chart-x-label${p.kind === "forecast" ? " chart-x-forecast" : ""}${isActive ? " chart-x-label-active" : ""}`}
                    textAnchor="middle"
                    pointerEvents="none"
                  >
                    {formatPeriodLabel(p.period)}
                  </text>
                )}
              </g>
            );
          })}
          {interactive && onPeriodSelect && (
            <rect
              x={padX}
              y={padY}
              width={plotWidth}
              height={plotHeight}
              className={`chart-plot-hit${crosshairSelectable ? " chart-plot-hit-actionable" : ""}`}
              onMouseMove={handlePlotMove}
              onMouseLeave={() => setActiveIndex(null)}
              onClick={handlePlotClick}
            />
          )}
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
