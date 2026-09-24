import { CustomerSegment } from "./api";

/** Canonical overview / cohort filter keys (business, products, portfolio prefetch). */
export const CUSTOMER_SEGMENTS: CustomerSegment[] = [
  "customers_all",
  "with_policies",
  "with_foreclosures",
  "with_investments",
  "with_insurance_status",
  "with_market_products",
];

const VALID_SEGMENTS = new Set<string>(CUSTOMER_SEGMENTS);

export function parseCustomerSegment(raw: string | null | undefined): CustomerSegment {
  const value = raw ?? "customers_all";
  return VALID_SEGMENTS.has(value) ? (value as CustomerSegment) : "customers_all";
}
