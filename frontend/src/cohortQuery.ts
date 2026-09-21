import { CustomerSegment, CustomerSortBy, SortOrder } from "./api";
import { ChartValueMetric, parseChartMetric } from "./chartFilter";

const VALID_SEGMENTS = new Set<string>([
  "customers_all",
  "with_policies",
  "with_foreclosures",
  "with_investments",
  "with_insurance_status",
  "with_market_products",
]);

const VALID_SORT: CustomerSortBy[] = [
  "customer_value",
  "churn_risk",
  "name",
  "policy_count",
  "investment_count",
];

export const CUSTOMER_PAGE_SIZE_OPTIONS = [25, 50, 100] as const;
export type CustomerPageSize = (typeof CUSTOMER_PAGE_SIZE_OPTIONS)[number];
export const DEFAULT_CUSTOMER_PAGE_SIZE: CustomerPageSize = 50;
export const MAX_CUSTOMER_PAGE_SIZE = 100;

/** @deprecated use DEFAULT_CUSTOMER_PAGE_SIZE or url state pageSize */
export const CUSTOMER_PAGE_SIZE = DEFAULT_CUSTOMER_PAGE_SIZE;

function parsePageSize(raw: string | null): CustomerPageSize {
  const n = Number.parseInt(raw ?? "", 10);
  if (CUSTOMER_PAGE_SIZE_OPTIONS.includes(n as CustomerPageSize)) {
    return n as CustomerPageSize;
  }
  return DEFAULT_CUSTOMER_PAGE_SIZE;
}

export type CustomerListView = "grid" | "table";

export type CohortQueryState = {
  segment: CustomerSegment;
  q: string;
  sortBy: CustomerSortBy;
  sortOrder: SortOrder;
  page: number;
  pageSize: CustomerPageSize;
  view: CustomerListView;
  asOf: string | null;
  metric: ChartValueMetric | null;
};

export function parseCohortSearch(params: URLSearchParams): CohortQueryState {
  const rawSegment = params.get("segment") ?? "customers_all";
  const segment = VALID_SEGMENTS.has(rawSegment)
    ? (rawSegment as CustomerSegment)
    : "customers_all";

  const rawSort = params.get("sort") ?? "churn_risk";
  const sortBy = VALID_SORT.includes(rawSort as CustomerSortBy)
    ? (rawSort as CustomerSortBy)
    : "churn_risk";

  const orderRaw = params.get("order");
  const sortOrder: SortOrder = orderRaw === "asc" || orderRaw === "desc" ? orderRaw : "desc";

  const pageRaw = Number.parseInt(params.get("page") ?? "1", 10);
  const page = Number.isFinite(pageRaw) && pageRaw > 0 ? pageRaw : 1;

  const viewRaw = params.get("view");
  const view: CustomerListView = viewRaw === "table" ? "table" : "grid";

  const asOfRaw = params.get("as_of")?.trim();
  const asOf = asOfRaw ? asOfRaw : null;
  const metric = parseChartMetric(params.get("metric"));

  const pageSize = parsePageSize(params.get("page_size"));

  return {
    segment,
    q: params.get("q") ?? "",
    sortBy,
    sortOrder,
    page,
    pageSize,
    view,
    asOf,
    metric,
  };
}

export function cohortSearchString(state: Partial<CohortQueryState>): string {
  const params = new URLSearchParams();
  if (state.segment && state.segment !== "customers_all") {
    params.set("segment", state.segment);
  }
  if (state.q?.trim()) params.set("q", state.q.trim());
  if (state.sortBy && state.sortBy !== "churn_risk") {
    params.set("sort", state.sortBy);
  }
  if (state.sortOrder && state.sortOrder !== "desc") {
    params.set("order", state.sortOrder);
  }
  if (state.page && state.page > 1) {
    params.set("page", String(state.page));
  }
  if (state.pageSize && state.pageSize !== DEFAULT_CUSTOMER_PAGE_SIZE) {
    params.set("page_size", String(state.pageSize));
  }
  if (state.view === "table") {
    params.set("view", "table");
  }
  if (state.asOf) params.set("as_of", state.asOf);
  if (state.metric) params.set("metric", state.metric);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function patchCohortParams(
  prev: URLSearchParams,
  patch: Partial<{
    segment: CustomerSegment;
    q: string | null;
    sortBy: CustomerSortBy;
    sortOrder: SortOrder;
    page: number | null;
    pageSize: CustomerPageSize | null;
    view: CustomerListView | null;
    asOf: string | null;
    metric: ChartValueMetric | null;
  }>,
): URLSearchParams {
  const next = new URLSearchParams(prev);
  const apply = (key: string, value: string | null, omitWhen?: string) => {
    if (value == null || value === "" || value === omitWhen) next.delete(key);
    else next.set(key, value);
  };
  if ("segment" in patch) apply("segment", patch.segment ?? null, "customers_all");
  if ("q" in patch) apply("q", patch.q ?? null);
  if ("sortBy" in patch) apply("sort", patch.sortBy ?? null, "churn_risk");
  if ("sortOrder" in patch) apply("order", patch.sortOrder ?? null, "desc");
  if ("page" in patch) {
    const p = patch.page;
    apply("page", p == null || p <= 1 ? null : String(p));
  }
  if ("pageSize" in patch) {
    const ps = patch.pageSize;
    apply(
      "page_size",
      ps == null || ps === DEFAULT_CUSTOMER_PAGE_SIZE ? null : String(ps),
    );
  }
  if ("view" in patch) apply("view", patch.view ?? null, "grid");
  if ("asOf" in patch) apply("as_of", patch.asOf ?? null);
  if ("metric" in patch) apply("metric", patch.metric ?? null);
  return next;
}

/** Business portfolio view: segment filter only. */
export function parseBusinessSegment(params: URLSearchParams): CustomerSegment {
  return parseCohortSearch(params).segment;
}

export function patchBusinessSegment(
  prev: URLSearchParams,
  segment: CustomerSegment,
): URLSearchParams {
  const next = new URLSearchParams();
  if (segment !== "customers_all") {
    next.set("segment", segment);
  }
  return next;
}
