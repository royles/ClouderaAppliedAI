import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CustomerDetail, fetchCustomer } from "../api";
import ChurnBadge from "../ChurnBadge";
import CustomerInsightsPanel from "../components/CustomerInsightsPanel";
import {
  formatCity,
  formatLastLogin,
  displayCustomerId,
  maskDate,
  maskEmail,
  displayCustomerName,
  maskPhone,
  maskStreet,
} from "../pii";

function formatMoney(n?: number | null) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-IL", {
    style: "currency",
    currency: "ILS",
    maximumFractionDigits: 0,
  }).format(n);
}

type Tab = "policies" | "foreclosures" | "investments" | "interactions";

function formatEventType(t: string) {
  if (t === "REVIEW") return "Review";
  if (t === "AGENT_QUESTION") return "Agent question";
  if (t === "WEB_SEARCH") return "Web search";
  return t;
}

export default function CustomerDetailPage() {
  const { customerId } = useParams();
  const id = Number(customerId);
  const [detail, setDetail] = useState<CustomerDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("policies");
  const [activePolicy, setActivePolicy] = useState<number | null>(null);

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

  const filteredInvestments = useMemo(() => {
    if (!detail) return [];
    if (activePolicy == null) return detail.investments;
    return detail.investments.filter((i) => i.policy_num === activePolicy);
  }, [detail, activePolicy]);

  if (error) {
    return (
      <section className="panel">
        <p className="error">{error}</p>
        <Link to="/">← Back to dashboard</Link>
      </section>
    );
  }
  if (!detail) return <p className="muted">Loading customer…</p>;

  const {
    profile,
    policies,
    foreclosures,
    investments,
    interactions = [],
    interaction_summary,
  } = detail;

  return (
    <>
      <p>
        <Link to="/">← Back to dashboard</Link>
      </p>
      <section className="panel">
        <h1>{displayCustomerName(profile.customer_name)}</h1>
        <div className="churn-detail-row">
          <span className="label">Churn likelihood</span>
          <ChurnBadge
            probability={detail.churn?.churn_probability}
            tier={detail.churn?.churn_risk_tier}
          />
        </div>
        <p className="muted small">
          City and last login are shown in full; other sensitive fields remain masked.
        </p>
        <div className="detail-grid">
          <div>
            <span className="label">Customer ID</span>
            <div>{displayCustomerId(profile.customer_id)}</div>
          </div>
          <div>
            <span className="label">Type</span>
            <div>{profile.customer_type_dsc ?? "—"}</div>
          </div>
          <div>
            <span className="label">Birth date</span>
            <div>{maskDate(profile.birth_date)}</div>
          </div>
          <div>
            <span className="label">Marital status</span>
            <div>{profile.marital_status_dsc ?? "—"}</div>
          </div>
          <div>
            <span className="label">Email</span>
            <div>{maskEmail(profile.email)}</div>
          </div>
          <div>
            <span className="label">Mobile</span>
            <div>{maskPhone(profile.mobile_no)}</div>
          </div>
          <div>
            <span className="label">Address</span>
            <div>
              {[maskStreet(profile.street_name), formatCity(profile.city_name)]
                .filter((x) => x !== "—")
                .join(", ") || "—"}
            </div>
          </div>
          <div>
            <span className="label">Communication</span>
            <div>{profile.communication_dsc ?? "—"}</div>
          </div>
          <div>
            <span className="label">Last login</span>
            <div>{formatLastLogin(profile.last_login)}</div>
          </div>
        </div>
      </section>

      <CustomerInsightsPanel
        customerId={profile.customer_id}
        churnTier={detail.churn?.churn_risk_tier}
      />

      <div className="tab-bar">
        <button
          type="button"
          className={tab === "policies" ? "tab active" : "tab"}
          onClick={() => setTab("policies")}
        >
          Policies ({policies.length})
        </button>
        <button
          type="button"
          className={tab === "foreclosures" ? "tab active" : "tab"}
          onClick={() => setTab("foreclosures")}
        >
          Foreclosures ({foreclosures.length})
        </button>
        <button
          type="button"
          className={tab === "investments" ? "tab active" : "tab"}
          onClick={() => setTab("investments")}
        >
          Investments ({investments.length})
        </button>
        <button
          type="button"
          className={tab === "interactions" ? "tab active" : "tab"}
          onClick={() => setTab("interactions")}
        >
          Interactions ({interaction_summary?.total_events ?? interactions.length})
        </button>
      </div>

      {tab === "policies" && (
        <section className="panel">
          <h2>Policies</h2>
          <p className="muted small">Click a policy to filter investment snapshots.</p>
          <div className="table-wrap">
            <table className="table table-interactive">
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
                  <tr
                    key={p.policy_num}
                    className={
                      activePolicy === p.policy_num
                        ? "table-row-selected"
                        : "table-row-click"
                    }
                    onClick={() =>
                      setActivePolicy((prev) =>
                        prev === p.policy_num ? null : p.policy_num,
                      )
                    }
                  >
                    <td>{p.policy_num}</td>
                    <td>{p.policy_type_desc ?? "—"}</td>
                    <td>{p.policy_status_desc ?? "—"}</td>
                    <td>{p.is_active ? "Yes" : "No"}</td>
                    <td>{formatMoney(p.bruto_monthly_premium)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {tab === "foreclosures" && (
        <section className="panel">
          <h2>Foreclosures & encumbrances</h2>
          {foreclosures.length === 0 ? (
            <p className="muted">No foreclosure records.</p>
          ) : (
            <div className="table-wrap">
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
                      <td>{maskDate(f.foreclosures_date)}</td>
                      <td>{f.portfolio_number ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {tab === "interactions" && (
        <section className="panel">
          <h2>Interaction timeline</h2>
          <p className="muted small">
            Synthetic omnichannel events — reviews, agent questions, and product or help
            searches — used by churn scoring and AI recommendations.
          </p>
          {interaction_summary && (
            <div className="interaction-stats">
              <span>
                Last 90 days: <strong>{interaction_summary.events_last_90d}</strong> events
              </span>
              {interaction_summary.avg_review_rating != null && (
                <span>
                  Avg review: <strong>{interaction_summary.avg_review_rating}/5</strong>
                </span>
              )}
              {interaction_summary.unresolved_agent_questions > 0 && (
                <span className="warn-stat">
                  Open agent items:{" "}
                  <strong>{interaction_summary.unresolved_agent_questions}</strong>
                </span>
              )}
            </div>
          )}
          {interactions.length === 0 ? (
            <p className="muted">No interaction events recorded.</p>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>When</th>
                    <th>Type</th>
                    <th>Channel</th>
                    <th>Title / query</th>
                    <th>Signal</th>
                  </tr>
                </thead>
                <tbody>
                  {interactions.map((ev) => (
                    <tr key={ev.event_id}>
                      <td>{maskDate(ev.event_ts)}</td>
                      <td>{formatEventType(ev.event_type)}</td>
                      <td>{ev.channel ?? "—"}</td>
                      <td>{ev.query_or_title ?? "—"}</td>
                      <td>
                        {ev.event_type === "REVIEW" && ev.rating != null
                          ? `${ev.rating}/5`
                          : ev.event_type === "AGENT_QUESTION"
                            ? ev.resolved
                              ? "Resolved"
                              : "Open"
                            : ev.topic === "help_center"
                              ? "Help"
                              : "Product"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {tab === "investments" && (
        <section className="panel">
          <h2>Latest investment snapshots</h2>
          {activePolicy != null && (
            <p className="filter-banner">
              Policy filter: <strong>{activePolicy}</strong>
              <button
                type="button"
                className="link-btn"
                onClick={() => setActivePolicy(null)}
              >
                Show all
              </button>
            </p>
          )}
          {filteredInvestments.length === 0 ? (
            <p className="muted">No investment snapshots for this selection.</p>
          ) : (
            <div className="table-wrap">
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
                  {filteredInvestments.map((inv, idx) => (
                    <tr key={`${inv.policy_num}-${inv.fund_id}-${idx}`}>
                      <td>{inv.policy_num}</td>
                      <td>{inv.fund_id ?? "—"}</td>
                      <td>{maskDate(inv.snapshot_date)}</td>
                      <td>{formatMoney(inv.accumulation_total)}</td>
                      <td>{formatMoney(inv.yearly_profit_loss_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </>
  );
}
