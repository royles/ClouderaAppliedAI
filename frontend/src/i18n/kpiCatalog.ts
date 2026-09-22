import type { TFunction } from "i18next";

const KPI_TITLE_KEYS: Record<string, string> = {
  total_book_value: "business.portfolio.kpi.totalBookValue",
  active_customers: "business.portfolio.kpi.activeCustomers",
  annual_retention_rate_forecast: "business.portfolio.kpi.retentionForecast",
  value_at_risk_12m: "business.portfolio.kpi.valueAtChurnRisk",
  avg_customer_value: "business.portfolio.kpi.avgCustomerValue",
  high_risk_book_pct: "business.portfolio.kpi.highRiskBookShare",
  book_growth_pct: "business.portfolio.kpi.bookGrowthHistory",
};

export function kpiBenchmarkLabel(t: TFunction, kpiKey: string, fallback: string): string {
  const mapped = KPI_TITLE_KEYS[kpiKey];
  if (mapped) return t(mapped);
  return fallback;
}

export function kpiBenchmarkDescription(
  t: TFunction,
  kpiKey: string,
  fallback: string | null | undefined,
): string | null {
  if (!fallback) return null;
  return t(`admin.kpiBenchmarks.descriptions.${kpiKey}`, { defaultValue: fallback });
}

export function kpiDirectionLabel(t: TFunction, direction: string): string {
  return t(`admin.kpiBenchmarks.direction.${direction}`, { defaultValue: direction });
}

export function kpiUnitKindLabel(t: TFunction, unitKind: string): string {
  return t(`admin.kpiBenchmarks.unitKind.${unitKind}`, { defaultValue: unitKind });
}
