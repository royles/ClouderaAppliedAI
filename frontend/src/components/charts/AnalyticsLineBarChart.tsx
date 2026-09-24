import { useCallback, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { MouseEvent as ReactMouseEvent } from "react";
import {
  ChartValueFormat,
  SeriesVisualKey,
  SERIES_VISUAL,
  formatAxisAverage,
  formatAxisCount,
  formatAxisMoney,
  formatAxisPct,
  formatPeriodAxisLabel,
  formatPeriodLabel,
  historyLabelIndicesForPlot,
  linePath,
} from "./analyticsChartUtils";
import ChartFloatingTooltip from "./ChartFloatingTooltip";
import { LegendSwatch } from "./AnalyticsLineChart";
import {
  ChartTooltipPosition,
  chartPointerFromSvgEvent,
  xForIndex,
} from "./chartPointer";

export type ComboChartPoint = {
  period: string;
  kind?: string;
  tooltipLines: string[];
};

type SeriesValues = {
  id: string;
  visualKey: SeriesVisualKey;
  label: string;
  values: (number | null)[];
};

type Props = {
  title: string;
  subtitle?: string;
  points: ComboChartPoint[];
  line: SeriesValues;
  bars: SeriesValues;
  referenceLine?: SeriesValues;
  loading?: boolean;
  emptyMessage?: string;
  lineFormat?: ChartValueFormat;
  barFormat?: ChartValueFormat;
  /** When true, bars may be omitted for some months (line-only months). */
  allowSparseBars?: boolean;
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
    (format === "count" ? 1 : rawMax * 0.05 || 1);
  if (format === "percent") {
    return {
      minY: Math.min(0, rawMin - pad),
      maxY: Math.max(0, rawMax + pad),
    };
  }
  const minY =
    format === "count" || format === "average"
      ? Math.max(0, rawMin - pad)
      : rawMin * 0.92;
  const maxY =
    format === "count" || format === "average" ? rawMax + pad : rawMax * 1.05;
  return { minY, maxY };
}

function formatAxisFor(format: ChartValueFormat, n: number) {
  if (format === "percent") return formatAxisPct(n);
  if (format === "average") return formatAxisAverage(n);
  if (format === "count") return formatAxisCount(n);
  return formatAxisMoney(n);
}

function yForValue(
  value: number,
  minY: number,
  maxY: number,
  plotBottom: number,
  plotHeight: number,
): number {
  const span = maxY - minY || 1;
  return plotBottom - plotHeight * ((value - minY) / span);
}

export default function AnalyticsLineBarChart({
  title,
  subtitle,
  points,
  line,
  bars,
  loading,
  emptyMessage,
  referenceLine,
  lineFormat = "money",
  barFormat = "average",
  allowSparseBars = false,
  interactive = false,
  onPeriodSelect,
}: Props) {
  const { t } = useTranslation();
  const resolvedEmpty = emptyMessage ?? t("charts.common.empty");
  const width = 640;
  const height = 182;
  const padX = 44;
  const padTop = 22;
  const padBottom = 40;
  const plotBottom = height - padBottom;
  const plotWidth = width - padX * 2;
  const plotHeight = plotBottom - padTop;

  const xLabelIndices = useMemo(
    () => new Set(historyLabelIndicesForPlot(points.length, width, padX)),
    [points.length, width, padX],
  );

  const svgRef = useRef<SVGSVGElement>(null);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState<ChartTooltipPosition | null>(null);
  const [crosshairSvgX, setCrosshairSvgX] = useState<number | null>(null);

  const clearHover = useCallback(() => {
    setActiveIndex(null);
    setTooltipPos(null);
    setCrosshairSvgX(null);
  }, []);

  const handlePlotMove = useCallback(
    (e: ReactMouseEvent<SVGRectElement>) => {
      const svg = svgRef.current;
      if (!svg || points.length === 0) return;
      const hit = chartPointerFromSvgEvent(e, svg, points.length, width, padX);
      if (!hit) return;
      setActiveIndex(hit.index);
      setTooltipPos(hit.position);
      setCrosshairSvgX(hit.svgX);
    },
    [points.length, width, padX],
  );

  const lineFlat = line.values.filter((v): v is number => v != null);
  const barFlat = bars.values.filter((v): v is number => v != null);

  if (loading) {
    return (
      <div className="analytics-chart-panel">
        <h3 className="analytics-chart-title">{title}</h3>
        <p className="muted small">{t("charts.common.loading")}</p>
      </div>
    );
  }

  if (
    points.length === 0 ||
    lineFlat.length === 0 ||
    (!allowSparseBars && barFlat.length === 0)
  ) {
    return (
      <div className="analytics-chart-panel">
        <h3 className="analytics-chart-title">{title}</h3>
        <p className="muted small">{resolvedEmpty}</p>
      </div>
    );
  }

  const lineBounds = boundsForValues(lineFlat, lineFormat);
  const barBounds = boundsForValues(barFlat, barFormat);
  const lineVisual = SERIES_VISUAL[line.visualKey];
  const barFill = SERIES_VISUAL[bars.visualKey].stroke;

  const stepX =
    points.length > 1 ? plotWidth / (points.length - 1) : plotWidth;
  const barWidth = Math.max(4, Math.min(24, stepX * 0.52));

  const lineD = linePath(
    line.values,
    width,
    height,
    padX,
    padTop,
    lineBounds.minY,
    lineBounds.maxY,
    padBottom,
  );

  const referenceD =
    referenceLine &&
    linePath(
      referenceLine.values,
      width,
      height,
      padX,
      padTop,
      lineBounds.minY,
      lineBounds.maxY,
      padBottom,
    );

  const zeroBarY =
    barFormat === "percent"
      ? yForValue(0, barBounds.minY, barBounds.maxY, plotBottom, plotHeight)
      : plotBottom;

  const handlePlotClick = useCallback(
    (e: ReactMouseEvent<SVGRectElement>) => {
      if (!interactive || !onPeriodSelect) return;
      const svg = svgRef.current;
      if (!svg || points.length === 0) return;
      const hit = chartPointerFromSvgEvent(e, svg, points.length, width, padX);
      if (!hit) return;
      const p = points[hit.index];
      if (!p || p.kind === "forecast") return;
      onPeriodSelect({ period: p.period, kind: p.kind });
    },
    [interactive, onPeriodSelect, points, width, padX],
  );

  const active = activeIndex != null ? points[activeIndex] : null;

  return (
    <div className="analytics-chart-panel">
      <h3 className="analytics-chart-title">{title}</h3>
      {subtitle && <p className="muted small analytics-chart-sub">{subtitle}</p>}
      {interactive && onPeriodSelect && (
        <p className="muted small chart-interactive-hint">
          {t("charts.common.interactiveHint")}
        </p>
      )}
      <div className="value-chart-canvas">
        <svg
          ref={svgRef}
          className={`value-chart-svg analytics-chart-svg${interactive ? " analytics-chart-svg-interactive" : ""}`}
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label={title}
        >
          <line
            x1={padX}
            y1={plotBottom}
            x2={width - padX}
            y2={plotBottom}
            className="chart-axis"
          />
          <text x={padX - 8} y={padTop} className="chart-axis-label" textAnchor="end">
            {formatAxisFor(lineFormat, lineBounds.maxY)}
          </text>
          <text
            x={padX - 8}
            y={plotBottom}
            className="chart-axis-label"
            textAnchor="end"
          >
            {formatAxisFor(lineFormat, lineBounds.minY)}
          </text>
          <text
            x={width - padX + 8}
            y={padTop}
            className="chart-axis-label chart-axis-label-right"
            textAnchor="start"
          >
            {formatAxisFor(barFormat, barBounds.maxY)}
          </text>
          <text
            x={width - padX + 8}
            y={plotBottom}
            className="chart-axis-label chart-axis-label-right"
            textAnchor="start"
          >
            {formatAxisFor(barFormat, barBounds.minY)}
          </text>
          {barFormat === "percent" && zeroBarY > padTop && zeroBarY < plotBottom ? (
            <line
              x1={padX}
              y1={zeroBarY}
              x2={width - padX}
              y2={zeroBarY}
              className="chart-zero-line"
              pointerEvents="none"
            />
          ) : null}
          {bars.values.map((v, i) => {
            if (v == null) return null;
            const x = xForIndex(i, points.length, width, padX);
            const yVal = yForValue(v, barBounds.minY, barBounds.maxY, plotBottom, plotHeight);
            const isActive = activeIndex === i;
            const negative = v < 0;
            let y = yVal;
            let barH = zeroBarY - yVal;
            if (negative) {
              y = zeroBarY;
              barH = yVal - zeroBarY;
            }
            return (
              <rect
                key={`bar-${bars.id}-${i}`}
                x={x - barWidth / 2}
                y={y}
                width={barWidth}
                height={Math.max(0, barH)}
                className={`analytics-bar-fill analytics-bar-fill-behind${
                  negative ? " analytics-bar-fill-negative" : ""
                }${isActive ? " analytics-bar-fill-active" : ""}`}
                fill={negative ? undefined : barFill}
                rx={2}
                pointerEvents="none"
              />
            );
          })}
          {referenceD ? (
            <path
              d={referenceD}
              fill="none"
              stroke={SERIES_VISUAL["return-baseline-balance"].stroke}
              strokeWidth={SERIES_VISUAL["return-baseline-balance"].strokeWidth}
              strokeDasharray={SERIES_VISUAL["return-baseline-balance"].strokeDasharray}
              opacity={SERIES_VISUAL["return-baseline-balance"].opacity ?? 1}
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
          {lineD ? (
            <path
              d={lineD}
              fill="none"
              stroke={lineVisual.stroke}
              strokeWidth={lineVisual.strokeWidth}
              strokeDasharray={lineVisual.strokeDasharray}
              opacity={lineVisual.opacity ?? 1}
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
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
            return showLabel ? (
              <text
                key={`lbl-${p.period}-${i}`}
                x={x}
                y={labelY}
                transform={`rotate(-42 ${x} ${labelY})`}
                className={`chart-x-label chart-x-label-rotated${isActive ? " chart-x-label-active" : ""}`}
                textAnchor="end"
                pointerEvents="none"
              >
                {formatPeriodAxisLabel(p.period)}
              </text>
            ) : null;
          })}
          <rect
            x={padX}
            y={padTop}
            width={plotWidth}
            height={plotHeight}
            className={`chart-plot-hit${interactive ? " chart-plot-hit-actionable" : ""}`}
            onMouseMove={handlePlotMove}
            onMouseLeave={clearHover}
            onClick={interactive ? handlePlotClick : undefined}
          />
        </svg>
      </div>
      {active && tooltipPos && (
        <ChartFloatingTooltip position={tooltipPos}>
          <strong>{formatPeriodLabel(active.period)}</strong>
          {active.tooltipLines.map((lineText) => (
            <span key={lineText}>{lineText}</span>
          ))}
        </ChartFloatingTooltip>
      )}
      <ul className="chart-legend chart-legend-compact">
        {referenceLine ? (
          <li>
            <LegendSwatch visualKey="return-baseline-balance" />
            {referenceLine.label}
          </li>
        ) : null}
        <li>
          <LegendSwatch visualKey={line.visualKey} />
          {line.label}
          <span className="chart-legend-axis-hint">{t("charts.common.axisLeft")}</span>
        </li>
        <li>
          <span className="legend-bar-swatch" style={{ background: barFill }} aria-hidden />
          {bars.label}
          <span className="chart-legend-axis-hint">{t("charts.common.axisRight")}</span>
        </li>
      </ul>
    </div>
  );
}
