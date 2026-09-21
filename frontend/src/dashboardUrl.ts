import { CustomerSegment, CustomerSortBy, SortOrder } from "./api";

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

export const DASHBOARD_PAGE_SIZE = 50;

export type CustomerListView = "grid" | "table";

export type DashboardUrlState = {
  segment: CustomerSegment;
  q: string;
  sortBy: CustomerSortBy;
  sortOrder: SortOrder;
  page: number;
  view: CustomerListView;
};

export function parseDashboardSearch(params: URLSearchParams): DashboardUrlState {
  const rawSegment = params.get("segment") ?? "customers_all";
  const segment = VALID_SEGMENTS.has(rawSegment)
    ? (rawSegment as CustomerSegment)
    : "customers_all";

  const rawSort = params.get("sort") ?? "customer_value";
  const sortBy = VALID_SORT.includes(rawSort as CustomerSortBy)
    ? (rawSort as CustomerSortBy)
    : "customer_value";

  const orderRaw = params.get("order");
  const sortOrder: SortOrder = orderRaw === "asc" || orderRaw === "desc" ? orderRaw : "desc";

  const pageRaw = Number.parseInt(params.get("page") ?? "1", 10);
  const page = Number.isFinite(pageRaw) && pageRaw > 0 ? pageRaw : 1;

  const viewRaw = params.get("view");
  const view: CustomerListView = viewRaw === "table" ? "table" : "grid";

  return {
    segment,
    q: params.get("q") ?? "",
    sortBy,
    sortOrder,
    page,
    view,
  };
}

export function dashboardSearchString(state: Partial<DashboardUrlState>): string {
  const params = new URLSearchParams();
  if (state.segment && state.segment !== "customers_all") {
    params.set("segment", state.segment);
  }
  if (state.q?.trim()) params.set("q", state.q.trim());
  if (state.sortBy && state.sortBy !== "customer_value") {
    params.set("sort", state.sortBy);
  }
  if (state.sortOrder && state.sortOrder !== "desc") {
    params.set("order", state.sortOrder);
  }
  if (state.page && state.page > 1) {
    params.set("page", String(state.page));
  }
  if (state.view === "table") {
    params.set("view", "table");
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function dashboardPath(state: Partial<DashboardUrlState> = {}): string {
  return `/${dashboardSearchString(state)}`;
}
