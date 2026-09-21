import { useCallback, useMemo, useRef, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";
import {
  ChartSeries,
  ChartValueFormat,
  SERIES_VISUAL,
  formatAxisCount,
  formatAxisMoney,
  formatAxisPct,
  formatPeriodAxisLabel,
  formatPeriodLabel,
  historyLabelIndicesForPlot,
  formatTooltipMoney,
  linePath,
  seriesHasPoints,
} from "./analyticsChartUtils";
import ChartFloatingTooltip from "./ChartFloatingTooltip";
import {
  chartPointerFromSvgEvent,
  ChartTooltipPosition,
  svgPointFromClient,
  xForIndex,
} from "./chartPointer";

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

function boundsForValues(
  values: number[],
  format: ChartValueFormat,
): { minY: number; maxY: number } {
  if (values.length === 0) {
    return { minY: 0, maxY: 1 };
  }
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const pad =
    (rawMax - rawMin) * 0.08 ||
    (format === "percent" ? 1 : format === "count" ? 1 : rawMax * 0.05 || 1);
  const minY =
    format === "percent"
      ? rawMin - pad
      : format === "count"
        ? Math.max(0, rawMin - pad)
        : rawMin * 0.92;
  const maxY =
    format === "percent"
      ? rawMax + pad
      : format === "count"
        ? rawMax + pad
        : rawMax * 1.05;
  return { minY, maxY };
}

function formatForKind(kind: ChartValueFormat) {
  return kind === "percent"
    ? formatAxisPct
    : kind === "count"
      ? formatAxisCount
      : formatAxisMoney;
}

function isPeriodSelectable(meta: ChartPointMeta): boolean {
  return meta.kind !== "forecast";
}

export function LegendSwatch({ visualKey }: { visualKey: ChartSeries["visualKey"] }) {
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
  const height = 182;
  const padX = 44;
  const padTop = 22;
  const padBottom = 40;
  const plotBottom = height - padBottom;
  const xLabelIndices = useMemo(
    () => new Set(historyLabelIndicesForPlot(points.length, width, padX)),
    [points.length, width, padX],
  );
  const canvasRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState<ChartTooltipPosition | null>(null);
  const [crosshairSvgX, setCrosshairSvgX] = useState<number | null>(null);

  const visibleSeries = useMemo(
    () => series.filter((s) => seriesHasPoints(s.values)),
    [series],
  );

  const pickIndexFromEvent = useCallback(
    (e: ReactMouseEvent<Element>) => {
      const target = e.currentTarget;
      const svg =
        target instanceof SVGSVGElement
          ? target
          : (target as SVGElement).ownerSVGElement;
      if (!svg) return null;
      const loc = svgPointFromClient(svg, e.clientX, e.clientY);
      if (!loc) return null;
      return indexFromSvgX(loc.x, points.length, width, padX);
    },
    [points.length, width, padX],
  );

  const clearHover = useCallback(() => {
    setActiveIndex(null);
    setTooltipPos(null);
    setCrosshairSvgX(null);
  }, []);

  const handlePlotMove = useCallback(
    (e: ReactMouseEvent<SVGRectElement>) => {
      const svg = svgRef.current;
      if (!svg) return;
      const hit = chartPointerFromSvgEvent(e, svg, points.length, width, padX);
      if (!hit) return;
      setActiveIndex(hit.index);
      setTooltipPos(hit.position);
      setCrosshairSvgX(hit.svgX);
    },
    [points.length, width, padX],
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

  const usesDualAxis = visibleSeries.some((s) => (s.axis ?? "primary") === "secondary");
  const primarySeries = visibleSeries.filter((s) => (s.axis ?? "primary") === "primary");
  const secondarySeries = visibleSeries.filter((s) => s.axis === "secondary");
  const primaryFlat = primarySeries.flatMap((s) =>
    s.values.filter((v): v is number => v != null),
  );
  const primaryFormat =
    primarySeries[0]?.valueFormat ?? valueFormat;
  const { minY, maxY } = boundsForValues(primaryFlat, primaryFormat);
  const formatAxis = formatForKind(primaryFormat);

  let secondaryBounds: { minY: number; maxY: number } | null = null;
  let formatSecondaryAxis = formatAxisCount;
  if (usesDualAxis && secondarySeries.length > 0) {
    const secondaryFlat = secondarySeries.flatMap((s) =>
      s.values.filter((v): v is number => v != null),
    );
    const secondaryFormat =
      secondarySeries[0]?.valueFormat ?? ("count" as ChartValueFormat);
    secondaryBounds = boundsForValues(secondaryFlat, secondaryFormat);
    formatSecondaryAxis = formatForKind(secondaryFormat);
  }
  const active = activeIndex != null ? points[activeIndex] : null;

  const plotWidth = width - padX * 2;
  const plotHeight = plotBottom - padTop;

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
      <div ref={canvasRef} className="value-chart-canvas">
        <svg
          ref={svgRef}
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
              y1={padTop}
              x2={
                padX +
                ((forecastDividerIndex - 0.5) / (points.length - 1)) * (width - padX * 2)
              }
              y2={plotBottom}
              className="chart-forecast-divider"
            />
          )}
          <line
            x1={padX}
            y1={plotBottom}
            x2={width - padX}
            y2={plotBottom}
            className="chart-axis"
          />
          <text x={padX - 8} y={padTop} className="chart-axis-label" textAnchor="end">
            {formatAxis(maxY)}
          </text>
          <text
            x={padX - 8}
            y={plotBottom}
            className="chart-axis-label"
            textAnchor="end"
          >
            {formatAxis(minY)}
          </text>
          {secondaryBounds && (
            <>
              <text
                x={width - padX + 8}
                y={padTop}
                className="chart-axis-label chart-axis-label-right"
                textAnchor="start"
              >
                {formatSecondaryAxis(secondaryBounds.maxY)}
              </text>
              <text
                x={width - padX + 8}
                y={plotBottom}
                className="chart-axis-label chart-axis-label-right"
                textAnchor="start"
              >
                {formatSecondaryAxis(secondaryBounds.minY)}
              </text>
            </>
          )}
          {visibleSeries.map((s) => {
            const v = SERIES_VISUAL[s.visualKey];
            const isSecondary = s.axis === "secondary";
            const scale = isSecondary && secondaryBounds ? secondaryBounds : { minY, maxY };
            const d = linePath(
              s.values,
              width,
              height,
              padX,
              padTop,
              scale.minY,
              scale.maxY,
              padBottom,
            );
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
          {crosshairSvgX != null && (
            <line
              x1={crosshairSvgX}
              y1={padTop}
              x2={crosshairSvgX}
              y2={plotBottom}
              className="chart-crosshair"
              pointerEvents="none"
            />
          )}
          {points.map((p, i) => {
            const x = xForIndex(i, points.length, width, padX);
            const showLabel = xLabelIndices.has(i);
            const isActive = activeIndex === i;
            const labelY = plotBottom + 6;
            return (
              <g key={`${p.period}-${i}`}>
                {showLabel && (
                  <text
                    x={x}
                    y={labelY}
                    transform={`rotate(-42 ${x} ${labelY})`}
                    className={`chart-x-label chart-x-label-rotated${p.kind === "forecast" ? " chart-x-forecast" : ""}${isActive ? " chart-x-label-active" : ""}`}
                    textAnchor="end"
                    pointerEvents="none"
                  >
                    {formatPeriodAxisLabel(p.period)}
                  </text>
                )}
              </g>
            );
          })}
          <rect
            x={padX}
            y={padTop}
            width={plotWidth}
            height={plotHeight}
            className={`chart-plot-hit${
              interactive && crosshairSelectable ? " chart-plot-hit-actionable" : ""
            }`}
            onMouseMove={handlePlotMove}
            onMouseLeave={clearHover}
            onClick={interactive && onPeriodSelect ? handlePlotClick : undefined}
          />
        </svg>
      </div>
      {active && tooltipPos && (
        <ChartFloatingTooltip position={tooltipPos}>
          <strong>
            {formatPeriodLabel(active.period)}
            {active.kind === "forecast" ? " (forecast)" : ""}
          </strong>
          {active.tooltipLines.map((line) => (
            <span key={line}>{line}</span>
          ))}
        </ChartFloatingTooltip>
      )}
      <ul className="chart-legend chart-legend-compact">
        {visibleSeries.map((s) => {
          const axisHint =
            usesDualAxis && (s.axis ?? "primary") === "secondary"
              ? " · right axis"
              : usesDualAxis
                ? " · left axis"
                : "";
          return (
            <li key={s.id}>
              <LegendSwatch visualKey={s.visualKey} />
              {s.label}
              {axisHint ? (
                <span className="chart-legend-axis-hint">{axisHint}</span>
              ) : null}
            </li>
          );
        })}
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
