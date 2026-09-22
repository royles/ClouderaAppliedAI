import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { MouseEvent as ReactMouseEvent } from "react";
import { ValueHistoryPoint } from "../api";
import {
  buildCustomerValueWithChurnForecast,
  CustomerChurnInput,
  ExtendedValuePoint,
} from "../customerValueChurnForecast";
import { LegendSwatch } from "./charts/AnalyticsLineChart";
import {
  formatPeriodAxisLabel,
  historyLabelIndicesForPlot,
} from "./charts/analyticsChartUtils";
import ChartFloatingTooltip from "./charts/ChartFloatingTooltip";
import {
  chartPointerFromSvgEvent,
  ChartTooltipPosition,
  xForIndex,
} from "./charts/chartPointer";
import { intlLocale } from "../localeFormat";

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
    const month = new Date(Number(y), Number(m) - 1, 1).toLocaleString(intlLocale(), {
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
  return new Intl.NumberFormat(intlLocale(), {
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
  padTop: number,
  minY: number,
  maxY: number,
  padBottom: number = padTop,
): string {
  if (values.length === 0) return "";
  const span = maxY - minY || 1;
  const stepX = values.length > 1 ? (width - padX * 2) / (values.length - 1) : 0;
  const plotHeight = Math.max(1, height - padTop - padBottom);
  let d = "";
  let open = false;
  values.forEach((v, i) => {
    if (v == null) {
      open = false;
      return;
    }
    const x = padX + i * stepX;
    const y = padTop + plotHeight * (1 - (v - minY) / span);
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
  padTop: number,
  minY: number,
  maxY: number,
  padBottom: number = padTop,
) {
  const span = maxY - minY || 1;
  const stepX = count > 1 ? (width - padX * 2) / (count - 1) : 0;
  const plotHeight = Math.max(1, height - padTop - padBottom);
  const x = padX + index * stepX;
  const y = padTop + plotHeight * (1 - (value - minY) / span);
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
  const { t } = useTranslation();
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
  const [crosshairSvgX, setCrosshairSvgX] = useState<number | null>(null);

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
  const height = fillContainer ? canvasSize.height : 182;
  const padX = fillContainer ? Math.max(36, Math.round(width * 0.06)) : 44;
  const padTop = fillContainer ? Math.max(24, Math.round(height * 0.1)) : 22;
  const padBottom = fillContainer ? Math.max(36, Math.round(height * 0.2)) : 40;
  const plotBottom = height - padBottom;

  const forecastBundle = useMemo(
    () => buildCustomerValueWithChurnForecast(points, churn),
    [points, churn],
  );

  const xLabelIndices = useMemo(
    () =>
      new Set(
        historyLabelIndicesForPlot(forecastBundle?.points.length ?? 0, width, padX),
      ),
    [forecastBundle?.points.length, width, padX],
  );

  const chartMetrics = useMemo(() => {
    if (!forecastBundle || forecastBundle.points.length === 0) return null;
    const displayPoints = forecastBundle.points;
    const historyLen = points.length;
    const totals = displayPoints.map((p) => p.total_value);
    const includeForecastComponents = forecastBundle.scenario !== "high_lapse";
    const investments = displayPoints.map((p) =>
      p.kind === "actual" || (p.kind === "forecast" && includeForecastComponents)
        ? p.investment_value
        : null,
    );
    const coverage = displayPoints.map((p) =>
      p.kind === "actual" || (p.kind === "forecast" && includeForecastComponents)
        ? p.coverage_value
        : null,
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
    const minY =
      forecastBundle.scenario === "high_lapse"
        ? 0
        : Math.min(...numericY) * 0.95;
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
      forecastHorizonMonths: forecastBundle.forecastHorizonMonths,
      predictedLapsePeriod: forecastBundle.predictedLapsePeriod,
      valueAtRisk: forecastBundle.valueAtRisk,
      churnProbability: churn?.probability ?? null,
      scenario: forecastBundle.scenario,
      churnTier: churn?.tier ?? null,
    };
  }, [forecastBundle, points.length, churn?.probability, churn?.tier]);

  if (loading) {
    return (
      <div className={wrapClass}>
        <h2 className="subsection-title">{title}</h2>
        <p className="muted small">{t("charts.customerValue.loading")}</p>
      </div>
    );
  }

  if (!chartMetrics || chartMetrics.displayPoints.length === 0) {
    return (
      <div className={wrapClass}>
        <h2 className="subsection-title">{title}</h2>
        <p className="muted small">{t("charts.customerValue.empty")}</p>
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
    forecastHorizonMonths,
    predictedLapsePeriod,
    valueAtRisk,
    churnProbability,
    scenario,
    churnTier,
  } = chartMetrics;
  const pointCount = displayPoints.length;
  const active =
    activeIndex != null ? (displayPoints[activeIndex] as ExtendedValuePoint) : null;
  const showChurnForecast = scenario !== "none";
  const forecastLegendLabel =
    scenario === "high_lapse"
      ? "High risk — lapse to ₪0 (3 mo)"
      : scenario === "medium_trend"
        ? "Medium risk — trend from recent history"
        : scenario === "low_trend"
          ? "Low risk — trend from full history"
          : "";

  const clearHover = useCallback(() => {
    setActiveIndex(null);
    setTooltipPos(null);
    setCrosshairSvgX(null);
  }, []);

  const handlePlotPointer = useCallback(
    (e: ReactMouseEvent<SVGRectElement>) => {
      const svg = svgRef.current;
      if (!svg || pointCount === 0) return;
      const hit = chartPointerFromSvgEvent(e, svg, pointCount, width, padX);
      if (!hit) return;
      setActiveIndex(hit.index);
      setTooltipPos(hit.position);
      setCrosshairSvgX(hit.svgX);
    },
    [pointCount, width, padX],
  );

  const plotWidth = Math.max(0, width - padX * 2);
  const plotHeight = Math.max(0, plotBottom - padTop);

  return (
    <div className={wrapClass}>
      {refreshing && (
        <p className="value-chart-refresh-label muted small">{t("charts.customerValue.refreshing")}</p>
      )}
      <div className="panel-head value-chart-head">
        <div>
          <h2 className="subsection-title">{title}</h2>
          {subtitle && <p className="muted small">{subtitle}</p>}
        </div>
        <div className="value-chart-kpi value-chart-kpi-stack">
          <div>
            <span className="label">{t("charts.customerValue.latestTotal")}</span>
            <strong>{formatAxisMoney(last)}</strong>
            <span className={`small ${delta >= 0 ? "delta-up" : "delta-down"}`}>
              {delta >= 0 ? "+" : ""}
              {formatAxisMoney(delta)} ({deltaPct >= 0 ? "+" : ""}
              {deltaPct.toFixed(1)}%) {t("charts.customerValue.vsStart")}
            </span>
          </div>
          {showChurnForecast && (
            <div className="value-chart-churn-kpi">
              <span className="label">
                Churn tier {churnTier ?? "—"}
                {churnProbability != null ? ` · ${(churnProbability * 100).toFixed(1)}%` : ""}
              </span>
              <strong>
                {scenario === "high_lapse"
                  ? "Lapse within 3 months"
                  : t("charts.customerValue.projected", { months: forecastHorizonMonths })}
              </strong>
              <span className="muted small">
                At-risk {formatTooltipMoney(valueAtRisk)}
                {scenario === "high_lapse" && predictedLapsePeriod
                  ? ` · Lapse ${formatPeriodLabel(predictedLapsePeriod)}`
                  : ""}
              </span>
            </div>
          )}
        </div>
      </div>

      <div
        ref={canvasRef}
        className={`value-chart-canvas${fillContainer ? " value-chart-canvas-fill" : ""}`}
      >
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
        >
          <line
            x1={padX}
            y1={plotBottom}
            x2={width - padX}
            y2={plotBottom}
            className="chart-axis"
          />
          <text x={padX - 6} y={padTop} className="chart-axis-label" textAnchor="end">
            {formatAxisMoney(maxY)}
          </text>
          <text
            x={padX - 6}
            y={plotBottom}
            className="chart-axis-label"
            textAnchor="end"
          >
            {formatAxisMoney(minY)}
          </text>
          <path
            d={linePath(coverage, width, height, padX, padTop, minY, maxY, padBottom)}
            className="chart-line chart-line-coverage"
            fill="none"
          />
          <path
            d={linePath(investments, width, height, padX, padTop, minY, maxY, padBottom)}
            className="chart-line chart-line-investment"
            fill="none"
          />
          <path
            d={linePath(actualTotals, width, height, padX, padTop, minY, maxY, padBottom)}
            className="chart-line chart-line-total"
            fill="none"
          />
          {showChurnForecast && (
            <path
              d={linePath(forecastTotals, width, height, padX, padTop, minY, maxY, padBottom)}
              className="chart-line chart-line-forecast chart-line-total"
              fill="none"
            />
          )}
          {scenario === "high_lapse" && lapseIndex >= 0 && (
            (() => {
              const stepX =
                displayPoints.length > 1
                  ? (width - padX * 2) / (displayPoints.length - 1)
                  : 0;
              const x = padX + lapseIndex * stepX;
              return (
                <line
                  x1={x}
                  y1={padTop}
                  x2={x}
                  y2={plotBottom}
                  className="chart-churn-lapse-marker"
                />
              );
            })()
          )}
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
          {displayPoints.map((p, i) => {
            const { x, y } = pointCoords(
              i,
              p.total_value,
              displayPoints.length,
              width,
              height,
              padX,
              padTop,
              minY,
              maxY,
              padBottom,
            );
            const isForecast = p.kind === "forecast";
            const labelY = plotBottom + 6;
            return (
              <g key={`${p.period}-${p.kind}`}>
                <circle
                  cx={x}
                  cy={y}
                  r={activeIndex === i ? 5 : 8}
                  className="chart-hit"
                  onFocus={(e) => {
                    setActiveIndex(i);
                    const target = e.currentTarget;
                    const tRect = target.getBoundingClientRect();
                    setTooltipPos({
                      clientX: tRect.left + tRect.width / 2,
                      clientY: tRect.top,
                    });
                    setCrosshairSvgX(
                      xForIndex(i, displayPoints.length, width, padX),
                    );
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
                {xLabelIndices.has(i) && (
                  <text
                    x={x}
                    y={labelY}
                    transform={`rotate(-42 ${x} ${labelY})`}
                    className={`chart-x-label chart-x-label-rotated${isForecast ? " chart-x-forecast" : ""}`}
                    textAnchor="end"
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
            className="chart-plot-hit"
            onMouseMove={handlePlotPointer}
            onMouseLeave={clearHover}
          />
        </svg>
      </div>

      {active && tooltipPos && (
        <ChartFloatingTooltip position={tooltipPos}>
          <strong>
            {formatPeriodLabel(active.period)}
            {active.kind === "forecast" ? t("customer.valueChart.projectedSuffix") : ""}
          </strong>
          <span>
            {t("customer.valueChart.tooltipTotal", {
              amount: formatTooltipMoney(active.total_value),
            })}
          </span>
          {active.kind === "actual" && (
            <>
              <span>
                {t("customer.valueChart.tooltipInvestments", {
                  amount: formatTooltipMoney(active.investment_value),
                })}
              </span>
              <span>
                {t("customer.valueChart.tooltipCoverage", {
                  amount: formatTooltipMoney(active.coverage_value),
                })}
              </span>
            </>
          )}
          {active.is_predicted_lapse && (
            <span className="warn-stat">{t("customer.valueChart.predictedLapse")}</span>
          )}
        </ChartFloatingTooltip>
      )}

      <ul className="chart-legend chart-legend-compact">
        <li>
          <LegendSwatch visualKey="book-total" /> {t("customer.valueChart.legendActualFull")}
        </li>
        {showChurnForecast && forecastLegendLabel && (
          <li>
            <LegendSwatch visualKey="churn-book-forecast" /> {forecastLegendLabel}
          </li>
        )}
        <li>
          <LegendSwatch visualKey="book-investment" />{" "}
          {t("charts.customerValue.legendInvestmentAcc")}
        </li>
        <li>
          <LegendSwatch visualKey="book-coverage" />{" "}
          {t("charts.customerValue.legendCoverageSavings")}
        </li>
      </ul>
    </div>
  );
}
