import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";
import { ValueHistoryPoint } from "../api";
import {
  buildCustomerValueWithChurnForecast,
  CustomerChurnInput,
  ExtendedValuePoint,
} from "../customerValueChurnForecast";
import ChartFloatingTooltip from "./charts/ChartFloatingTooltip";
import { chartPointerFromSvgEvent, ChartTooltipPosition } from "./charts/chartPointer";

type Props = {
  title: string;
  subtitle?: string;
  points: ValueHistoryPoint[];
  loading?: boolean;
  refreshing?: boolean;
  className?: string;
  /** When set, extends the chart with a lapse scenario (value → 0 at predicted churn). */
  churn?: CustomerChurnInput | null;
  /** Size SVG to the chart canvas (customer detail hero). */
  fillContainer?: boolean;
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
  values: (number | null)[],
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
  let d = "";
  let open = false;
  values.forEach((v, i) => {
    if (v == null) {
      open = false;
      return;
    }
    const x = padX + i * stepX;
    const y = padY + (height - padY * 2) * (1 - (v - minY) / span);
    d += `${open ? " L" : " M"}${x.toFixed(1)},${y.toFixed(1)}`;
    open = true;
  });
  return d.trim();
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
  churn,
  fillContainer = false,
}: Props) {
  const wrapClass = [
    "value-chart-wrap",
    "in-panel",
    fillContainer ? "value-chart-fill" : "",
    refreshing ? "value-chart-refreshing" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  const canvasRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [canvasSize, setCanvasSize] = useState({ width: 640, height: 168 });
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState<ChartTooltipPosition | null>(null);

  useEffect(() => {
    if (!fillContainer || !canvasRef.current) return;
    const node = canvasRef.current;
    const update = () => {
      const rect = node.getBoundingClientRect();
      setCanvasSize({
        width: Math.max(280, Math.floor(rect.width)),
        height: Math.max(140, Math.floor(rect.height)),
      });
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(node);
    return () => observer.disconnect();
  }, [fillContainer]);

  const width = fillContainer ? canvasSize.width : 640;
  const height = fillContainer ? canvasSize.height : 168;
  const padX = fillContainer ? Math.max(36, Math.round(width * 0.06)) : 44;
  const padY = fillContainer ? Math.max(28, Math.round(height * 0.12)) : 22;
  const xLabelBottom = fillContainer ? Math.max(8, height - padY + 14) : height - 6;

  const forecastBundle = useMemo(
    () => buildCustomerValueWithChurnForecast(points, churn),
    [points, churn],
  );

  const chartMetrics = useMemo(() => {
    if (!forecastBundle || forecastBundle.points.length === 0) return null;
    const displayPoints = forecastBundle.points;
    const historyLen = points.length;
    const totals = displayPoints.map((p) => p.total_value);
    const investments = displayPoints.map((p) =>
      p.kind === "actual" ? p.investment_value : null,
    );
    const coverage = displayPoints.map((p) =>
      p.kind === "actual" ? p.coverage_value : null,
    );
    const actualTotals = displayPoints.map((p, i) =>
      i < historyLen ? p.total_value : null,
    );
    const forecastTotals = displayPoints.map((p, i) => {
      if (i < historyLen - 1) return null;
      if (p.kind === "actual" && i === historyLen - 1) return p.total_value;
      if (p.kind === "forecast") return p.total_value;
      return null;
    });
    const numericY = totals.filter((v) => v != null) as number[];
    const minY = forecastBundle.monthsToChurn > 0 ? 0 : Math.min(...numericY) * 0.95;
    const maxY = Math.max(...numericY) * 1.05;
    const first = points[0].total_value;
    const last = forecastBundle.lastActualValue;
    const delta = last - first;
    const deltaPct = first > 0 ? (delta / first) * 100 : 0;
    const lapseIndex = displayPoints.findIndex((p) => p.is_predicted_lapse);
    return {
      displayPoints,
      historyLen,
      totals,
      investments,
      coverage,
      actualTotals,
      forecastTotals,
      minY,
      maxY,
      first,
      last,
      delta,
      deltaPct,
      lapseIndex,
      monthsToChurn: forecastBundle.monthsToChurn,
      predictedLapsePeriod: forecastBundle.predictedLapsePeriod,
      valueAtRisk: forecastBundle.valueAtRisk,
      churnProbability: churn?.probability ?? null,
    };
  }, [forecastBundle, points.length, churn?.probability]);

  if (loading) {
    return (
      <div className={wrapClass}>
        <h2 className="subsection-title">{title}</h2>
        <p className="muted small">Loading value history…</p>
      </div>
    );
  }

  if (!chartMetrics || chartMetrics.displayPoints.length === 0) {
    return (
      <div className={wrapClass}>
        <h2 className="subsection-title">{title}</h2>
        <p className="muted small">No historical value snapshots for this selection.</p>
      </div>
    );
  }

  const {
    displayPoints,
    investments,
    coverage,
    actualTotals,
    forecastTotals,
    minY,
    maxY,
    last,
    delta,
    deltaPct,
    lapseIndex,
    monthsToChurn,
    predictedLapsePeriod,
    valueAtRisk,
    churnProbability,
  } = chartMetrics;
  const pointCount = displayPoints.length;
  const xLabelStep =
    pointCount <= 8 ? 1 : pointCount <= 14 ? 2 : Math.max(2, Math.ceil(pointCount / 7));
  const showXLabel = (index: number) =>
    index === 0 || index === pointCount - 1 || index % xLabelStep === 0;
  const active =
    activeIndex != null ? (displayPoints[activeIndex] as ExtendedValuePoint) : null;
  const showChurnForecast = monthsToChurn > 0 && churnProbability != null;

  const clearHover = useCallback(() => {
    setActiveIndex(null);
    setTooltipPos(null);
  }, []);

  const handlePlotPointer = useCallback(
    (e: ReactMouseEvent<SVGSVGElement>) => {
      const svg = svgRef.current;
      const canvas = canvasRef.current;
      if (!svg || !canvas || pointCount === 0) return;
      const hit = chartPointerFromSvgEvent(e, svg, canvas, pointCount, width, padX);
      if (!hit) return;
      setActiveIndex(hit.index);
      setTooltipPos(hit.position);
    },
    [pointCount, width, padX],
  );

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
        <div className="value-chart-kpi value-chart-kpi-stack">
          <div>
            <span className="label">Latest total</span>
            <strong>{formatAxisMoney(last)}</strong>
            <span className={`small ${delta >= 0 ? "delta-up" : "delta-down"}`}>
              {delta >= 0 ? "+" : ""}
              {formatAxisMoney(delta)} ({deltaPct >= 0 ? "+" : ""}
              {deltaPct.toFixed(1)}%) vs start
            </span>
          </div>
          {showChurnForecast && (
            <div className="value-chart-churn-kpi">
              <span className="label">12m lapse risk</span>
              <strong>{(churnProbability * 100).toFixed(1)}%</strong>
              <span className="muted small">
                At-risk {formatTooltipMoney(valueAtRisk)} · Predicted lapse{" "}
                {predictedLapsePeriod
                  ? formatPeriodLabel(predictedLapsePeriod)
                  : "—"}{" "}
                ({monthsToChurn} mo)
              </span>
            </div>
          )}
        </div>
      </div>

      <div
        ref={canvasRef}
        className={`value-chart-canvas${fillContainer ? " value-chart-canvas-fill" : ""}`}
      >
        {active && (
          <ChartFloatingTooltip canvasRef={canvasRef} position={tooltipPos}>
            <strong>
              {formatPeriodLabel(active.period)}
              {active.kind === "forecast" ? " (projected)" : ""}
            </strong>
            <span>Total {formatTooltipMoney(active.total_value)}</span>
            {active.kind === "actual" && (
              <>
                <span>Investments {formatTooltipMoney(active.investment_value)}</span>
                <span>Coverage {formatTooltipMoney(active.coverage_value)}</span>
              </>
            )}
            {active.is_predicted_lapse && (
              <span className="warn-stat">Predicted lapse — value at ₪0</span>
            )}
          </ChartFloatingTooltip>
        )}
        <svg
          ref={svgRef}
          className="value-chart-svg"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio={fillContainer ? "none" : "xMidYMid meet"}
          role="img"
          aria-label={
            showChurnForecast
              ? "Customer value over time with churn lapse forecast"
              : "Customer value over time"
          }
          onMouseMove={handlePlotPointer}
          onMouseLeave={clearHover}
        >
          <rect
            x={padX}
            y={padY}
            width={Math.max(0, width - padX * 2)}
            height={Math.max(0, height - padY * 2)}
            fill="transparent"
            aria-hidden
          />
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
            d={linePath(actualTotals, width, height, padX, padY, minY, maxY)}
            className="chart-line chart-line-total"
            fill="none"
          />
          {showChurnForecast && (
            <path
              d={linePath(forecastTotals, width, height, padX, padY, minY, maxY)}
              className="chart-line chart-line-forecast chart-line-total"
              fill="none"
            />
          )}
          {showChurnForecast && lapseIndex >= 0 && (
            (() => {
              const stepX =
                displayPoints.length > 1
                  ? (width - padX * 2) / (displayPoints.length - 1)
                  : 0;
              const x = padX + lapseIndex * stepX;
              return (
                <line
                  x1={x}
                  y1={padY}
                  x2={x}
                  y2={height - padY}
                  className="chart-churn-lapse-marker"
                />
              );
            })()
          )}
          {displayPoints.map((p, i) => {
            const { x, y } = pointCoords(
              i,
              p.total_value,
              displayPoints.length,
              width,
              height,
              padX,
              padY,
              minY,
              maxY,
            );
            const isForecast = p.kind === "forecast";
            return (
              <g key={`${p.period}-${p.kind}`}>
                <circle
                  cx={x}
                  cy={y}
                  r={activeIndex === i ? 5 : 8}
                  className="chart-hit"
                  onFocus={(e) => {
                    setActiveIndex(i);
                    const canvas = canvasRef.current;
                    const target = e.currentTarget;
                    if (canvas && target) {
                      const cRect = canvas.getBoundingClientRect();
                      const tRect = target.getBoundingClientRect();
                      setTooltipPos({
                        x: tRect.left - cRect.left + tRect.width / 2,
                        y: tRect.top - cRect.top,
                      });
                    }
                  }}
                  onBlur={clearHover}
                  tabIndex={0}
                  aria-label={`${formatPeriodLabel(p.period)} total ${formatTooltipMoney(p.total_value)}`}
                />
                {activeIndex === i && (
                  <circle
                    cx={x}
                    cy={y}
                    r={3.5}
                    className={
                      p.is_predicted_lapse
                        ? "chart-point-lapse"
                        : "chart-point-active"
                    }
                  />
                )}
                {p.is_predicted_lapse && (
                  <circle cx={x} cy={y} r={4.5} className="chart-point-lapse-ring" />
                )}
                {showXLabel(i) && (
                  <text
                    x={x}
                    y={xLabelBottom}
                    className={`chart-x-label${isForecast ? " chart-x-forecast" : ""}`}
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

      <ul className="chart-legend">
        <li>
          <span className="swatch swatch-total" /> Total customer value (actual)
        </li>
        {showChurnForecast && (
          <li>
            <span className="swatch swatch-forecast" /> Lapse scenario (value → ₪0)
          </li>
        )}
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
