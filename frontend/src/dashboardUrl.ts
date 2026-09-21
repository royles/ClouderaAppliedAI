import { CustomerSegment } from "./api";
import { BUSINESS_BASE } from "./appRoutes";
import {
  cohortSearchString,
  CUSTOMER_PAGE_SIZE,
  CustomerListView,
  CohortQueryState,
  parseBusinessSegment,
  patchBusinessSegment,
} from "./cohortQuery";

export {
  CUSTOMER_PAGE_SIZE as DASHBOARD_PAGE_SIZE,
  parseBusinessSegment,
  patchBusinessSegment,
  type CustomerListView,
};

/** @deprecated Business page only uses segment; prefer parseBusinessSegment. */
export type DashboardUrlState = CohortQueryState;

/** @deprecated Prefer parseBusinessSegment on /business. */
export function parseDashboardSearch(params: URLSearchParams): DashboardUrlState {
  return {
    segment: parseBusinessSegment(params),
    q: "",
    sortBy: "churn_risk",
    sortOrder: "desc",
    page: 1,
    view: "grid",
    asOf: null,
    metric: null,
  };
}

export function dashboardSearchString(state: { segment?: CustomerSegment } = {}): string {
  return cohortSearchString({ segment: state.segment ?? "customers_all" });
}

export function dashboardPath(state: { segment?: CustomerSegment } = {}): string {
  return `${BUSINESS_BASE}${dashboardSearchString(state)}`;
}
