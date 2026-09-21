import { useMemo, useState } from "react";
import { ChurnForecastPoint } from "../api";

type Props = {
  series: ChurnForecastPoint[];
  loading?: boolean;
  refreshing?: boolean;
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
  const span = maxY - minY || 1;
  const stepX = values.length > 1 ? (width - padX * 2) / (values.length - 1) : 0;
  let d = "";
  values.forEach((v, i) => {
    if (v == null) return;
    const x = padX + i * stepX;
    const y = padY + (height - padY * 2) * (1 - (v - minY) / span);
    d += `${d ? " L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
  });
  return d;
}

export default function PortfolioBookChart({ series, loading, refreshing }: Props) {
  const width = 720;
  const height = 200;
  const padX = 48;
  const padY = 24;
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const forecastStart = useMemo(
    () => series.findIndex((p) => p.kind === "forecast"),
    [series],
  );

  if (loading) {
    return <p className="muted small">Loading book and churn forecast…</p>;
  }

  if (series.length === 0) {
    return (
      <p className="muted small">No book history for this cohort.</p>
    );
  }

  const bookValues = series.map((p) => p.total_book_value);
  const riskValues = series.map((p) => p.value_at_risk);
  const retainedValues = series.map((p) => p.expected_retained_value);
  const allY = [...bookValues, ...riskValues, ...retainedValues];
  const minY = Math.min(...allY) * 0.92;
  const maxY = Math.max(...allY) * 1.05;

  const bookActual = series.map((p, i) =>
    forecastStart >= 0 && i >= forecastStart ? null : p.total_book_value,
  );
  const bookForecast = series.map((p, i) =>
    forecastStart >= 0 && i >= forecastStart - 1 ? p.total_book_value : i === forecastStart - 1 ? p.total_book_value : null,
  );
  // Connect at last actual point
  if (forecastStart > 0) {
    bookForecast[forecastStart - 1] = series[forecastStart - 1].total_book_value;
  }

  const active = activeIndex != null ? series[activeIndex] : null;

  return (
    <div className={`portfolio-chart-wrap${refreshing ? " value-chart-refreshing" : ""}`}>
      {refreshing && (
        <p className="value-chart-refresh-label muted small">Updating analytics…</p>
      )}
      {active && (
        <div className="chart-tooltip" role="status">
          <strong>
            {formatPeriodLabel(active.period)}
            {active.kind === "forecast" ? " (forecast)" : ""}
          </strong>
          <span>Book {formatTooltipMoney(active.total_book_value)}</span>
          <span>At risk {formatTooltipMoney(active.value_at_risk)}</span>
          <span>Retained {formatTooltipMoney(active.expected_retained_value)}</span>
        </div>
      )}
      <div className="value-chart-canvas">
        <svg
          className="value-chart-svg portfolio-chart-svg"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label="Book value and churn-adjusted forecast"
          onMouseLeave={() => setActiveIndex(null)}
        >
          {forecastStart > 0 && (
            <line
              x1={padX + ((forecastStart - 0.5) / (series.length - 1)) * (width - padX * 2)}
              y1={padY}
              x2={padX + ((forecastStart - 0.5) / (series.length - 1)) * (width - padX * 2)}
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
            {formatAxisMoney(maxY)}
          </text>
          <path
            d={linePath(retainedValues, width, height, padX, padY, minY, maxY)}
            className="chart-line chart-line-retained"
            fill="none"
          />
          <path
            d={linePath(riskValues, width, height, padX, padY, minY, maxY)}
            className="chart-line chart-line-risk"
            fill="none"
          />
          <path
            d={linePath(bookActual, width, height, padX, padY, minY, maxY)}
            className="chart-line chart-line-total"
            fill="none"
          />
          <path
            d={linePath(bookForecast, width, height, padX, padY, minY, maxY)}
            className="chart-line chart-line-forecast"
            fill="none"
          />
          {series.map((p, i) => {
            const stepX =
              series.length > 1 ? (width - padX * 2) / (series.length - 1) : 0;
            const x = padX + i * stepX;
            const y =
              padY +
              (height - padY * 2) *
                (1 - (p.total_book_value - minY) / (maxY - minY || 1));
            const showLabel =
              i === 0 ||
              i === series.length - 1 ||
              i % Math.max(1, Math.floor(series.length / 8)) === 0;
            return (
              <g key={`${p.period}-${p.kind}`}>
                <circle
                  cx={x}
                  cy={y}
                  r={8}
                  className="chart-hit"
                  onMouseEnter={() => setActiveIndex(i)}
                  tabIndex={0}
                  onFocus={() => setActiveIndex(i)}
                />
                {showLabel && (
                  <text
                    x={x}
                    y={height - 6}
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
      <ul className="chart-legend">
        <li>
          <span className="swatch swatch-total" /> Total book value
        </li>
        <li>
          <span className="swatch swatch-forecast" /> Retained book (forecast)
        </li>
        <li>
          <span className="swatch swatch-risk" /> Value at churn risk
        </li>
        <li>
          <span className="swatch swatch-retained" /> Expected retained value
        </li>
      </ul>
    </div>
  );
}
