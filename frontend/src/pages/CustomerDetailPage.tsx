import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useParams } from "react-router-dom";
import { CUSTOMER_BASE, ENGAGEMENT_BASE } from "../appRoutes";
import Breadcrumbs from "../components/Breadcrumbs";
import { rememberRecentCustomer } from "../recentCustomers";
import {
  CustomerDetail,
  fetchCustomer,
  fetchCustomerValueHistory,
  ValueHistoryPoint,
} from "../api";
import CustomerInsightsPanel from "../components/CustomerInsightsPanel";
import CustomerSummaryCard, {
  CustomerCardProfileDetails,
} from "../components/CustomerSummaryCard";
import CustomerValueChart from "../components/CustomerValueChart";
import { formatMoneyIls } from "../localeFormat";
import { engagementRecommendedAction } from "../i18n/recommendedActions";
import {
  formatLastLogin,
  maskDate,
  displayCustomerName,
} from "../pii";
import { useMobileFocus } from "../mobileUxContext";

type Tab = "policies" | "foreclosures" | "investments" | "interactions";

const CUSTOMER_TAB_PANEL_ID = "customer-records-tabpanel";

function formatEventType(t: (key: string) => string, type: string) {
  if (type === "REVIEW") return t("customer.interactions.eventType.review");
  if (type === "AGENT_QUESTION") return t("customer.interactions.eventType.agentQuestion");
  if (type === "WEB_SEARCH") return t("customer.interactions.eventType.webSearch");
  return type;
}

function interactionIcon(type: string) {
  if (type === "REVIEW") return "★";
  if (type === "AGENT_QUESTION") return "?";
  if (type === "WEB_SEARCH") return "⌕";
  return "•";
}

