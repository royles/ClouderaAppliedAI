import { useCallback, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { MouseEvent as ReactMouseEvent } from "react";
import {
  SeriesVisualKey,
  SERIES_VISUAL,
  formatAxisRating,
  formatPeriodAxisLabel,
  formatPeriodLabel,
  historyLabelIndicesForPlot,
} from "./analyticsChartUtils";
import ChartFloatingTooltip from "./ChartFloatingTooltip";
import {
  ChartTooltipPosition,
  indexFromBarChartX,
  svgPointFromClient,
  xForBarCenter,
} from "./chartPointer";

export type BarChartPoint = {
  period: string;
  value: number;
  tooltipLines: string[];
};

type Props = {
  title: string;
  subtitle?: string;
  points: BarChartPoint[];
  visualKey: SeriesVisualKey;
  loading?: boolean;
  emptyMessage?: string;
  yMin?: number;
  yMax?: number;
  legendLabel?: string;
};

export default function AnalyticsBarChart({
  title,
  subtitle,
  points,
  visualKey,
  loading,
  emptyMessage,
  yMin = 0,
  yMax = 5,
  legendLabel,
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
  const span = yMax - yMin || 1;
  const fill = SERIES_VISUAL[visualKey].stroke;

  const xLabelIndices = useMemo(
    () => new Set(historyLabelIndicesForPlot(points.length, width, padX)),
    [points.length, width, padX],
  );

  const svgRef = useRef<SVGSVGElement>(null);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState<ChartTooltipPosition | null>(null);

  const clearHover = useCallback(() => {
    setActiveIndex(null);
    setTooltipPos(null);
  }, []);

  const handlePlotMove = useCallback(
    (e: ReactMouseEvent<SVGRectElement>) => {
      const svg = svgRef.current;
      if (!svg || points.length === 0) return;
      const loc = svgPointFromClient(svg, e.clientX, e.clientY);
      if (!loc) return;
      const index = indexFromBarChartX(loc.x, points.length, width, padX);
      setActiveIndex(index);
      setTooltipPos({ clientX: e.clientX, clientY: e.clientY });
    },
    [points.length, width, padX],
  );

  if (loading) {
    return (
      <div className="analytics-chart-panel">
        <h3 className="analytics-chart-title">{title}</h3>
        <p className="muted small">{t("charts.common.loading")}</p>
      </div>
    );
  }

  if (points.length === 0) {
    return (
      <div className="analytics-chart-panel">
        <h3 className="analytics-chart-title">{title}</h3>
        <p className="muted small">{resolvedEmpty}</p>
      </div>
    );
  }

  const slotWidth = plotWidth / points.length;
  const barWidth = Math.max(4, Math.min(28, slotWidth * 0.62));
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
            {formatAxisRating(yMax)}
          </text>
          <text
            x={padX - 8}
            y={plotBottom}
            className="chart-axis-label"
            textAnchor="end"
          >
            {formatAxisRating(yMin)}
          </text>
          {points.map((p, i) => {
            const cx = xForBarCenter(i, points.length, width, padX);
            const barH = plotHeight * ((p.value - yMin) / span);
            const y = plotBottom - barH;
            const isActive = activeIndex === i;
            return (
              <rect
                key={`${p.period}-${i}`}
                x={cx - barWidth / 2}
                y={y}
                width={barWidth}
                height={Math.max(0, barH)}
                className={`analytics-bar-fill${isActive ? " analytics-bar-fill-active" : ""}`}
                fill={fill}
                rx={2}
                pointerEvents="none"
              />
            );
          })}
          {points.map((p, i) => {
            const x = xForBarCenter(i, points.length, width, padX);
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
          {active.tooltipLines.map((line) => (
            <span key={line}>{line}</span>
          ))}
        </ChartFloatingTooltip>
      )}
      {legendLabel ? (
        <ul className="chart-legend chart-legend-compact">
          <li>
            <span className="legend-bar-swatch" style={{ background: fill }} aria-hidden />
            {legendLabel}
          </li>
        </ul>
      ) : null}
    </div>
  );
}
