export type ChartValueMetric = "total" | "investment" | "coverage" | "at_risk";

const VALID_METRICS = new Set<string>(["total", "investment", "coverage", "at_risk"]);

export function parseChartMetric(raw: string | null): ChartValueMetric | null {
  if (!raw) return null;
  const key = raw.trim().toLowerCase();
  return VALID_METRICS.has(key) ? (key as ChartValueMetric) : null;
}

export function chartMetricLabel(metric: ChartValueMetric): string {
  switch (metric) {
    case "investment":
      return "investment balance";
    case "coverage":
      return "coverage & savings";
    case "at_risk":
      return "value at churn risk (book × churn probability at snapshot)";
    default:
      return "total book value";
  }
}

export type ChartPeriodSelection = {
  period: string;
  kind?: string;
};
