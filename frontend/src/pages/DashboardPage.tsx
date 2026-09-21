import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  CustomerSummary,
  fetchCustomers,
  fetchOverview,
  Overview,
} from "../api";

export default function DashboardPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const [ov, list] = await Promise.all([
          fetchOverview(),
          fetchCustomers(),
        ]);
        if (!cancelled) {
          setOverview(ov);
          setCustomers(list);
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
    const handle = window.setTimeout(async () => {
      try {
        setCustomers(await fetchCustomers(search));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Search failed");
      }
    }, 300);
    return () => window.clearTimeout(handle);
  }, [search]);

  if (loading) return <p className="muted">Loading warehouse…</p>;
  if (error) return <p className="error">{error}</p>;

  return (
    <>
      <section className="panel">
        <h1>Warehouse overview</h1>
        {overview && (
          <>
            <p className="muted small">Database: {overview.database_path}</p>
            <div className="stat-grid">
              {overview.domains.map((d) => (
                <div key={d.domain} className="stat-card">
                  <div className="stat-value">{d.row_count.toLocaleString()}</div>
                  <div className="stat-label">{d.domain}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Customers</h2>
          <input
            className="search"
            placeholder="Search by name or ID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>ID</th>
              <th>City</th>
              <th>Policies</th>
              <th>Last login</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.customer_key}>
                <td>
                  <Link to={`/customers/${c.customer_id}`}>{c.customer_name}</Link>
                </td>
                <td>{c.customer_id}</td>
                <td>{c.city_name ?? "—"}</td>
                <td>{c.policy_count}</td>
                <td>{c.last_login ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
