import { CustomerSegment } from "./api";
import { parseCustomerSegment } from "./customerSegments";

export type ProductsQueryState = {
  segment: CustomerSegment;
  city: string | null;
};

export function parseProductsSearch(params: URLSearchParams): ProductsQueryState {
  const segment = parseCustomerSegment(params.get("segment"));
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
