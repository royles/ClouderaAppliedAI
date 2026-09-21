import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import {
  CustomerSegment,
  CustomerSortBy,
  CustomerSummary,
  DomainCount,
  SortOrder,
  fetchCustomers,
} from "../api";
import { CUSTOMER_BASE } from "../appRoutes";
import {
  CUSTOMER_PAGE_SIZE_OPTIONS,
  CustomerListView,
  CustomerPageSize,
  CohortQueryState,
  parseCohortSearch,
  patchCohortParams,
} from "../cohortQuery";
import { chartMetricLabel } from "../chartFilter";
import { formatPeriodLabel } from "./charts/analyticsChartUtils";
import CustomerCardGrid from "./CustomerCardGrid";
import CustomerListTable from "./CustomerListTable";

type Props = {
  segment: CustomerSegment;
  overviewDomains?: DomainCount[] | null;
  overviewReady: boolean;
  onClearFilter?: () => void;
};

export default function CustomerDirectoryPanel({
  segment,
  overviewDomains,
  overviewReady,
  onClearFilter,
}: Props) {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const urlState: CohortQueryState = useMemo(
    () => parseCohortSearch(searchParams),
    [searchParams],
  );
  const { sortBy, sortOrder, page, pageSize, view, asOf, metric } = urlState;
  const effectiveSegment = segment;

  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [listTotal, setListTotal] = useState(0);
  const [listTruncated, setListTruncated] = useState(false);
  const [search, setSearch] = useState(urlState.q);
  const [debouncedSearch, setDebouncedSearch] = useState(urlState.q);
  const [error, setError] = useState<string | null>(null);
  const [tableLoading, setTableLoading] = useState(false);
  const customersRequestRef = useRef(0);

  const listReturn = location.pathname + location.search;

  useEffect(() => {
    setSearch(urlState.q);
    setDebouncedSearch(urlState.q);
  }, [urlState.q]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      const trimmed = search.trim();
      setDebouncedSearch(trimmed);
      setSearchParams(
        (prev) => {
          const currentQ = prev.get("q") ?? "";
          if (currentQ === trimmed) return prev;
          return patchCohortParams(prev, { q: trimmed || null, page: 1 });
        },
        { replace: true },
      );
    }, 300);
    return () => window.clearTimeout(handle);
  }, [search, setSearchParams]);

  const activeDomain = useMemo((): DomainCount | null => {
    if (effectiveSegment === "customers_all" || !overviewDomains) return null;
    const match = overviewDomains.find((d) => d.filter_key === effectiveSegment);
    return match ?? null;
  }, [effectiveSegment, overviewDomains]);

  useEffect(() => {
    if (location.pathname !== CUSTOMER_BASE) return;

    const requestId = ++customersRequestRef.current;
    let cancelled = false;
    const offset = (page - 1) * pageSize;

    (async () => {
      setTableLoading(true);
      try {
        const result = await fetchCustomers({
          q: debouncedSearch,
          segment: effectiveSegment,
          sortBy,
          sortOrder,
          limit: pageSize,
          offset,
          asOf,
          metric: asOf ? (metric ?? "total") : null,
        });
        if (cancelled || requestId !== customersRequestRef.current) return;
        setCustomers(result.customers);
        setListTotal(result.total);
        setListTruncated(result.truncated);
        setError(null);
      } catch (e) {
        if (cancelled || requestId !== customersRequestRef.current) return;
        setError(e instanceof Error ? e.message : "Failed to load customers");
      } finally {
        if (requestId === customersRequestRef.current) {
          setTableLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
      customersRequestRef.current += 1;
    };
  }, [
    debouncedSearch,
    effectiveSegment,
    sortBy,
    sortOrder,
    page,
    pageSize,
    location.pathname,
    location.key,
    asOf,
    metric,
  ]);

  const clearChartFilter = () => {
    setSearchParams(
      (prev) => patchCohortParams(prev, { asOf: null, metric: null, page: 1 }),
      { replace: true },
    );
  };

  const setRankBy = (by: CustomerSortBy) => {
    const order: SortOrder =
      by === "customer_value" ||
      by === "churn_risk" ||
      by === "policy_count" ||
      by === "investment_count"
        ? "desc"
        : "asc";
    setSearchParams(
      (prev) => patchCohortParams(prev, { sortBy: by, sortOrder: order, page: 1 }),
      { replace: true },
    );
  };

  const toggleSortOrder = () => {
    setSearchParams(
      (prev) =>
        patchCohortParams(prev, {
          sortOrder: sortOrder === "asc" ? "desc" : "asc",
          page: 1,
        }),
      { replace: true },
    );
  };

  const toggleColumnSort = (by: CustomerSortBy) => {
    if (sortBy === by) toggleSortOrder();
    else setRankBy(by);
  };

  const setListView = (next: CustomerListView) => {
    setSearchParams((prev) => patchCohortParams(prev, { view: next }), {
      replace: true,
    });
  };

  const pageCount = Math.max(1, Math.ceil(listTotal / pageSize));
  const showingFrom = listTotal === 0 ? 0 : (page - 1) * pageSize + 1;
  const showingTo = Math.min(page * pageSize, listTotal);

  const setPageSize = (next: CustomerPageSize) => {
    setSearchParams(
      (prev) => patchCohortParams(prev, { pageSize: next, page: 1 }),
      { replace: true },
    );
  };

  useEffect(() => {
    if (page <= pageCount) return;
    setSearchParams((prev) => patchCohortParams(prev, { page: pageCount }), {
      replace: true,
    });
  }, [page, pageCount, setSearchParams]);

  const showRank =
    sortBy === "customer_value" ||
    sortBy === "churn_risk" ||
    sortBy === "policy_count" ||
    sortBy === "investment_count";

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Customers</h2>
          {asOf ? (
            <p className="filter-banner chart-date-filter-banner">
              Chart snapshot: <strong>{formatPeriodLabel(asOf)}</strong> (
              {chartMetricLabel(metric ?? "total")})
              <button type="button" className="link-btn" onClick={clearChartFilter}>
                Clear date filter
              </button>
            </p>
          ) : activeDomain ? (
            <p className="filter-banner">
              Filter: <strong>{activeDomain.domain}</strong>
              {onClearFilter && (
                <button type="button" className="link-btn" onClick={onClearFilter}>
                  Clear filter
                </button>
              )}
            </p>
          ) : (
            <p className="muted small">Showing all current customers in this cohort</p>
          )}
        </div>
        <div className="toolbar">
          <div className="toolbar-item">
            <label htmlFor="customer-sort-by">Rank by</label>
            <select
              id="customer-sort-by"
              className="control"
              value={sortBy}
              onChange={(e) => setRankBy(e.target.value as CustomerSortBy)}
            >
              <option value="churn_risk">Churn, then value</option>
              <option value="customer_value">Value, then churn</option>
              <option value="name">Name (A–Z)</option>
              <option value="policy_count">Policy count</option>
              <option value="investment_count">Investment tracks</option>
            </select>
          </div>
          <button type="button" className="control control-btn" onClick={toggleSortOrder}>
            {sortBy === "customer_value"
              ? sortOrder === "desc"
                ? "Highest value first ↓"
                : "Lowest value first ↑"
              : sortBy === "churn_risk"
                ? sortOrder === "desc"
                  ? "High risk first ↓"
                  : "Low risk first ↑"
                : sortOrder === "desc"
                  ? "Highest first ↓"
                  : "Lowest first ↑"}
          </button>
          <div className="toolbar-item toolbar-item-grow">
            <label htmlFor="customer-search">Search</label>
            <input
              id="customer-search"
              className="control control-search"
              placeholder="Name or customer ID"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="toolbar-item">
            <span className="toolbar-label-static" id="customer-view-label">
              Layout
            </span>
            <div
              className="view-toggle"
              role="group"
              aria-labelledby="customer-view-label"
            >
              <button
                type="button"
                className={`view-toggle-btn${view === "grid" ? " is-active" : ""}`}
                aria-pressed={view === "grid"}
                onClick={() => setListView("grid")}
              >
                Cards
              </button>
              <button
                type="button"
                className={`view-toggle-btn${view === "table" ? " is-active" : ""}`}
                aria-pressed={view === "table"}
                onClick={() => setListView("table")}
              >
                Table
              </button>
            </div>
          </div>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      <div
        className={`customer-list-wrap${tableLoading ? " customer-list-loading" : ""}${
          view === "table" ? " customer-list-wrap-table" : ""
        }`}
      >
        {tableLoading && (
          <p className="table-loading-label muted">
            Updating {view === "grid" ? "cards" : "table"}…
          </p>
        )}
        {view === "grid" ? (
          <CustomerCardGrid
            customers={customers}
            showRank={showRank}
            rankStart={showingFrom}
            dashboardReturn={listReturn}
          />
        ) : (
          <div className="table-wrap">
            <CustomerListTable
              customers={customers}
              showRank={showRank}
              rankStart={showingFrom}
              dashboardReturn={listReturn}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onToggleColumnSort={toggleColumnSort}
            />
          </div>
        )}
      </div>
      <div className="table-footer">
        <p className="muted small">
          {listTotal === 0
            ? "No matching customers"
            : `Showing ${showingFrom.toLocaleString()}–${showingTo.toLocaleString()} of ${listTotal.toLocaleString()}`}
          {listTotal > 0 && ` · up to ${pageSize} per page`}
        </p>
        {listTotal > 0 && (
          <div className="pagination">
            <div className="toolbar-item pagination-page-size">
              <label htmlFor="customer-page-size">Per page</label>
              <select
                id="customer-page-size"
                className="control"
                value={pageSize}
                disabled={tableLoading}
                onChange={(e) => setPageSize(Number(e.target.value) as CustomerPageSize)}
              >
                {CUSTOMER_PAGE_SIZE_OPTIONS.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>
            {pageCount > 1 && (
              <>
                <button
                  type="button"
                  className="control control-btn"
                  disabled={page <= 1 || tableLoading}
                  onClick={() =>
                    setSearchParams(
                      (prev) => patchCohortParams(prev, { page: page - 1 }),
                      { replace: true },
                    )
                  }
                >
                  Previous
                </button>
                <span className="muted small">
                  Page {page} of {pageCount}
                </span>
                <button
                  type="button"
                  className="control control-btn"
                  disabled={page >= pageCount || tableLoading}
                  onClick={() =>
                    setSearchParams(
                      (prev) => patchCohortParams(prev, { page: page + 1 }),
                      { replace: true },
                    )
                  }
                >
                  Next
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
