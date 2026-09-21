import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  CustomerSegment,
  EngagementHub,
  fetchEngagementHub,
  fetchOverview,
  Overview,
} from "../api";
import { customerPath, ENGAGEMENT_BASE } from "../appRoutes";
import Breadcrumbs from "../components/Breadcrumbs";
import ChurnBadge from "../ChurnBadge";
import DomainFilterGrid from "../components/DomainFilterGrid";
import { parseBusinessSegment, patchBusinessSegment } from "../dashboardUrl";
import { displayCustomerName, formatCity } from "../pii";
import { formatMoneyIls } from "../formatMoney";

function channelLabel(hint: string) {
  if (hint === "email") return "Email";
  if (hint === "phone") return "Phone";
  if (hint === "sms") return "SMS";
  return hint;
}

export default function EngagementHubPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const segment = useMemo(() => parseBusinessSegment(searchParams), [searchParams]);

  const [overview, setOverview] = useState<Overview | null>(null);
  const [hub, setHub] = useState<EngagementHub | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const ov = await fetchOverview();
        if (!cancelled) setOverview(ov);
      } catch {
        /* optional */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    void (async () => {
      try {
        const data = await fetchEngagementHub({ segment, limit: 50 });
        if (!cancelled) {
          setHub(data);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load engagement hub");
          setHub(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [segment]);

  const setSegment = (next: CustomerSegment) => {
    setSearchParams((prev) => patchBusinessSegment(prev, next), { replace: true });
  };

  const summary = hub?.book_summary;

  return (
    <>
      <Breadcrumbs items={[{ label: "Engagement & touchpoints" }]} />
      <section className="panel engagement-hub-intro">
        <h1 className="page-title">Engagement & touchpoints</h1>
        <p className="muted engagement-hub-lede">
          Prioritize customers with the highest propensity to influence — recent digital
          signals, open questions, and relationship value — then act with a clear next step.
        </p>
      </section>

      {overview && (
        <section className="panel">
          <DomainFilterGrid
            overview={overview}
            segment={segment}
            onSelect={setSegment}
            helperText="Optional cohort filter (same cards as The business)."
          />
        </section>
      )}

      <section className="panel">
        <div className="engagement-summary-grid">
          <div className="engagement-summary-card">
            <span className="label">Touchpoints (90d)</span>
            <strong>{loading ? "…" : (summary?.total_touchpoints_90d ?? 0).toLocaleString()}</strong>
            <span className="muted small">
              {summary?.customers_with_touchpoints_90d ?? 0} customers active
            </span>
          </div>
          <div className="engagement-summary-card">
            <span className="label">Digital & agent</span>
            <strong>{loading ? "…" : (summary?.digital_touchpoints_90d ?? 0).toLocaleString()}</strong>
            <span className="muted small">Web searches & agent questions</span>
          </div>
          <div className="engagement-summary-card">
            <span className="label">Reviews (90d)</span>
            <strong>{loading ? "…" : (summary?.review_events_90d ?? 0).toLocaleString()}</strong>
            <span className="muted small">Voice-of-customer events</span>
          </div>
          <div className="engagement-summary-card engagement-summary-card-warn">
            <span className="label">Open agent questions</span>
            <strong>{loading ? "…" : (summary?.unresolved_agent_questions ?? 0).toLocaleString()}</strong>
            <span className="muted small">Needs resolution in 90d window</span>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2 className="subsection-title">Influence priority list</h2>
            <p className="muted small">
              Ranked by influence score (value, recency, open items, and churn context).
              {hub != null && !loading ? ` Showing ${hub.opportunities.length} of ${hub.total}.` : ""}
            </p>
          </div>
        </div>

        {error && <p className="error">{error}</p>}

        {loading && !hub && (
          <p className="muted small">Loading engagement opportunities…</p>
        )}

        {!loading && hub && hub.opportunities.length === 0 && (
          <p className="muted small">No engagement opportunities match this filter.</p>
        )}

        <ul className="engagement-opportunity-list">
          {hub?.opportunities.map((row) => (
            <li key={row.customer_id} className="engagement-opportunity-card">
              <div className="engagement-opportunity-head">
                <div>
                  <Link
                    to={customerPath(row.customer_id)}
                    state={{
                      businessReturn: `${ENGAGEMENT_BASE}${searchParams.toString() ? `?${searchParams}` : ""}`,
                      initialTab: "interactions" as const,
                      scrollToInsights: true,
                      engagementAction: row.recommended_action.title,
                    }}
                    className="engagement-opportunity-name"
                  >
                    {displayCustomerName(row.customer_name)}
                  </Link>
                  <p className="muted small">
                    {formatCity(row.city_name)} · {formatMoneyIls(row.customer_value)} book
                    {row.churn_risk_tier && (
                      <>
                        {" · "}
                        <ChurnBadge
                          tier={row.churn_risk_tier}
                          probability={row.churn_probability}
                        />
                      </>
                    )}
                  </p>
                </div>
                <div className="engagement-influence-score" title="Propensity to influence">
                  <span className="label">Influence</span>
                  <strong>{row.influence_score.toFixed(0)}</strong>
                </div>
              </div>

              <div className="engagement-touchpoint-strip">
                <span className="touchpoint-chip">
                  {row.touchpoints.events_last_90d} touchpoints (90d)
                </span>
                <span className="touchpoint-chip">
                  {row.touchpoints.web_searches_90d} web searches
                </span>
                <span className="touchpoint-chip">
                  {row.touchpoints.reviews_90d} reviews
                </span>
                {row.touchpoints.unresolved_agent_questions > 0 && (
                  <span className="touchpoint-chip touchpoint-chip-warn">
                    {row.touchpoints.unresolved_agent_questions} open questions
                  </span>
                )}
                <span className="touchpoint-chip">
                  {Math.round(row.touchpoints.days_since_last_touch)}d since last touch
                </span>
              </div>

              <div className="engagement-action-block">
                <div>
                  <span className="label">Recommended next step</span>
                  <strong>{row.recommended_action.title}</strong>
                  <p className="muted small">{row.recommended_action.detail}</p>
                </div>
                <div className="engagement-action-buttons">
                  <Link
                    to={customerPath(row.customer_id)}
                    state={{
                      businessReturn: `${ENGAGEMENT_BASE}${searchParams.toString() ? `?${searchParams}` : ""}`,
                      initialTab: "interactions" as const,
                      scrollToInsights: true,
                      engagementAction: row.recommended_action.title,
                    }}
                    className="btn engagement-act-link"
                  >
                    Act — {channelLabel(row.recommended_action.channel_hint)}
                  </Link>
                  <Link
                    to={customerPath(row.customer_id)}
                    state={{
                      businessReturn: `${ENGAGEMENT_BASE}${searchParams.toString() ? `?${searchParams}` : ""}`,
                      initialTab: "interactions" as const,
                    }}
                    className="btn secondary engagement-act-link"
                  >
                    View touchpoints
                  </Link>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
