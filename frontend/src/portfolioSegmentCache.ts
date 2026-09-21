import { CustomerSegment, fetchPortfolioAnalytics, PortfolioAnalytics } from "./api";

/** Overview filter keys prefetched for instant business-dashboard switching. */
export const PORTFOLIO_PREFETCH_SEGMENTS: CustomerSegment[] = [
  "customers_all",
  "with_policies",
  "with_foreclosures",
  "with_investments",
  "with_insurance_status",
  "with_market_products",
];

export type PortfolioSegmentCache = Map<CustomerSegment, PortfolioAnalytics>;

export async function prefetchPortfolioAnalytics(
  segments: CustomerSegment[] = PORTFOLIO_PREFETCH_SEGMENTS,
): Promise<PortfolioSegmentCache> {
  const entries = await Promise.all(
    segments.map(async (segment) => {
      const data = await fetchPortfolioAnalytics(segment);
      return [segment, data] as const;
    }),
  );
  return new Map(entries);
}
