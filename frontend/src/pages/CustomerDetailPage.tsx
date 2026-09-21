import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CustomerDetail, fetchCustomer } from "../api";

function formatMoney(n?: number | null) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-IL", {
    style: "currency",
    currency: "ILS",
    maximumFractionDigits: 0,
  }).format(n);
}

export default function CustomerDetailPage() {
  const { customerId } = useParams();
  const id = Number(customerId);
  const [detail, setDetail] = useState<CustomerDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(id)) {
      setError("Invalid customer ID");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        setDetail(await fetchCustomer(id));
        setError(null);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Customer not found");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return (
      <section className="panel">
        <p className="error">{error}</p>
        <Link to="/">← Back to dashboard</Link>
      </section>
    );
  }
  if (!detail) return <p className="muted">Loading customer…</p>;

  const { profile, policies, foreclosures, investments } = detail;

  return (
    <>
      <p>
        <Link to="/">← Back to dashboard</Link>
      </p>
      <section className="panel">
        <h1>{profile.customer_name}</h1>
        <div className="detail-grid">
          <div>
            <span className="label">Customer ID</span>
            <div>{profile.customer_id}</div>
          </div>
          <div>
            <span className="label">Type</span>
            <div>{profile.customer_type_dsc ?? "—"}</div>
          </div>
          <div>
            <span className="label">Birth date</span>
            <div>{profile.birth_date ?? "—"}</div>
          </div>
          <div>
            <span className="label">Marital status</span>
            <div>{profile.marital_status_dsc ?? "—"}</div>
          </div>
          <div>
            <span className="label">Email</span>
            <div>{profile.email ?? "—"}</div>
          </div>
          <div>
            <span className="label">Mobile</span>
            <div>{profile.mobile_no ?? "—"}</div>
          </div>
          <div>
            <span className="label">Address</span>
            <div>
              {[profile.street_name, profile.city_name].filter(Boolean).join(", ") ||
                "—"}
            </div>
          </div>
          <div>
            <span className="label">Communication</span>
            <div>{profile.communication_dsc ?? "—"}</div>
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>Policies</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Number</th>
              <th>Type</th>
              <th>Status</th>
              <th>Active</th>
              <th>Monthly premium</th>
            </tr>
          </thead>
          <tbody>
            {policies.map((p) => (
              <tr key={p.policy_num}>
                <td>{p.policy_num}</td>
                <td>{p.policy_type_desc ?? "—"}</td>
                <td>{p.policy_status_desc ?? "—"}</td>
                <td>{p.is_active ? "Yes" : "No"}</td>
                <td>{formatMoney(p.bruto_monthly_premium)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {foreclosures.length > 0 && (
        <section className="panel">
          <h2>Foreclosures & encumbrances</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Proceeding #</th>
                <th>Amount</th>
                <th>Date</th>
                <th>Portfolio</th>
              </tr>
            </thead>
            <tbody>
              {foreclosures.map((f) => (
                <tr key={f.foreclosures_number}>
                  <td>{f.foreclosures_number}</td>
                  <td>{formatMoney(f.foreclosures_amount)}</td>
                  <td>{f.foreclosures_date ?? "—"}</td>
                  <td>{f.portfolio_number ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {investments.length > 0 && (
        <section className="panel">
          <h2>Latest investment snapshots</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Policy</th>
                <th>Fund</th>
                <th>Snapshot</th>
                <th>Accumulation</th>
                <th>YTD P/L</th>
              </tr>
            </thead>
            <tbody>
              {investments.map((inv, idx) => (
                <tr key={`${inv.policy_num}-${inv.fund_id}-${idx}`}>
                  <td>{inv.policy_num}</td>
                  <td>{inv.fund_id ?? "—"}</td>
                  <td>{inv.snapshot_date}</td>
                  <td>{formatMoney(inv.accumulation_total)}</td>
                  <td>{formatMoney(inv.yearly_profit_loss_total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </>
  );
}
