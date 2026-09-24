import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { formatPeriodLabel } from "./charts/analyticsChartUtils";
import { useNavigate } from "react-router-dom";
import {
  CustomerSegment,
  KpiTargetProgress,
  PortfolioAnalytics,
  PortfolioKpis,
} from "../api";
import { CUSTOMER_BASE } from "../appRoutes";
import { ChartValueMetric } from "../chartFilter";
import { cohortSearchString } from "../cohortQuery";
import { formatMoneyIls, formatNumber, formatRatePercent } from "../localeFormat";
import BookValueChart from "./charts/BookValueChart";
import ChurnHorizonChart from "./charts/ChurnHorizonChart";
import EngagementObjectiveChart from "./charts/EngagementObjectiveChart";
import InvestmentReturnsChart from "./charts/InvestmentReturnsChart";
import PremiumMomentumChart from "./charts/PremiumMomentumChart";
import SavingsAumObjectiveChart from "./charts/SavingsAumObjectiveChart";
import CohortVsBookBanner from "./CohortVsBookBanner";
import { useAgentCopilot } from "../agentCopilotContext";
import PortfolioKpiCard from "./PortfolioKpiCard";
import ReviewStarRating from "./ReviewStarRating";
import { formatShareOfBook } from "../cohortBaseline";
import { portfolioChartScopeKey } from "../portfolioSegmentCache";

type Props = {
  data: PortfolioAnalytics | null;
  bookBaseline: PortfolioAnalytics | null;
  loading: boolean;
  refreshing: boolean;
  cohortLabel?: string | null;
  segment: CustomerSegment;
  chartInteractive?: boolean;
  /** Phone / copilot focus: KPI cards only. */
  minimal?: boolean;
};

function retentionKpiSub(
  kpis: PortfolioKpis | undefined,
  t: (key: string, opts?: Record<string, unknown>) => string,
): string | undefined {
  if (!kpis) return undefined;
  const w = kpis.weighted_churn_probability;
  if (w == null || Number.isNaN(w)) {
    return t("business.portfolio.retentionRunScoring");
  }
  const high = kpis.high_risk_customers ?? 0;
  const med = kpis.medium_risk_customers ?? 0;
  const low = kpis.low_risk_customers ?? 0;
  return t("business.portfolio.retentionSub", {
    pct: (w * 100).toFixed(2),
    high,
    med,
    low,
  });
}

function formatTargetLabel(key: string, progress: KpiTargetProgress): string {
  if (key === "annual_retention_rate_forecast") {
    return formatRatePercent(progress.target);
  }
  if (key === "book_growth_pct" || key === "high_risk_book_pct") {
    return `${progress.target}%`;
  }
  if (key === "active_customers") {
    return formatNumber(progress.target);
  }
  if (
    key === "total_book_value" ||
    key === "value_at_risk_12m" ||
    key === "avg_customer_value"
  ) {
    return formatMoneyIls(progress.target);
  }
  return String(progress.target);
}

