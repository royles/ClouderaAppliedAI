import i18n from "./i18n";

export type ChartValueMetric = "total" | "investment" | "coverage" | "at_risk";

const VALID_METRICS = new Set<string>(["total", "investment", "coverage", "at_risk"]);

export function parseChartMetric(raw: string | null): ChartValueMetric | null {
  if (!raw) return null;
  const key = raw.trim().toLowerCase();
  return VALID_METRICS.has(key) ? (key as ChartValueMetric) : null;
}

export function chartMetricLabel(metric: ChartValueMetric): string {
  return i18n.t(`customer.directory.chartFilter.metrics.${metric}`);
}

export type ChartPeriodSelection = {
  period: string;
  kind?: string;
};
