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

/** X-axis labels for long monthly history (show endpoints, Jan/Jul, and light thinning). */
export function shouldShowHistoryLabel(
  period: string,
  index: number,
  count: number,
): boolean {
  if (count <= 1) return true;
  if (index === 0 || index === count - 1) return true;
  const month =
    period.length >= 7 ? Number.parseInt(period.slice(5, 7), 10) : Number.NaN;
  if (month === 1 || month === 7) return true;
  if (count > 18) {
    const step = Math.max(3, Math.ceil(count / 10));
    return index % step === 0;
  }
  return index % Math.max(1, Math.floor(count / 6)) === 0;
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
  padY: number,
  minY: number,
  maxY: number,
): string {
  const span = maxY - minY || 1;
  const stepX = values.length > 1 ? (width - padX * 2) / (values.length - 1) : 0;
  let d = "";
  let segmentOpen = false;
  values.forEach((v, i) => {
    if (v == null) {
      segmentOpen = false;
      return;
    }
    const x = padX + i * stepX;
    const y = padY + (height - padY * 2) * (1 - (v - minY) / span);
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
