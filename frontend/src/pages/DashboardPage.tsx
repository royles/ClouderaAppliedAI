import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
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
import ChurnBadge from "../ChurnBadge";
import CustomerValueChart from "../components/CustomerValueChart";
import {
  formatCity,
  formatLastLogin,
  displayCustomerId,
  maskEmail,
  displayCustomerName,
  maskPhone,
} from "../pii";

export default function DashboardPage() {
  const location = useLocation();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [segment, setSegment] = useState<CustomerSegment>("customers_all");
  const [sortBy, setSortBy] = useState<CustomerSortBy>("churn_risk");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [error, setError] = useState<string | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);
  const [valueHistory, setValueHistory] = useState<ValueHistoryPoint[]>([]);
  const [valueHistoryLoading, setValueHistoryLoading] = useState(true);
  const customersRequestRef = useRef(0);
  const valueHistoryRequestRef = useRef(0);
  const valueHistorySegmentRef = useRef<CustomerSegment | null>(null);

  const activeDomain = useMemo((): DomainCount | null => {
    if (segment === "customers_all" || !overview?.domains) return null;
    const match = overview.domains.find((d) => d.filter_key === segment);
    return match ?? null;
  }, [segment, overview]);

  useEffect(() => {
    const handle = window.setTimeout(() => setDebouncedSearch(search), 300);
    return () => window.clearTimeout(handle);
  }, [search]);

  // Refetch overview when the user lands on the dashboard route.
  useEffect(() => {
    if (location.pathname !== "/") return;

    let cancelled = false;
    (async () => {
      setOverviewLoading(true);
      try {
        const ov = await fetchOverview();
        if (!cancelled) {
          setOverview(ov);
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

    (async () => {
      setTableLoading(true);
      try {
        const rows = await fetchCustomers({
          q: debouncedSearch,
          segment,
          sortBy,
          sortOrder,
          limit: 200,
        });
        if (cancelled || requestId !== customersRequestRef.current) return;
        setCustomers(rows);
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

  const onCardClick = (domain: DomainCount) => {
    const key = domain.filter_key as CustomerSegment;
    setSegment((prev) => (prev === key ? "customers_all" : key));
  };

  const clearFilter = () => {
    setSegment("customers_all");
  };

  const setRankBy = (by: CustomerSortBy) => {
    setSortBy(by);
    if (by === "churn_risk" || by === "policy_count" || by === "investment_count") {
      setSortOrder("desc");
    } else {
      setSortOrder("asc");
    }
  };

  const toggleSortOrder = () => {
    setSortOrder((o) => (o === "asc" ? "desc" : "asc"));
  };

  const showRank =
    sortBy === "churn_risk" ||
    sortBy === "policy_count" ||
    sortBy === "investment_count";

  if (overviewLoading && !overview) {
    return <p className="muted">Loading warehouse…</p>;
  }
  if (error && !overview) return <p className="error">{error}</p>;

  return (
    <>
      <section className="panel">
        <h1>Warehouse overview</h1>
        <p className="muted small">
          Click a card to filter the customer table and value chart. Click again to clear.
        </p>
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
                <option value="churn_risk">Churn risk</option>
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
              {sortBy === "churn_risk"
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
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        <div className={`table-wrap${tableLoading ? " table-loading" : ""}`}>
          {tableLoading && (
            <p className="table-loading-label muted">Updating table…</p>
          )}
          <table className="table table-interactive">
            <thead>
              <tr>
                {showRank && <th>#</th>}
                <th>Name</th>
                <th>ID</th>
                <th>City</th>
                <th>Email</th>
                <th>Mobile</th>
                <th
                  className={sortBy === "policy_count" ? "th-sorted" : undefined}
                >
                  Policies
                </th>
                <th
                  className={
                    sortBy === "investment_count" ? "th-sorted" : undefined
                  }
                >
                  Investments
                </th>
                <th>Last login</th>
                <th className={sortBy === "churn_risk" ? "th-sorted" : undefined}>
                  Churn risk
                </th>
              </tr>
            </thead>
            <tbody>
              {customers.length === 0 ? (
                <tr>
                  <td colSpan={showRank ? 10 : 9} className="muted">
                    No customers match this filter.
                  </td>
                </tr>
              ) : (
                customers.map((c, index) => (
                  <tr key={c.customer_id} className="table-row-click">
                    {showRank && <td className="rank-cell">{index + 1}</td>}
                    <td>
                      <Link to={`/customers/${c.customer_id}`}>
                        {displayCustomerName(c.customer_name)}
                      </Link>
                    </td>
                    <td>
                      <Link to={`/customers/${c.customer_id}`}>
                        {displayCustomerId(c.customer_id)}
                      </Link>
                    </td>
                    <td>{formatCity(c.city_name)}</td>
                    <td>{maskEmail(c.email)}</td>
                    <td>{maskPhone(c.mobile_no)}</td>
                    <td>{c.policy_count ?? 0}</td>
                    <td>{c.investment_count ?? 0}</td>
                    <td>{formatLastLogin(c.last_login)}</td>
                    <td>
                      <ChurnBadge
                        probability={c.churn_probability}
                        tier={c.churn_risk_tier}
                      />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
