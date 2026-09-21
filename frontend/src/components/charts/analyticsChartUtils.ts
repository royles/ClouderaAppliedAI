export function formatPeriodLabel(period: string) {
  if (period.length >= 7) {
    const [y, m] = period.split("-");
    const month = new Date(Number(y), Number(m) - 1, 1).toLocaleString("en-GB", {
      month: "short",
    });
    return `${month} ${y?.slice(2)}`;
  }
  return period;
}

/** Minimum horizontal gap between x-axis tick labels (px in SVG viewBox). */
export const CHART_X_LABEL_MIN_GAP = 56;

/**
 * Pick x-axis label indices so labels do not overlap at the given plot width.
 * Always includes first and last points; interior ticks are evenly spaced.
 */
export function historyLabelIndicesForPlot(
  count: number,
  width: number,
  padX: number,
  minGapPx: number = CHART_X_LABEL_MIN_GAP,
): number[] {
  if (count <= 0) return [];
  if (count === 1) return [0];
  const plotWidth = Math.max(1, width - padX * 2);
  const maxLabels = Math.max(2, Math.floor(plotWidth / minGapPx));
  if (maxLabels >= count) {
    return Array.from({ length: count }, (_, i) => i);
  }
  const indices = new Set<number>([0, count - 1]);
  const interior = maxLabels - 2;
  for (let k = 1; k <= interior; k += 1) {
    const idx = Math.round((k / (interior + 1)) * (count - 1));
    if (idx > 0 && idx < count - 1) indices.add(idx);
  }
  return [...indices].sort((a, b) => a - b);
}

/** Compact month label for crowded x-axes (e.g. Jan '21). */
export function formatPeriodAxisLabel(period: string) {
  if (period.length >= 7) {
    const [y, m] = period.split("-");
    const month = new Date(Number(y), Number(m) - 1, 1).toLocaleString("en-GB", {
      month: "short",
    });
    return `${month} '${y?.slice(2) ?? ""}`;
  }
  return period;
}

export function shouldShowHistoryLabel(
  _period: string,
  index: number,
  count: number,
  layout?: { width: number; padX: number },
): boolean {
  const width = layout?.width ?? 640;
  const padX = layout?.padX ?? 44;
  return historyLabelIndicesForPlot(count, width, padX).includes(index);
}

export function formatAxisMoney(n: number) {
  if (n >= 1_000_000) return `₪${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `₪${(n / 1_000).toFixed(0)}K`;
  return `₪${n.toFixed(0)}`;
}

export function formatTooltipMoney(n: number) {
  return new Intl.NumberFormat("en-IL", {
    style: "currency",
    currency: "ILS",
    maximumFractionDigits: 0,
  }).format(n);
}

export function formatAxisPct(n: number) {
  return `${n.toFixed(1)}%`;
}

export function formatAxisCount(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 10_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(Math.round(n));
}

export function formatTooltipCount(n: number) {
  return n.toLocaleString();
}

/** Shared stroke styles — legend swatches use the same tokens as chart paths. */
export type SeriesVisualKey =
  | "book-total"
  | "book-investment"
  | "book-coverage"
  | "churn-retained"
  | "churn-at-risk"
  | "churn-book-actual"
  | "churn-book-forecast"
  | "return-cumulative"
  | "return-period"
  | "return-balance"
  | "obj-aum"
  | "obj-savers"
  | "obj-premium"
  | "obj-policies"
  | "obj-engagement"
  | "obj-digital"
  | "book-baseline-total"
  | "churn-baseline-book"
  | "return-baseline-balance";

export const SERIES_VISUAL: Record<
  SeriesVisualKey,
  { stroke: string; strokeWidth: number; strokeDasharray?: string; opacity?: number }
> = {
  "book-total": { stroke: "#0f3d5e", strokeWidth: 2 },
  "book-investment": { stroke: "#0f6db8", strokeWidth: 1.5 },
  "book-coverage": { stroke: "#8a96a3", strokeWidth: 1.25, strokeDasharray: "4 3" },
  "churn-retained": { stroke: "#1e6b34", strokeWidth: 1.5 },
  "churn-at-risk": { stroke: "#c47a0a", strokeWidth: 1.5, strokeDasharray: "5 3" },
  "churn-book-actual": { stroke: "#0f3d5e", strokeWidth: 2 },
  "churn-book-forecast": {
    stroke: "#0f6db8",
    strokeWidth: 1.75,
    strokeDasharray: "6 4",
    opacity: 0.9,
  },
  "return-cumulative": { stroke: "#0f6db8", strokeWidth: 2 },
  "return-period": { stroke: "#c47a0a", strokeWidth: 1.5, strokeDasharray: "4 3" },
  "return-balance": { stroke: "#0f6db8", strokeWidth: 2 },
  "obj-aum": { stroke: "#0f3d5e", strokeWidth: 2 },
  "obj-savers": { stroke: "#5a7a9a", strokeWidth: 1.5, strokeDasharray: "4 3" },
  "obj-premium": { stroke: "#0f6db8", strokeWidth: 2 },
  "obj-policies": { stroke: "#1e6b34", strokeWidth: 1.5, strokeDasharray: "5 3" },
  "obj-engagement": { stroke: "#0f3d5e", strokeWidth: 2 },
  "obj-digital": { stroke: "#c47a0a", strokeWidth: 1.5, strokeDasharray: "4 3" },
  "book-baseline-total": {
    stroke: "#94a3b8",
    strokeWidth: 2.25,
    strokeDasharray: "7 5",
    opacity: 0.85,
  },
  "churn-baseline-book": {
    stroke: "#94a3b8",
    strokeWidth: 2.25,
    strokeDasharray: "7 5",
    opacity: 0.85,
  },
  "return-baseline-balance": {
    stroke: "#94a3b8",
    strokeWidth: 2,
    strokeDasharray: "7 5",
    opacity: 0.85,
  },
};

export function linePath(
  values: (number | null)[],
  width: number,
  height: number,
  padX: number,
  padTop: number,
  minY: number,
  maxY: number,
  padBottom: number = padTop,
): string {
  const span = maxY - minY || 1;
  const stepX = values.length > 1 ? (width - padX * 2) / (values.length - 1) : 0;
  const plotHeight = Math.max(1, height - padTop - padBottom);
  let d = "";
  let segmentOpen = false;
  values.forEach((v, i) => {
    if (v == null) {
      segmentOpen = false;
      return;
    }
    const x = padX + i * stepX;
    const y = padTop + plotHeight * (1 - (v - minY) / span);
    if (!segmentOpen) {
      d += `${d ? " " : ""}M${x.toFixed(1)},${y.toFixed(1)}`;
      segmentOpen = true;
    } else {
      d += ` L${x.toFixed(1)},${y.toFixed(1)}`;
    }
  });
  return d;
}

export function seriesHasPoints(values: (number | null)[]): boolean {
  return values.some((v) => v != null);
}

export type ChartValueFormat = "money" | "percent" | "count";

export type ChartSeries = {
  id: string;
  visualKey: SeriesVisualKey;
  label: string;
  values: (number | null)[];
  /** When set with a different primary valueFormat, uses the right-hand scale. */
  axis?: "primary" | "secondary";
  valueFormat?: ChartValueFormat;
};
