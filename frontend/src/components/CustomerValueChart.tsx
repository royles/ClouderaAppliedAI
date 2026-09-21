import { ValueHistoryPoint } from "../api";

type Props = {
  title: string;
  subtitle?: string;
  points: ValueHistoryPoint[];
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

function linePath(
  values: number[],
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
  return values
    .map((v, i) => {
      const x = padX + i * stepX;
      const y = padY + (height - padY * 2) * (1 - (v - minY) / span);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export default function CustomerValueChart({
  title,
  subtitle,
  points,
  loading,
  refreshing,
}: Props) {
  const width = 640;
  const height = 168;
  const padX = 44;
  const padY = 22;

  if (loading) {
    return (
      <div className="value-chart-wrap in-panel">
        <h2 className="subsection-title">{title}</h2>
        <p className="muted small">Loading value history…</p>
      </div>
    );
  }

  if (points.length === 0) {
    return (
      <div className="value-chart-wrap in-panel">
        <h2 className="subsection-title">{title}</h2>
        <p className="muted small">No historical value snapshots for this selection.</p>
      </div>
    );
  }

  const totals = points.map((p) => p.total_value);
  const investments = points.map((p) => p.investment_value);
  const coverage = points.map((p) => p.coverage_value);
  const allY = [...totals, ...investments, ...coverage];
  const minY = Math.min(...allY) * 0.95;
  const maxY = Math.max(...allY) * 1.05;

  const first = points[0].total_value;
  const last = points[points.length - 1].total_value;
  const delta = last - first;
  const deltaPct = first > 0 ? (delta / first) * 100 : 0;

  return (
    <div
      className={`value-chart-wrap in-panel${refreshing ? " value-chart-refreshing" : ""}`}
    >
      {refreshing && (
        <p className="value-chart-refresh-label muted small">Updating chart…</p>
      )}
      <div className="panel-head value-chart-head">
        <div>
          <h2 className="subsection-title">{title}</h2>
          {subtitle && <p className="muted small">{subtitle}</p>}
        </div>
        <div className="value-chart-kpi">
          <span className="label">Latest total</span>
          <strong>{formatAxisMoney(last)}</strong>
          <span className={`small ${delta >= 0 ? "delta-up" : "delta-down"}`}>
            {delta >= 0 ? "+" : ""}
            {formatAxisMoney(delta)} ({deltaPct >= 0 ? "+" : ""}
            {deltaPct.toFixed(1)}%) vs start
          </span>
        </div>
      </div>

      <div className="value-chart-canvas">
      <svg
        className="value-chart-svg"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Customer value over time"
      >
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
          d={linePath(totals, width, height, padX, padY, minY, maxY)}
          className="chart-line chart-line-total"
          fill="none"
        />
        {points.map((p, i) => {
          const stepX =
            points.length > 1 ? (width - padX * 2) / (points.length - 1) : 0;
          const x = padX + i * stepX;
          return (
            <text
              key={p.period}
              x={x}
              y={height - 6}
              className="chart-x-label"
              textAnchor="middle"
            >
              {formatPeriodLabel(p.period)}
            </text>
          );
        })}
      </svg>
      </div>

      <ul className="chart-legend">
        <li>
          <span className="swatch swatch-total" /> Total customer value
        </li>
        <li>
          <span className="swatch swatch-investment" /> Investment accumulation
        </li>
        <li>
          <span className="swatch swatch-coverage" /> Coverage & savings (matzav)
        </li>
      </ul>
    </div>
  );
}