export default function PortfolioAnalyticsSection({
  data,
  bookBaseline,
  loading,
  refreshing,
  cohortLabel,
  segment,
  chartInteractive = true,
  minimal = false,
}: Props) {
  const { t } = useTranslation();
  const emDash = t("common.emDash");
  const navigate = useNavigate();
  const { openRetentionPlaybook } = useAgentCopilot();
  const kpis = data?.kpis;
  const targets = data?.kpi_targets ?? {};
  const dataSynced = data != null && data.segment === segment;
  const chartLoading = loading || !dataSynced;

  const goToCustomerList = useCallback(
    (metric: ChartValueMetric) =>
      (selection: { period: string; kind?: string }) => {
        if (selection.kind === "forecast") return;
        navigate(
          `${CUSTOMER_BASE}${cohortSearchString({
            segment,
            asOf: selection.period,
            metric,
            page: 1,
            sortBy: metric === "at_risk" ? "customer_value" : undefined,
          })}`,
        );
      },
    [navigate, segment],
  );

  const progress = (key: string) => targets[key] ?? null;
  const cohortScoped = segment !== "customers_all";
  const cohortCaption = cohortLabel
    ? t("cohort.filteredBy", { label: cohortLabel })
    : cohortScoped
      ? t("cohort.filteredCohort")
      : t("cohort.fullActiveBook");

  const historyPeriodRange = useMemo(() => {
    const pts = data?.value_points ?? [];
    if (pts.length === 0) return null;
    const first = formatPeriodLabel(pts[0].period);
    const last = formatPeriodLabel(pts[pts.length - 1].period);
    return t("business.historyMonths", { first, last, count: pts.length });
  }, [data?.value_points, t]);

  const chartScopeKey = portfolioChartScopeKey(segment, data);
  const showBookCompare = cohortScoped && bookBaseline != null && data != null;
  const baselineHistory = showBookCompare ? bookBaseline.value_points : undefined;
  const baselineChurn = showBookCompare ? bookBaseline.churn_forecast : undefined;
  const baselineInvestments = showBookCompare ? bookBaseline.investment_returns : undefined;

  return (
    <div
      className={`portfolio-analytics in-panel${cohortScoped ? " portfolio-analytics-filtered" : ""}`}
      key={chartScopeKey}
    >
      {showBookCompare && !minimal && (
        <CohortVsBookBanner
          cohortLabel={cohortLabel ?? t("business.cohort.filteredBadge")}
          cohort={data}
          book={bookBaseline}
        />
      )}
      {!minimal && (
        <div className="panel-head value-chart-head">
          <div>
            <h2 className="subsection-title">{t("business.portfolio.sectionGrowth")}</h2>
            <p className="muted small">
              {cohortScoped
                ? t("business.portfolio.ledeFiltered", { caption: cohortCaption })
                : t("business.portfolio.ledeFull")}
              {historyPeriodRange && (
                <>
                  {" "}
                  {t("business.portfolio.bookHistory", { range: historyPeriodRange })}
                </>
              )}
            </p>
          </div>
        </div>
      )}
      {minimal && (
        <p className="muted small mobile-focus-lead">
          {t("business.portfolio.mobileLead", { caption: cohortCaption })}
        </p>
      )}

      <div className="portfolio-kpi-grid">
        <PortfolioKpiCard
          label={t("business.portfolio.kpi.totalBookValue")}
          value={formatMoneyIls(kpis?.total_book_value)}
          sub={
            showBookCompare && kpis && bookBaseline.kpis
              ? formatShareOfBook(kpis.total_book_value, bookBaseline.kpis.total_book_value) ??
                undefined
              : undefined
          }
          progress={progress("total_book_value")}
          targetLabel={
            progress("total_book_value")
              ? formatTargetLabel("total_book_value", progress("total_book_value")!)
              : null
          }
          loading={chartLoading}
        />
        <PortfolioKpiCard
          label={t("business.portfolio.kpi.retentionForecast")}
          value={formatRatePercent(kpis?.annual_retention_rate_forecast, 2, emDash)}
          sub={retentionKpiSub(kpis, t)}
          progress={progress("annual_retention_rate_forecast")}
          targetLabel={
            progress("annual_retention_rate_forecast")
              ? formatTargetLabel(
                  "annual_retention_rate_forecast",
                  progress("annual_retention_rate_forecast")!,
                )
              : null
          }
          loading={chartLoading}
        />
        <PortfolioKpiCard
          label={t("business.portfolio.kpi.valueAtChurnRisk")}
          value={formatMoneyIls(kpis?.value_at_risk_12m)}
          actionHint={t("business.portfolio.retentionQueueHint")}
          onClick={() => openRetentionPlaybook(segment, cohortLabel ?? null)}
          sub={
            kpis?.weighted_churn_probability != null
              ? t("business.portfolio.valueAtRiskSub")
              : undefined
          }
          progress={progress("value_at_risk_12m")}
          targetLabel={
            progress("value_at_risk_12m")
              ? formatTargetLabel("value_at_risk_12m", progress("value_at_risk_12m")!)
              : null
          }
          loading={chartLoading}
        />
        <PortfolioKpiCard
          label={t("business.portfolio.kpi.activeCustomers")}
          value={formatNumber(kpis?.active_customers ?? 0)}
          progress={progress("active_customers")}
          targetLabel={
            progress("active_customers")
              ? formatTargetLabel("active_customers", progress("active_customers")!)
              : null
          }
          loading={chartLoading}
        />
        <PortfolioKpiCard
          label={t("business.portfolio.kpi.policyRecords")}
          value={formatNumber(kpis?.total_policies ?? 0)}
          sub={t("business.portfolio.policyRecordsSub", {
            active: formatNumber(kpis?.active_policies ?? 0),
            avg: (kpis?.avg_policies_per_customer ?? 0).toFixed(1),
          })}
          loading={chartLoading}
        />
        <PortfolioKpiCard
          label={t("business.portfolio.kpi.avgCustomerValue")}
          value={formatMoneyIls(kpis?.avg_customer_value)}
          progress={progress("avg_customer_value")}
          targetLabel={
            progress("avg_customer_value")
              ? formatTargetLabel("avg_customer_value", progress("avg_customer_value")!)
              : null
          }
          loading={chartLoading}
        />
        <PortfolioKpiCard
          label={t("business.portfolio.kpi.highRiskBookShare")}
          value={
            kpis?.high_risk_book_pct != null ? `${kpis.high_risk_book_pct}%` : emDash
          }
          sub={t("business.portfolio.highRiskShareSub", {
            count: kpis?.high_risk_customers ?? 0,
          })}
          progress={progress("high_risk_book_pct")}
          targetLabel={
            progress("high_risk_book_pct")
              ? formatTargetLabel("high_risk_book_pct", progress("high_risk_book_pct")!)
              : null
          }
          loading={chartLoading}
        />
        <PortfolioKpiCard
          label={t("business.portfolio.kpi.bookGrowthHistory")}
          value={
            kpis?.book_growth_pct != null
              ? `${kpis.book_growth_pct >= 0 ? "+" : ""}${kpis.book_growth_pct}%`
              : emDash
          }
          progress={progress("book_growth_pct")}
          targetLabel={
            progress("book_growth_pct")
              ? formatTargetLabel("book_growth_pct", progress("book_growth_pct")!)
              : null
          }
          loading={chartLoading}
        />
        <PortfolioKpiCard
          label={t("business.portfolio.kpi.avgReviewScore")}
          value={
            kpis?.avg_review_rating != null
              ? t("business.portfolio.reviewScoreValue", {
                  avg: kpis.avg_review_rating.toFixed(1),
                })
              : emDash
          }
          sub={
            kpis?.review_count
              ? t("business.portfolio.reviewScoreSub", { count: kpis.review_count })
              : t("business.portfolio.reviewScoreSubEmpty")
          }
          footer={
            kpis?.avg_review_rating != null ? (
              <ReviewStarRating
                average={kpis.avg_review_rating}
                reviewCount={kpis.review_count}
                compact
              />
            ) : undefined
          }
          loading={chartLoading}
        />
      </div>

      {!minimal && (
      <div
        className={`portfolio-charts-grid${refreshing ? " portfolio-charts-refreshing" : ""}`}
      >
        <BookValueChart
          key={`book-${chartScopeKey}`}
          history={data?.value_points ?? []}
          baselineHistory={baselineHistory}
          loading={chartLoading}
          interactive={chartInteractive}
          onPeriodSelect={goToCustomerList("total")}
        />
        <InvestmentReturnsChart
          key={`returns-${chartScopeKey}`}
          series={data?.investment_returns ?? []}
          baselineSeries={baselineInvestments}
          loading={chartLoading}
          interactive={chartInteractive}
          onPeriodSelect={goToCustomerList("investment")}
        />
        <ChurnHorizonChart
          key={`churn-${chartScopeKey}`}
          series={data?.churn_forecast ?? []}
          baselineSeries={baselineChurn}
          loading={chartLoading}
          interactive={chartInteractive}
          onPeriodSelect={goToCustomerList("at_risk")}
        />
      </div>
      )}

      {!minimal && (
      <>
      <div className="portfolio-objectives-head">
        <h2 className="subsection-title">{t("business.portfolio.objectivesTitle")}</h2>
        <p className="muted small">
          {cohortScoped ? `${cohortCaption} · ` : ""}
          {data?.objectives_note ?? t("business.portfolio.objectivesDefaultNote")}
        </p>
      </div>
      <div
        className={`portfolio-charts-grid portfolio-objectives-grid${refreshing ? " portfolio-charts-refreshing" : ""}`}
      >
        <SavingsAumObjectiveChart
          key={`aum-${chartScopeKey}`}
          series={data?.savings_aum_trend ?? []}
          loading={chartLoading}
        />
        <PremiumMomentumChart
          key={`premium-${chartScopeKey}`}
          series={data?.premium_momentum_trend ?? []}
          loading={chartLoading}
        />
        <EngagementObjectiveChart
          key={`engagement-${chartScopeKey}`}
          series={data?.engagement_trend ?? []}
          loading={chartLoading}
        />
      </div>
      </>
      )}
      {refreshing && !minimal && (
        <p className="value-chart-refresh-label muted small">{t("business.portfolio.updating")}</p>
      )}

      {data?.methodology_note && !minimal && (
        <p className="muted small portfolio-methodology">{data.methodology_note}</p>
      )}

    </div>
  );
}
