import { CustomerSegment, fetchPortfolioAnalytics, PortfolioAnalytics } from "./api";
import { CUSTOMER_SEGMENTS } from "./customerSegments";

/** Overview filter keys prefetched for instant business-dashboard switching. */
export const PORTFOLIO_PREFETCH_SEGMENTS = CUSTOMER_SEGMENTS;

export type PortfolioSegmentCache = Map<CustomerSegment, PortfolioAnalytics>;

/** Avoid sharing nested arrays/objects across cache entries. */
export function clonePortfolioAnalytics(data: PortfolioAnalytics): PortfolioAnalytics {
  return {
    ...data,
    kpis: { ...data.kpis },
    kpi_targets: data.kpi_targets ? { ...data.kpi_targets } : undefined,
    value_points: data.value_points.map((p) => ({ ...p })),
    investment_returns: data.investment_returns.map((p) => ({ ...p })),
    churn_forecast: data.churn_forecast.map((p) => ({ ...p })),
    savings_aum_trend: data.savings_aum_trend?.map((p) => ({ ...p })),
    premium_momentum_trend: data.premium_momentum_trend?.map((p) => ({ ...p })),
    engagement_trend: data.engagement_trend?.map((p) => ({ ...p })),
  };
}

export function portfolioAnalyticsMatchesSegment(
  data: PortfolioAnalytics | null | undefined,
  segment: CustomerSegment,
): boolean {
  return data != null && data.segment === segment;
}

export function portfolioChartScopeKey(
  segment: CustomerSegment,
  data: PortfolioAnalytics | null | undefined,
): string {
  if (!data || data.segment !== segment) return `${segment}:pending`;
  const last = data.value_points[data.value_points.length - 1];
  return `${segment}:${data.kpis.active_customers}:${data.kpis.total_book_value}:${last?.period ?? "none"}`;
}

export async function prefetchPortfolioAnalytics(
  segments: CustomerSegment[] = PORTFOLIO_PREFETCH_SEGMENTS,
): Promise<PortfolioSegmentCache> {
  const entries = await Promise.all(
    segments.map(async (segment) => {
      const data = await fetchPortfolioAnalytics(segment);
      return [segment, clonePortfolioAnalytics(data)] as const;
    }),
  );
  return new Map(entries);
}
