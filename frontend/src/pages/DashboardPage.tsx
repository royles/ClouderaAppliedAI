import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import {
  CustomerSegment,
  CustomerSortBy,
  CustomerSummary,
  DomainCount,
  fetchCustomers,
  fetchOverview,
  fetchPortfolioValueHistory,
  Overview,
  SortOrder,
  ValueHistoryPoint,
} from "../api";
import Breadcrumbs from "../components/Breadcrumbs";
import CustomerCardGrid from "../components/CustomerCardGrid";
import CustomerListTable from "../components/CustomerListTable";
import CustomerValueChart from "../components/CustomerValueChart";
import {
  CustomerListView,
  DASHBOARD_PAGE_SIZE,
  parseDashboardSearch,
} from "../dashboardUrl";

function patchDashboardParams(
  prev: URLSearchParams,
  patch: Partial<{
    segment: CustomerSegment;
    q: string | null;
    sortBy: CustomerSortBy;
    sortOrder: SortOrder;
    page: number | null;
    view: CustomerListView | null;
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
  if ("view" in patch) apply("view", patch.view ?? null, "grid");
  return next;
}

export default function DashboardPage() {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const urlState = useMemo(
    () => parseDashboardSearch(searchParams),
    [searchParams],
  );
  const { segment, sortBy, sortOrder, page, view } = urlState;

  const [overview, setOverview] = useState<Overview | null>(null);
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [listTotal, setListTotal] = useState(0);
  const [listTruncated, setListTruncated] = useState(false);
  const [search, setSearch] = useState(urlState.q);
  const [debouncedSearch, setDebouncedSearch] = useState(urlState.q);
  const [error, setError] = useState<string | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);
  const [valueHistory, setValueHistory] = useState<ValueHistoryPoint[]>([]);
  const [valueHistoryLoading, setValueHistoryLoading] = useState(true);
  const [overviewUpdatedAt, setOverviewUpdatedAt] = useState<Date | null>(null);
  const customersRequestRef = useRef(0);
  const valueHistoryRequestRef = useRef(0);
  const valueHistorySegmentRef = useRef<CustomerSegment | null>(null);

  const dashboardReturn = location.pathname + location.search;

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
          return patchDashboardParams(prev, { q: trimmed || null, page: 1 });
        },
        { replace: true },
      );
    }, 300);
    return () => window.clearTimeout(handle);
  }, [search, setSearchParams]);

  const activeDomain = useMemo((): DomainCount | null => {
    if (segment === "customers_all" || !overview?.domains) return null;
    const match = overview.domains.find((d) => d.filter_key === segment);
    return match ?? null;
  }, [segment, overview]);

  useEffect(() => {
    if (location.pathname !== "/") return;

    let cancelled = false;
    (async () => {
      setOverviewLoading(true);
      try {
        const ov = await fetchOverview();
        if (!cancelled) {
          setOverview(ov);
          setOverviewUpdatedAt(new Date());
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load overview");
        }
      } finally {
        if (!cancelled) setOverviewLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [location.pathname, location.key]);

  useEffect(() => {
    if (location.pathname !== "/" || overviewLoading) return;

    const requestId = ++customersRequestRef.current;
    let cancelled = false;
    const offset = (page - 1) * DASHBOARD_PAGE_SIZE;

    (async () => {
      setTableLoading(true);
      try {
        const result = await fetchCustomers({
          q: debouncedSearch,
          segment,
          sortBy,
          sortOrder,
          limit: DASHBOARD_PAGE_SIZE,
          offset,
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
    segment,
    sortBy,
    sortOrder,
    page,
    location.pathname,
    location.key,
    overviewLoading,
  ]);

  const loadValueHistory = useCallback(async (seg: CustomerSegment) => {
    const requestId = ++valueHistoryRequestRef.current;
    if (valueHistorySegmentRef.current !== seg) {
      setValueHistory([]);
      valueHistorySegmentRef.current = seg;
    }
    setValueHistoryLoading(true);
    try {
      const data = await fetchPortfolioValueHistory(seg);
      if (requestId !== valueHistoryRequestRef.current) return;
      setValueHistory(data.points ?? []);
    } catch {
      if (requestId === valueHistoryRequestRef.current) {
        setValueHistory([]);
      }
    } finally {
      if (requestId === valueHistoryRequestRef.current) {
        setValueHistoryLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    if (location.pathname !== "/" || overviewLoading) return;

    void loadValueHistory(segment);

    return () => {
      valueHistoryRequestRef.current += 1;
    };
  }, [
    segment,
    loadValueHistory,
    location.pathname,
    location.key,
    overviewLoading,
  ]);

  const setSegment = (next: CustomerSegment) => {
    setSearchParams((prev) => patchDashboardParams(prev, { segment: next, page: 1 }), {
      replace: true,
    });
  };

  const onCardClick = (domain: DomainCount) => {
    const key = domain.filter_key as CustomerSegment;
    setSegment(segment === key ? "customers_all" : key);
  };

  const clearFilter = () => setSegment("customers_all");

  const setRankBy = (by: CustomerSortBy) => {
    const order: SortOrder =
      by === "customer_value" ||
      by === "churn_risk" ||
      by === "policy_count" ||
      by === "investment_count"
        ? "desc"
        : "asc";
    setSearchParams(
      (prev) => patchDashboardParams(prev, { sortBy: by, sortOrder: order, page: 1 }),
      { replace: true },
    );
  };

  const toggleSortOrder = () => {
    setSearchParams(
      (prev) =>
        patchDashboardParams(prev, {
          sortOrder: sortOrder === "asc" ? "desc" : "asc",
          page: 1,
        }),
      { replace: true },
    );
  };

  const toggleColumnSort = (by: CustomerSortBy) => {
    if (sortBy === by) {
      toggleSortOrder();
      return;
    }
    setRankBy(by);
  };

  const setListView = (next: CustomerListView) => {
    setSearchParams((prev) => patchDashboardParams(prev, { view: next }), {
      replace: true,
    });
  };

  const pageCount = Math.max(1, Math.ceil(listTotal / DASHBOARD_PAGE_SIZE));
  const showingFrom = listTotal === 0 ? 0 : (page - 1) * DASHBOARD_PAGE_SIZE + 1;
  const showingTo = Math.min(page * DASHBOARD_PAGE_SIZE, listTotal);

  const showRank =
    sortBy === "customer_value" ||
    sortBy === "churn_risk" ||
    sortBy === "policy_count" ||
    sortBy === "investment_count";

  if (overviewLoading && !overview) {
    return (
      <>
        <Breadcrumbs items={[{ label: "Dashboard" }]} />
        <section className="panel">
          <div className="skeleton skeleton-title" />
          <div className="stat-grid">
            {[1, 2, 3, 4, 5].map((n) => (
              <div key={n} className="skeleton skeleton-stat" />
            ))}
          </div>
        </section>
      </>
    );
  }
  if (error && !overview) return <p className="error">{error}</p>;

  return (
    <>
      <Breadcrumbs items={[{ label: "Dashboard" }]} />
      <section className="panel">
        <div className="panel-head">
          <div>
            <h1>Warehouse overview</h1>
            <p className="muted small">
              Click a card to filter the customer table and value chart. Click again to
              clear.
            </p>
          </div>
          {overviewUpdatedAt && (
            <p className="muted small data-freshness">
              Counts refreshed {overviewUpdatedAt.toLocaleTimeString()}
            </p>
          )}
        </div>
        {overview && (
          <div className="stat-grid">
            {(overview.domains ?? []).map((d) => {
              const filterKey = d.filter_key ?? "customers_all";
              const selected = segment === filterKey;
              return (
                <button
                  key={filterKey + d.domain}
                  type="button"
                  className={`stat-card stat-card-btn${selected ? " stat-card-selected" : ""}`}
                  onClick={() =>
                    onCardClick({ ...d, filter_key: filterKey } as DomainCount)
                  }
                  title={d.description || d.domain}
                >
                  <div className="stat-value">
                    {(d.row_count ?? 0).toLocaleString()}
                  </div>
                  <div className="stat-label">{d.domain}</div>
                </button>
              );
            })}
          </div>
        )}
        <CustomerValueChart
          title="Accumulated customer value over time"
          subtitle={
            activeDomain
              ? `Filtered cohort: ${activeDomain.domain} — investment tracks plus coverage/savings snapshots (ILS).`
              : "Book-wide monthly history — investment accumulation and insurance status values (ILS)."
          }
          points={valueHistory}
          loading={valueHistoryLoading && valueHistory.length === 0}
          refreshing={valueHistoryLoading && valueHistory.length > 0}
        />
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Customers</h2>
            {activeDomain ? (
              <p className="filter-banner">
                Filter: <strong>{activeDomain.domain}</strong>
                <button type="button" className="link-btn" onClick={clearFilter}>
                  Clear filter
                </button>
              </p>
            ) : (
              <p className="muted small">Showing all current customers</p>
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
            <button
              type="button"
              className="control control-btn"
              onClick={toggleSortOrder}
            >
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
              dashboardReturn={dashboardReturn}
            />
          ) : (
            <div className="table-wrap">
              <CustomerListTable
                customers={customers}
                showRank={showRank}
                rankStart={showingFrom}
                dashboardReturn={dashboardReturn}
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
            {listTruncated && " · refine search or filter to narrow results"}
          </p>
          {pageCount > 1 && (
            <div className="pagination">
              <button
                type="button"
                className="control control-btn"
                disabled={page <= 1 || tableLoading}
                onClick={() =>
                  setSearchParams(
                    (prev) => patchDashboardParams(prev, { page: page - 1 }),
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
                    (prev) => patchDashboardParams(prev, { page: page + 1 }),
                    { replace: true },
                  )
                }
              >
                Next
              </button>
            </div>
          )}
        </div>
      </section>
    </>
  );
}
