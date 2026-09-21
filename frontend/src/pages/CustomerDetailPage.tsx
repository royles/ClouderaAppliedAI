import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { CUSTOMER_BASE } from "../appRoutes";
import Breadcrumbs from "../components/Breadcrumbs";
import { rememberRecentCustomer } from "../recentCustomers";
import {
  CustomerDetail,
  fetchCustomer,
  fetchCustomerValueHistory,
  ValueHistoryPoint,
} from "../api";
import CustomerInsightsPanel from "../components/CustomerInsightsPanel";
import CustomerSummaryCard from "../components/CustomerSummaryCard";
import CustomerValueChart from "../components/CustomerValueChart";
import {
  formatCity,
  formatLastLogin,
  maskDate,
  displayCustomerName,
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

function interactionIcon(type: string) {
  if (type === "REVIEW") return "★";
  if (type === "AGENT_QUESTION") return "?";
  if (type === "WEB_SEARCH") return "⌕";
  return "•";
}

export default function CustomerDetailPage() {
  const { customerId } = useParams();
  const location = useLocation();
  const id = Number(customerId);
  const listBack =
    typeof location.state?.businessReturn === "string"
      ? location.state.businessReturn
      : CUSTOMER_BASE;
  const backFromCustomerList = listBack.startsWith(CUSTOMER_BASE);
  const hubBackLabel = backFromCustomerList ? "The customer" : "The business";
  const hubBackLinkText = backFromCustomerList
    ? "← Back to customers"
    : "← Back to the business";
  const secondaryHubLinkText = backFromCustomerList
    ? "Back to customer list"
    : "Portfolio in the business";
  const [detail, setDetail] = useState<CustomerDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("policies");
  const [activePolicy, setActivePolicy] = useState<number | null>(null);
  const [valueHistory, setValueHistory] = useState<ValueHistoryPoint[]>([]);
  const [valueHistoryLoading, setValueHistoryLoading] = useState(true);

  useEffect(() => {
    if (!Number.isFinite(id)) {
      setError("Invalid customer ID");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchCustomer(id);
        if (!cancelled) {
          setDetail(data);
          rememberRecentCustomer(id);
          setError(null);
        }
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

  useEffect(() => {
    if (!Number.isFinite(id)) return;
    let cancelled = false;
    (async () => {
      setValueHistoryLoading(true);
      try {
        const data = await fetchCustomerValueHistory(id);
        if (!cancelled) setValueHistory(data.points ?? []);
      } catch {
        if (!cancelled) setValueHistory([]);
      } finally {
        if (!cancelled) setValueHistoryLoading(false);
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

  const customerCard = useMemo(() => {
    if (!detail) return null;
    const { profile, policies, investments, churn } = detail;
    const investmentCount = new Set(
      investments.map((inv) => `${inv.policy_num}-${inv.fund_id ?? ""}`),
    ).size;
    const customerValue =
      valueHistory.length > 0
        ? valueHistory[valueHistory.length - 1].total_value
        : 0;
    return {
      customer_id: profile.customer_id,
      customer_name: profile.customer_name,
      city_name: profile.city_name,
      email: profile.email,
      mobile_no: profile.mobile_no,
      last_login: profile.last_login,
      policy_count: policies.length,
      investment_count: investmentCount,
      customer_value: customerValue,
      churn_probability: churn?.churn_probability,
      churn_risk_tier: churn?.churn_risk_tier,
    };
  }, [detail, valueHistory]);

  if (error) {
    return (
      <section className="panel">
        <p className="error">{error}</p>
        <Link to={listBack}>{hubBackLinkText}</Link>
      </section>
    );
  }
  if (!detail) {
    return (
      <>
        <Breadcrumbs
          items={[
            { label: hubBackLabel, to: listBack },
            { label: "Loading…" },
          ]}
        />
        <section className="panel">
          <div className="skeleton skeleton-title" />
          <div className="kpi-strip">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="skeleton skeleton-kpi" />
            ))}
          </div>
        </section>
      </>
    );
  }

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
      <Breadcrumbs
        items={[
          { label: hubBackLabel, to: listBack },
          { label: displayCustomerName(profile.customer_name) },
        ]}
      />
      <p className="muted small customer-area-links">
        <Link to={listBack}>{secondaryHubLinkText}</Link>
        {!backFromCustomerList && (
          <>
            {" · "}
            <Link to={CUSTOMER_BASE}>Customer home</Link>
          </>
        )}
      </p>
      <section className="panel customer-detail-hero">
        <div className="customer-detail-hero-grid">
          {customerCard && (
            <CustomerSummaryCard variant="static" customer={customerCard} />
          )}
          <CustomerValueChart
            className="customer-detail-value-chart"
            fillContainer
            title="Customer value"
            subtitle="Solid lines are warehouse snapshots. Dashed projection: HIGH risk lapses to ₪0 within 3 months; MEDIUM extends recent history; LOW extends full history."
            points={valueHistory}
            loading={valueHistoryLoading}
            churn={
              detail.churn?.churn_risk_tier || detail.churn?.churn_probability != null
                ? {
                    probability: detail.churn?.churn_probability ?? 0,
                    tier: detail.churn?.churn_risk_tier,
                  }
                : null
            }
          />
        </div>
        {detail.churn?.scored_at && (
          <p className="muted small customer-detail-churn-meta">
            Churn scored {formatLastLogin(detail.churn.scored_at)}
            {detail.churn.model_version ? ` · ${detail.churn.model_version}` : ""}
          </p>
        )}
        <p className="muted small customer-detail-privacy">
          City and last login are shown in full; other sensitive fields remain masked.
        </p>
        <div className="detail-grid customer-detail-profile-grid">
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
            <span className="label">Last interaction</span>
            <div>
              {interaction_summary?.last_event_ts
                ? formatLastLogin(interaction_summary.last_event_ts)
                : "—"}
            </div>
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
            <ol className="interaction-timeline">
              {interactions.map((ev) => {
                const signal =
                  ev.event_type === "REVIEW" && ev.rating != null
                    ? `${ev.rating}/5 stars`
                    : ev.event_type === "AGENT_QUESTION"
                      ? ev.resolved
                        ? "Resolved"
                        : "Open"
                      : ev.topic === "help_center"
                        ? "Help search"
                        : "Product search";
                return (
                  <li
                    key={ev.event_id}
                    className={`timeline-item timeline-${ev.event_type.toLowerCase()}${
                      ev.event_type === "AGENT_QUESTION" && !ev.resolved
                        ? " timeline-open"
                        : ""
                    }`}
                  >
                    <div className="timeline-icon" aria-hidden>
                      {interactionIcon(ev.event_type)}
                    </div>
                    <div className="timeline-body">
                      <div className="timeline-head">
                        <strong>{formatEventType(ev.event_type)}</strong>
                        <span className="muted small">{maskDate(ev.event_ts)}</span>
                      </div>
                      <p className="timeline-title">{ev.query_or_title ?? "—"}</p>
                      <p className="muted small timeline-meta">
                        {[ev.channel, signal].filter(Boolean).join(" · ")}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
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
