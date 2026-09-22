import { useTranslation } from "react-i18next";
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
import { parseBusinessSegment, patchBusinessSegment } from "../cohortQuery";
import { displayCustomerName, formatCity } from "../pii";
import { formatMoneyIls, formatNumber } from "../localeFormat";
import { useMobileFocus } from "../mobileUxContext";

function channelLabel(hint: string, t: (key: string) => string) {
  if (hint === "email") return t("engagement.channel.email");
  if (hint === "phone") return t("engagement.channel.phone");
  if (hint === "sms") return t("engagement.channel.sms");
  return hint;
}

export default function EngagementHubPage() {
  const { t } = useTranslation();
  const mobileFocus = useMobileFocus();
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
          setError(e instanceof Error ? e.message : t("errors.engagementLoadFailed"));
          setHub(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [segment, t]);

  const setSegment = (next: CustomerSegment) => {
    setSearchParams((prev) => patchBusinessSegment(prev, next), { replace: true });
  };

  const summary = hub?.book_summary;

  return (
    <>
      {!mobileFocus && <Breadcrumbs items={[{ label: t("engagement.title") }]} />}
      {!mobileFocus && (
      <section className="panel engagement-hub-intro">
        <h1 className="page-title">{t("engagement.title")}</h1>
        <p className="muted engagement-hub-lede">{t("engagement.lede")}</p>
      </section>
      )}

      {!mobileFocus && overview && (
        <section className="panel">
          <DomainFilterGrid
            overview={overview}
            segment={segment}
            onSelect={setSegment}
            helperText={t("engagement.domainFilter.helper")}
          />
        </section>
      )}

      {!mobileFocus && (
      <section className="panel">
        <div className="engagement-summary-grid">
          <div className="engagement-summary-card">
            <span className="label">{t("engagement.summary.touchpoints90.label")}</span>
            <strong>{loading ? "…" : formatNumber(summary?.total_touchpoints_90d ?? 0)}</strong>
            <span className="muted small">
              {t("engagement.summary.touchpoints90.sub", {
                count: summary?.customers_with_touchpoints_90d ?? 0,
              })}
            </span>
          </div>
          <div className="engagement-summary-card">
            <span className="label">{t("engagement.summary.digital90.label")}</span>
            <strong>{loading ? "…" : formatNumber(summary?.digital_touchpoints_90d ?? 0)}</strong>
            <span className="muted small">{t("engagement.summary.digital90.sub")}</span>
          </div>
          <div className="engagement-summary-card">
            <span className="label">{t("engagement.summary.reviews90.label")}</span>
            <strong>{loading ? "…" : formatNumber(summary?.review_events_90d ?? 0)}</strong>
            <span className="muted small">{t("engagement.summary.reviews90.sub")}</span>
          </div>
          <div className="engagement-summary-card engagement-summary-card-warn">
            <span className="label">{t("engagement.summary.openAgent.label")}</span>
            <strong>{loading ? "…" : formatNumber(summary?.unresolved_agent_questions ?? 0)}</strong>
            <span className="muted small">{t("engagement.summary.openAgent.sub")}</span>
          </div>
        </div>
      </section>
      )}

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2 className="subsection-title">
              {mobileFocus ? t("engagement.list.titleMobile") : t("engagement.list.title")}
            </h2>
            {!mobileFocus && hub != null && !loading && (
            <p className="muted small">
              {t("engagement.list.lede", {
                shown: hub.opportunities.length,
                total: hub.total,
              })}
            </p>
            )}
          </div>
        </div>

        {error && <p className="error">{error}</p>}

        {loading && !hub && (
          <p className="muted small">{t("engagement.loading")}</p>
        )}

        {!loading && hub && hub.opportunities.length === 0 && (
          <p className="muted small">{t("engagement.list.empty")}</p>
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
                    {formatCity(row.city_name)} ·{" "}
                    {t("engagement.list.bookSuffix", {
                      value: formatMoneyIls(row.customer_value),
                    })}
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
                <div className="engagement-influence-score" title={t("engagement.a11y.influenceTitle")}>
                  <span className="label">{t("engagement.influence.label")}</span>
                  <strong>{row.influence_score.toFixed(0)}</strong>
                </div>
              </div>

              {!mobileFocus && (
              <div className="engagement-touchpoint-strip">
                <span className="touchpoint-chip">
                  {t("engagement.touchpoints.count90", { count: row.touchpoints.events_last_90d })}
                </span>
                <span className="touchpoint-chip">
                  {t("engagement.touchpoints.webSearches", { count: row.touchpoints.web_searches_90d })}
                </span>
                <span className="touchpoint-chip">
                  {t("engagement.touchpoints.reviews", { count: row.touchpoints.reviews_90d })}
                </span>
                {row.touchpoints.unresolved_agent_questions > 0 && (
                  <span className="touchpoint-chip touchpoint-chip-warn">
                    {t("engagement.touchpoints.openQuestions", {
                      count: row.touchpoints.unresolved_agent_questions,
                    })}
                  </span>
                )}
                <span className="touchpoint-chip">
                  {t("engagement.touchpoints.daysSince", {
                    days: Math.round(row.touchpoints.days_since_last_touch),
                  })}
                </span>
              </div>
              )}

              <div className="engagement-action-block">
                <div>
                  <span className="label">{t("engagement.action.recommendedLabel")}</span>
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
                    {t("engagement.action.actChannel", {
                      channel: channelLabel(row.recommended_action.channel_hint, t),
                    })}
                  </Link>
                  <Link
                    to={customerPath(row.customer_id)}
                    state={{
                      businessReturn: `${ENGAGEMENT_BASE}${searchParams.toString() ? `?${searchParams}` : ""}`,
                      initialTab: "interactions" as const,
                    }}
                    className="btn secondary engagement-act-link"
                  >
                    {t("engagement.action.viewTouchpoints")}
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
