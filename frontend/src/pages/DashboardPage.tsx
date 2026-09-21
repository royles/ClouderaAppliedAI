import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  CustomerSegment,
  CustomerSortBy,
  CustomerSummary,
  DomainCount,
  fetchCustomers,
  fetchOverview,
  Overview,
  SortOrder,
} from "../api";
import {
  maskCity,
  maskCustomerId,
  maskDate,
  maskEmail,
  maskName,
  maskPhone,
} from "../pii";

export default function DashboardPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [search, setSearch] = useState("");
  const [segment, setSegment] = useState<CustomerSegment>("customers_all");
  const [sortBy, setSortBy] = useState<CustomerSortBy>("name");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const [activeDomain, setActiveDomain] = useState<DomainCount | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);

  const loadCustomers = useCallback(
    async (
      q: string,
      seg: CustomerSegment,
      by: CustomerSortBy,
      order: SortOrder,
    ) => {
      setTableLoading(true);
      try {
        setCustomers(
          await fetchCustomers({
            q,
            segment: seg,
            sortBy: by,
            sortOrder: order,
            limit: 200,
          }),
        );
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load customers");
      } finally {
        setTableLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const ov = await fetchOverview();
        if (!cancelled) {
          setOverview(ov);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load data");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      void loadCustomers(search, segment, sortBy, sortOrder);
    }, 300);
    return () => window.clearTimeout(handle);
  }, [search, segment, sortBy, sortOrder, loadCustomers]);

  const onCardClick = (domain: DomainCount) => {
    const key = domain.filter_key as CustomerSegment;
    if (segment === key) {
      setSegment("customers_all");
      setActiveDomain(null);
    } else {
      setSegment(key);
      setActiveDomain(domain);
    }
  };

  const clearFilter = () => {
    setSegment("customers_all");
    setActiveDomain(null);
  };

  const setRankBy = (by: CustomerSortBy) => {
    setSortBy(by);
    if (by === "policy_count" || by === "investment_count") {
      setSortOrder("desc");
    } else {
      setSortOrder("asc");
    }
  };

  const toggleSortOrder = () => {
    setSortOrder((o) => (o === "asc" ? "desc" : "asc"));
  };

  const showRank = sortBy === "policy_count" || sortBy === "investment_count";

  if (loading) return <p className="muted">Loading warehouse…</p>;
  if (error && !overview) return <p className="error">{error}</p>;

  return (
    <>
      <section className="panel">
        <h1>Warehouse overview</h1>
        <p className="muted small">
          Click a card to filter the customer table. Click again to clear. PII is masked in
          the UI.
        </p>
        {overview && (
          <div className="stat-grid">
            {overview.domains.map((d) => {
              const selected = segment === d.filter_key;
              return (
                <button
                  key={d.filter_key}
                  type="button"
                  className={`stat-card stat-card-btn${selected ? " stat-card-selected" : ""}`}
                  onClick={() => onCardClick(d)}
                  title={d.description || d.domain}
                >
                  <div className="stat-value">{d.row_count.toLocaleString()}</div>
                  <div className="stat-label">{d.domain}</div>
                </button>
              );
            })}
          </div>
        )}
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
              {sortOrder === "desc" ? "Highest first ↓" : "Lowest first ↑"}
            </button>
            <div className="toolbar-item toolbar-item-grow">
              <label htmlFor="customer-search">Search</label>
              <input
                id="customer-search"
                className="control control-search"
                placeholder="Name or ID"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        {tableLoading ? (
          <p className="muted">Updating table…</p>
        ) : (
          <div className="table-wrap">
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
                </tr>
              </thead>
              <tbody>
                {customers.length === 0 ? (
                  <tr>
                    <td colSpan={showRank ? 9 : 8} className="muted">
                      No customers match this filter.
                    </td>
                  </tr>
                ) : (
                  customers.map((c, index) => (
                    <tr key={c.customer_key} className="table-row-click">
                      {showRank && <td className="rank-cell">{index + 1}</td>}
                      <td>
                        <Link to={`/customers/${c.customer_id}`}>
                          {maskName(c.customer_name)}
                        </Link>
                      </td>
                      <td>{maskCustomerId(c.customer_id)}</td>
                      <td>{maskCity(c.city_name)}</td>
                      <td>{maskEmail(c.email)}</td>
                      <td>{maskPhone(c.mobile_no)}</td>
                      <td>{c.policy_count}</td>
                      <td>{c.investment_count}</td>
                      <td>{maskDate(c.last_login?.slice(0, 10))}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