export default function CustomerDetailPage() {
  const { t } = useTranslation();
  const emDash = t("common.emDash");
  const mobileFocus = useMobileFocus();
  const { customerId } = useParams();
  const location = useLocation();
  const id = Number(customerId);
  const listBack =
    typeof location.state?.businessReturn === "string"
      ? location.state.businessReturn
      : CUSTOMER_BASE;
  const backFromCustomerList =
    listBack.startsWith(CUSTOMER_BASE) || listBack.startsWith(ENGAGEMENT_BASE);
  const hubBackLabel = listBack.startsWith(ENGAGEMENT_BASE)
    ? t("nav.engagement.short")
    : backFromCustomerList
      ? t("nav.customer.title")
      : t("nav.business.title");
  const hubBackLinkText = listBack.startsWith(ENGAGEMENT_BASE)
    ? t("customer.back.engagement")
    : backFromCustomerList
      ? t("customer.back.list")
      : t("customer.back.business");
  const secondaryHubLinkText = listBack.startsWith(ENGAGEMENT_BASE)
    ? t("customer.link.engagementHub")
    : backFromCustomerList
      ? t("customer.link.list")
      : t("customer.link.businessPortfolio");
  const [detail, setDetail] = useState<CustomerDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navState = location.state as {
    businessReturn?: string;
    initialTab?: Tab;
    scrollToInsights?: boolean;
    engagementAction?: string;
    engagementActionCode?: string;
    engagementUnresolvedCount?: number;
  } | null;
  const [tab, setTab] = useState<Tab>(navState?.initialTab ?? "policies");
  const engagementActionHint = useMemo(() => {
    if (navState?.engagementActionCode) {
      return engagementRecommendedAction(
        t,
        {
          action_code: navState.engagementActionCode,
          title: navState.engagementAction ?? "",
          detail: "",
        },
        { unresolvedCount: navState.engagementUnresolvedCount ?? 0 },
      ).title;
    }
    return navState?.engagementAction ?? null;
  }, [
    navState?.engagementAction,
    navState?.engagementActionCode,
    navState?.engagementUnresolvedCount,
    t,
  ]);
  const [activePolicy, setActivePolicy] = useState<number | null>(null);
  const [valueHistory, setValueHistory] = useState<ValueHistoryPoint[]>([]);
  const [valueHistoryLoading, setValueHistoryLoading] = useState(true);

  useEffect(() => {
    if (navState?.initialTab) {
      setTab(navState.initialTab);
    }
  }, [location.key, navState?.initialTab]);

  useEffect(() => {
    if (!navState?.scrollToInsights) return;
    const node = document.getElementById("customer-insights-anchor");
    node?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [detail, navState?.scrollToInsights]);

  useEffect(() => {
    if (!Number.isFinite(id)) {
      setError(t("errors.invalidCustomerId"));
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
          setError(e instanceof Error ? e.message : t("errors.customerNotFound"));
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
    const { profile, policies, investments, churn, interaction_summary } = detail;
    const investmentCount = new Set(
      investments.map((inv) => `${inv.policy_num}-${inv.fund_id ?? ""}`),
    ).size;
    const customerValue =
      valueHistory.length > 0
        ? valueHistory[valueHistory.length - 1].total_value
        : 0;
    const profileDetails: CustomerCardProfileDetails = {
      customer_type_dsc: profile.customer_type_dsc,
      birth_date: profile.birth_date,
      marital_status_dsc: profile.marital_status_dsc,
      street_name: profile.street_name,
      communication_dsc: profile.communication_dsc,
      last_interaction_ts: interaction_summary?.last_event_ts ?? null,
      churn_scored_at: churn?.scored_at ?? null,
      churn_model_version: churn?.model_version ?? null,
    };
    return {
      summary: {
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
        avg_review_rating:
          interaction_summary?.avg_review_rating_all ??
          interaction_summary?.avg_review_rating ??
          null,
        review_count: interaction_summary?.review_count ?? 0,
      },
      profileDetails,
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
            { label: t("common.loading") },
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
      {!mobileFocus && (
      <Breadcrumbs
        items={[
          { label: hubBackLabel, to: listBack },
          { label: displayCustomerName(profile.customer_name) },
        ]}
      />
      )}
      {!mobileFocus && (
      <p className="muted small customer-area-links">
        <Link to={listBack}>{secondaryHubLinkText}</Link>
        {!backFromCustomerList && (
          <>
            {" · "}
            <Link to={CUSTOMER_BASE}>{t("customer.homeLink")}</Link>
          </>
        )}
      </p>
      )}
      <section className="panel customer-detail-top">
        <div
          className={`customer-detail-hero-grid${mobileFocus ? " customer-detail-hero-grid-compact" : ""}`}
        >
          {customerCard && (
            <CustomerSummaryCard
              variant="static"
              customer={customerCard.summary}
              profileDetails={customerCard.profileDetails}
            />
          )}
          {!mobileFocus && (
            <div id="customer-insights-anchor" className="customer-detail-insights-pane">
              <CustomerInsightsPanel
                embedded
                customerId={profile.customer_id}
                churnTier={detail.churn?.churn_risk_tier}
              />
            </div>
          )}
        </div>
      </section>

      {!mobileFocus && engagementActionHint && (
        <p className="engagement-action-banner muted small">
          {t("customer.engagementHint.prefix")} <strong>{engagementActionHint}</strong>
        </p>
      )}

      {!mobileFocus && (
        <section className="panel customer-detail-records-panel">
          <div className="customer-detail-tabs-pane">
            <div
              className="tab-bar customer-detail-tab-bar"
              role="tablist"
              aria-label={t("customer.tabs.listLabel")}
            >
              <button
                type="button"
                role="tab"
                id="customer-tab-policies"
                aria-selected={tab === "policies"}
                aria-controls={CUSTOMER_TAB_PANEL_ID}
                className={tab === "policies" ? "tab active" : "tab"}
                onClick={() => setTab("policies")}
              >
                {t("customer.tabs.policies")} ({policies.length})
              </button>
              <button
                type="button"
                role="tab"
                id="customer-tab-foreclosures"
                aria-selected={tab === "foreclosures"}
                aria-controls={CUSTOMER_TAB_PANEL_ID}
                className={tab === "foreclosures" ? "tab active" : "tab"}
                onClick={() => setTab("foreclosures")}
              >
                {t("customer.tabs.foreclosures")} ({foreclosures.length})
              </button>
              <button
                type="button"
                role="tab"
                id="customer-tab-investments"
                aria-selected={tab === "investments"}
                aria-controls={CUSTOMER_TAB_PANEL_ID}
                className={tab === "investments" ? "tab active" : "tab"}
                onClick={() => setTab("investments")}
              >
                {t("customer.tabs.investments")} ({investments.length})
              </button>
              <button
                type="button"
                role="tab"
                id="customer-tab-interactions"
                aria-selected={tab === "interactions"}
                aria-controls={CUSTOMER_TAB_PANEL_ID}
                className={tab === "interactions" ? "tab active" : "tab"}
                onClick={() => setTab("interactions")}
              >
                {t("customer.tabs.interactions")} (
                {interaction_summary?.total_events ?? interactions.length})
              </button>
            </div>

            <div
              className="customer-detail-tab-body"
              role="tabpanel"
              id={CUSTOMER_TAB_PANEL_ID}
              aria-labelledby={`customer-tab-${tab}`}
            >
      {tab === "policies" && (
        <div className="customer-detail-tab-content">
          <h2 className="subsection-title">{t("customer.policies.title")}</h2>
          <p className="muted small">{t("customer.policies.hint")}</p>
          <div className="table-wrap">
            <table className="table table-interactive">
              <thead>
                <tr>
                  <th>{t("customer.policies.columns.number")}</th>
                  <th>{t("customer.policies.columns.type")}</th>
                  <th>{t("customer.policies.columns.status")}</th>
                  <th>{t("customer.policies.columns.active")}</th>
                  <th>{t("customer.policies.columns.monthlyPremium")}</th>
                </tr>
              </thead>
              <tbody>
                {policies.map((p) => {
                  const selected = activePolicy === p.policy_num;
                  const togglePolicy = () =>
                    setActivePolicy((prev) =>
                      prev === p.policy_num ? null : p.policy_num,
                    );
                  return (
                  <tr
                    key={p.policy_num}
                    className={selected ? "table-row-selected" : "table-row-click"}
                    tabIndex={0}
                    role="button"
                    aria-pressed={selected}
                    aria-label={
                      selected
                        ? t("customer.policies.rowSelectedA11y", { number: p.policy_num })
                        : t("customer.policies.rowA11y", { number: p.policy_num })
                    }
                    onClick={togglePolicy}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        togglePolicy();
                      }
                    }}
                  >
                    <td>{p.policy_num}</td>
                    <td>{p.policy_type_desc ?? emDash}</td>
                    <td>{p.policy_status_desc ?? emDash}</td>
                    <td>{p.is_active ? t("common.yes") : t("common.no")}</td>
                    <td>{formatMoneyIls(p.bruto_monthly_premium)}</td>
                  </tr>
                );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "foreclosures" && (
        <div className="customer-detail-tab-content">
          <h2 className="subsection-title">{t("customer.foreclosures.title")}</h2>
          {foreclosures.length === 0 ? (
            <p className="muted">{t("customer.foreclosures.empty")}</p>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>{t("customer.foreclosures.columns.proceeding")}</th>
                    <th>{t("customer.foreclosures.columns.amount")}</th>
                    <th>{t("customer.foreclosures.columns.date")}</th>
                    <th>{t("customer.foreclosures.columns.portfolio")}</th>
                  </tr>
                </thead>
                <tbody>
                  {foreclosures.map((f) => (
                    <tr key={f.foreclosures_number}>
                      <td>{f.foreclosures_number}</td>
                      <td>{formatMoneyIls(f.foreclosures_amount)}</td>
                      <td>{maskDate(f.foreclosures_date)}</td>
                      <td>{f.portfolio_number ?? emDash}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === "interactions" && (
        <div className="customer-detail-tab-content">
          <h2 className="subsection-title">{t("customer.interactions.title")}</h2>
          <p className="muted small">{t("customer.interactions.lede")}</p>
          {interaction_summary && (
            <div className="interaction-stats">
              <span>
                {t("customer.interactions.stats.last90d", {
                  count: interaction_summary.events_last_90d,
                })}
              </span>
              {interaction_summary.avg_review_rating != null && (
                <span>
                  {t("customer.interactions.stats.avgReview", {
                    avg: interaction_summary.avg_review_rating,
                  })}
                </span>
              )}
              {interaction_summary.unresolved_agent_questions > 0 && (
                <span className="warn-stat">
                  {t("customer.interactions.stats.openAgent", {
                    count: interaction_summary.unresolved_agent_questions,
                  })}
                </span>
              )}
            </div>
          )}
          {interactions.length === 0 ? (
            <p className="muted">{t("customer.interactions.empty")}</p>
          ) : (
            <ol className="interaction-timeline">
              {interactions.map((ev) => {
                const signal =
                  ev.event_type === "REVIEW" && ev.rating != null
                    ? t("customer.interactions.signal.stars", { rating: ev.rating })
                    : ev.event_type === "AGENT_QUESTION"
                      ? ev.resolved
                        ? t("customer.interactions.signal.resolved")
                        : t("customer.interactions.signal.open")
                      : ev.topic === "help_center"
                        ? t("customer.interactions.signal.helpSearch")
                        : t("customer.interactions.signal.productSearch");
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
                        <strong>{formatEventType(t, ev.event_type)}</strong>
                        <span className="muted small">{maskDate(ev.event_ts)}</span>
                      </div>
                      <p className="timeline-title">{ev.query_or_title ?? emDash}</p>
                      <p className="muted small timeline-meta">
                        {[ev.channel, signal].filter(Boolean).join(" · ")}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          )}
        </div>
      )}

      {tab === "investments" && (
        <div className="customer-detail-tab-content">
          <h2 className="subsection-title">{t("customer.investments.title")}</h2>
          {activePolicy != null && (
            <p className="filter-banner">
              {t("customer.investments.policyFilter")} <strong>{activePolicy}</strong>
              <button
                type="button"
                className="link-btn"
                onClick={() => setActivePolicy(null)}
              >
                {t("common.showAll")}
              </button>
            </p>
          )}
          {filteredInvestments.length === 0 ? (
            <p className="muted">{t("customer.investments.empty")}</p>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>{t("customer.investments.columns.policy")}</th>
                    <th>{t("customer.investments.columns.fund")}</th>
                    <th>{t("customer.investments.columns.snapshot")}</th>
                    <th>{t("customer.investments.columns.accumulation")}</th>
                    <th>{t("customer.investments.columns.ytdPl")}</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredInvestments.map((inv, idx) => (
                    <tr key={`${inv.policy_num}-${inv.fund_id}-${idx}`}>
                      <td>{inv.policy_num}</td>
                      <td>{inv.fund_id ?? emDash}</td>
                      <td>{maskDate(inv.snapshot_date)}</td>
                      <td>{formatMoneyIls(inv.accumulation_total)}</td>
                      <td>{formatMoneyIls(inv.yearly_profit_loss_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
            </div>
          </div>
        </section>
      )}

      {!mobileFocus && (
        <section className="panel customer-detail-chart-panel">
          <CustomerValueChart
            className="customer-detail-value-chart"
            title={t("charts.customerValue.title")}
            subtitle={t("charts.customerValue.subtitle")}
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
        </section>
      )}
    </>
  );
}
