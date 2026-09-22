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
  loading?: boolean;
  emptyMessage?: string;
  lineFormat?: ChartValueFormat;
  barFormat?: ChartValueFormat;
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
  const minY =
    format === "count" || format === "average"
      ? Math.max(0, rawMin - pad)
      : rawMin * 0.92;
  const maxY =
    format === "count" || format === "average" ? rawMax + pad : rawMax * 1.05;
  return { minY, maxY };
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
  lineFormat = "money",
  barFormat = "average",
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

  if (points.length === 0 || lineFlat.length === 0 || barFlat.length === 0) {
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

  const active = activeIndex != null ? points[activeIndex] : null;

  return (
    <div className="analytics-chart-panel">
      <h3 className="analytics-chart-title">{title}</h3>
      {subtitle && <p className="muted small analytics-chart-sub">{subtitle}</p>}
      <div className="value-chart-canvas">
        <svg
          ref={svgRef}
          className="value-chart-svg analytics-chart-svg"
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
            {formatAxisMoney(lineBounds.maxY)}
          </text>
          <text
            x={padX - 8}
            y={plotBottom}
            className="chart-axis-label"
            textAnchor="end"
          >
            {formatAxisMoney(lineBounds.minY)}
          </text>
          <text
            x={width - padX + 8}
            y={padTop}
            className="chart-axis-label chart-axis-label-right"
            textAnchor="start"
          >
            {(barFormat === "average" ? formatAxisAverage : formatAxisCount)(
              barBounds.maxY,
            )}
          </text>
          <text
            x={width - padX + 8}
            y={plotBottom}
            className="chart-axis-label chart-axis-label-right"
            textAnchor="start"
          >
            {(barFormat === "average" ? formatAxisAverage : formatAxisCount)(
              barBounds.minY,
            )}
          </text>
          {bars.values.map((v, i) => {
            if (v == null) return null;
            const x = xForIndex(i, points.length, width, padX);
            const y = yForValue(v, barBounds.minY, barBounds.maxY, plotBottom, plotHeight);
            const barH = plotBottom - y;
            const isActive = activeIndex === i;
            return (
              <rect
                key={`bar-${bars.id}-${i}`}
                x={x - barWidth / 2}
                y={y}
                width={barWidth}
                height={Math.max(0, barH)}
                className={`analytics-bar-fill analytics-bar-fill-behind${isActive ? " analytics-bar-fill-active" : ""}`}
                fill={barFill}
                rx={2}
                pointerEvents="none"
              />
            );
          })}
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
            className="chart-plot-hit"
            onMouseMove={handlePlotMove}
            onMouseLeave={clearHover}
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
