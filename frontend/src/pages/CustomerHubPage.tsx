import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCustomers, CustomerSummary } from "../api";
import { customerPath } from "../appRoutes";
import Breadcrumbs from "../components/Breadcrumbs";
import ChurnBadge from "../ChurnBadge";
import { displayCustomerId, displayCustomerName, formatCity } from "../pii";

const RECENT_KEY = "customer360.recentCustomers";

function loadRecent(): number[] {
  try {
    const raw = sessionStorage.getItem(RECENT_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((id) => typeof id === "number").slice(0, 8);
  } catch {
    return [];
  }
}

export function rememberRecentCustomer(customerId: number) {
  const ids = loadRecent().filter((id) => id !== customerId);
  ids.unshift(customerId);
  sessionStorage.setItem(RECENT_KEY, JSON.stringify(ids.slice(0, 8)));
}

export default function CustomerHubPage() {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<CustomerSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [recentDetails, setRecentDetails] = useState<CustomerSummary[]>([]);

  useEffect(() => {
    const recentIds = loadRecent();
    if (recentIds.length === 0) {
      setRecentDetails([]);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const lists = await Promise.all(
          recentIds.map((id) =>
            fetchCustomers({ q: String(id), limit: 1 }).then((r) => r.customers[0]),
          ),
        );
        if (!cancelled) {
          setRecentDetails(lists.filter(Boolean) as CustomerSummary[]);
        }
      } catch {
        if (!cancelled) setRecentDetails([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const trimmed = search.trim();
    if (trimmed.length < 2) {
      setResults([]);
      return;
    }
    let cancelled = false;
    const handle = window.setTimeout(async () => {
      setLoading(true);
      try {
        const data = await fetchCustomers({
          q: trimmed,
          sortBy: "churn_risk",
          sortOrder: "desc",
          limit: 12,
        });
        if (!cancelled) setResults(data.customers);
      } catch {
        if (!cancelled) setResults([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 300);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [search]);

  return (
    <>
      <Breadcrumbs items={[{ label: "The customer" }]} />
      <section className="panel">
        <h1>Customer 360</h1>
        <p className="muted small">
          Search by name or ID, pick a recent profile, or open a customer from{" "}
          <Link to="/business">the business</Link> portfolio.
        </p>
        <div className="toolbar customer-hub-search">
          <div className="toolbar-item toolbar-item-grow">
            <label htmlFor="customer-hub-search">Find customer</label>
            <input
              id="customer-hub-search"
              className="control control-search"
              placeholder="Name or customer ID"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
        {loading && <p className="muted small">Searching…</p>}
        {search.trim().length >= 2 && !loading && results.length === 0 && (
          <p className="muted">No customers match.</p>
        )}
        {results.length > 0 && (
          <ul className="customer-hub-list">
            {results.map((c) => (
              <li key={c.customer_id}>
                <Link to={customerPath(c.customer_id)} className="customer-hub-row">
                  <span className="customer-hub-name">
                    {displayCustomerName(c.customer_name)}
                  </span>
                  <span className="muted small">
                    {displayCustomerId(c.customer_id)} · {formatCity(c.city_name)}
                  </span>
                  <ChurnBadge
                    probability={c.churn_probability}
                    tier={c.churn_risk_tier}
                  />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      {recentDetails.length > 0 && (
        <section className="panel">
          <h2>Recently viewed</h2>
          <ul className="customer-hub-list">
            {recentDetails.map((c) => (
              <li key={c.customer_id}>
                <Link to={customerPath(c.customer_id)} className="customer-hub-row">
                  <span className="customer-hub-name">
                    {displayCustomerName(c.customer_name)}
                  </span>
                  <span className="muted small">{displayCustomerId(c.customer_id)}</span>
                  <ChurnBadge
                    probability={c.churn_probability}
                    tier={c.churn_risk_tier}
                  />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
