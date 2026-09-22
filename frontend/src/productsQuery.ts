import { CustomerSegment } from "./api";

const VALID_SEGMENTS = new Set<string>([
  "customers_all",
  "with_policies",
  "with_foreclosures",
  "with_investments",
  "with_insurance_status",
  "with_market_products",
]);

export type ProductsQueryState = {
  segment: CustomerSegment;
  city: string | null;
};

export function parseProductsSearch(params: URLSearchParams): ProductsQueryState {
  const rawSegment = params.get("segment") ?? "customers_all";
  const segment = VALID_SEGMENTS.has(rawSegment)
    ? (rawSegment as CustomerSegment)
    : "customers_all";
  const cityRaw = params.get("city")?.trim();
  const city = cityRaw ? cityRaw : null;
  return { segment, city };
}

export function patchProductsParams(
  prev: URLSearchParams,
  patch: Partial<{ segment: CustomerSegment; city: string | null }>,
): URLSearchParams {
  const next = new URLSearchParams(prev);
  if ("segment" in patch) {
    const seg = patch.segment ?? "customers_all";
    if (seg === "customers_all") next.delete("segment");
    else next.set("segment", seg);
  }
  if ("city" in patch) {
    const city = patch.city?.trim();
    if (!city) next.delete("city");
    else next.set("city", city);
  }
  return next;
}

export const PRODUCT_COHORT_SEGMENTS: CustomerSegment[] = [
  "customers_all",
  "with_policies",
  "with_foreclosures",
  "with_investments",
  "with_insurance_status",
  "with_market_products",
];
