import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { CustomerSegment, KpiTargetProgress, PortfolioAnalytics } from "../api";
import { CUSTOMER_BASE } from "../appRoutes";
import { ChartValueMetric } from "../chartFilter";
import { cohortSearchString } from "../cohortQuery";
import { formatMoneyIls } from "../formatMoney";
import BookValueChart from "./charts/BookValueChart";
import ChurnHorizonChart from "./charts/ChurnHorizonChart";
import InvestmentReturnsChart from "./charts/InvestmentReturnsChart";
import PortfolioKpiCard from "./PortfolioKpiCard";

type Props = {
  data: PortfolioAnalytics | null;
  loading: boolean;
  refreshing: boolean;
  cohortLabel?: string | null;
  segment: CustomerSegment;
  chartInteractive?: boolean;
};

function formatPct(rate: number | null | undefined, digits = 1) {
  if (rate == null || Number.isNaN(rate)) return "—";
  return `${(rate * 100).toFixed(digits)}%`;
}

function formatTargetLabel(key: string, progress: KpiTargetProgress): string {
  if (key === "annual_retention_rate_forecast") {
    return formatPct(progress.target);
  }
  if (key === "book_growth_pct" || key === "high_risk_book_pct") {
    return `${progress.target}%`;
  }
  if (key === "active_customers") {
    return progress.target.toLocaleString();
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
  loading,
  refreshing,
  cohortLabel,
  segment,
  chartInteractive = true,
}: Props) {
  const navigate = useNavigate();
  const kpis = data?.kpis;
  const targets = data?.kpi_targets ?? {};
  const chartLoading = loading && !data;

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

  return (
    <div className="portfolio-analytics in-panel">
      <div className="panel-head value-chart-head">
        <div>
          <h2 className="subsection-title">Book growth &amp; churn outlook</h2>
          <p className="muted small">
            {cohortLabel
              ? `Cohort: ${cohortLabel} — portfolio KPIs and retention-aware forecast.`
              : "Portfolio KPIs with industry-aligned churn forecast on total customer value."}
          </p>
        </div>
      </div>

      <div className="portfolio-kpi-grid">
        <PortfolioKpiCard
          label="Total book value"
          value={formatMoneyIls(kpis?.total_book_value)}
          progress={progress("total_book_value")}
          targetLabel={
            progress("total_book_value")
              ? formatTargetLabel("total_book_value", progress("total_book_value")!)
              : null
          }
          loading={loading}
        />
        <PortfolioKpiCard
          label="12m retention (forecast)"
          value={formatPct(kpis?.annual_retention_rate_forecast)}
          progress={progress("annual_retention_rate_forecast")}
          targetLabel={
            progress("annual_retention_rate_forecast")
              ? formatTargetLabel(
                  "annual_retention_rate_forecast",
                  progress("annual_retention_rate_forecast")!,
                )
              : null
          }
          loading={loading}
        />
        <PortfolioKpiCard
          label="Value at churn risk"
          value={formatMoneyIls(kpis?.value_at_risk_12m)}
          progress={progress("value_at_risk_12m")}
          targetLabel={
            progress("value_at_risk_12m")
              ? formatTargetLabel("value_at_risk_12m", progress("value_at_risk_12m")!)
              : null
          }
          loading={loading}
        />
        <PortfolioKpiCard
          label="Active customers"
          value={(kpis?.active_customers ?? 0).toLocaleString()}
          progress={progress("active_customers")}
          targetLabel={
            progress("active_customers")
              ? formatTargetLabel("active_customers", progress("active_customers")!)
              : null
          }
          loading={loading}
        />
        <PortfolioKpiCard
          label="Avg customer value"
          value={formatMoneyIls(kpis?.avg_customer_value)}
          progress={progress("avg_customer_value")}
          targetLabel={
            progress("avg_customer_value")
              ? formatTargetLabel("avg_customer_value", progress("avg_customer_value")!)
              : null
          }
          loading={loading}
        />
        <PortfolioKpiCard
          label="High-risk book share"
          value={
            kpis?.high_risk_book_pct != null ? `${kpis.high_risk_book_pct}%` : "—"
          }
          sub={`${kpis?.high_risk_customers ?? 0} high-risk customers`}
          progress={progress("high_risk_book_pct")}
          targetLabel={
            progress("high_risk_book_pct")
              ? formatTargetLabel("high_risk_book_pct", progress("high_risk_book_pct")!)
              : null
          }
          loading={loading}
        />
        <PortfolioKpiCard
          label="Book growth (history)"
          value={
            kpis?.book_growth_pct != null
              ? `${kpis.book_growth_pct >= 0 ? "+" : ""}${kpis.book_growth_pct}%`
              : "—"
          }
          progress={progress("book_growth_pct")}
          targetLabel={
            progress("book_growth_pct")
              ? formatTargetLabel("book_growth_pct", progress("book_growth_pct")!)
              : null
          }
          loading={loading}
        />
        <div className="portfolio-kpi">
          <div className="portfolio-kpi-head">
            <span className="label portfolio-kpi-label">Avg policies / customer</span>
            <strong className="portfolio-kpi-value">
              {loading ? "…" : (kpis?.avg_policies_per_customer ?? 0).toFixed(1)}
            </strong>
          </div>
        </div>
      </div>

      <div
        className={`portfolio-charts-grid${refreshing ? " portfolio-charts-refreshing" : ""}`}
      >
        <BookValueChart
          history={data?.value_points ?? []}
          loading={chartLoading}
          interactive={chartInteractive}
          onPeriodSelect={goToCustomerList("total")}
        />
        <InvestmentReturnsChart
          series={data?.investment_returns ?? []}
          loading={chartLoading}
          interactive={chartInteractive}
          onPeriodSelect={goToCustomerList("investment")}
        />
        <ChurnHorizonChart
          series={data?.churn_forecast ?? []}
          loading={chartLoading}
          interactive={chartInteractive}
          onPeriodSelect={goToCustomerList("at_risk")}
        />
      </div>
      {refreshing && (
        <p className="value-chart-refresh-label muted small">Updating analytics…</p>
      )}

      {data?.methodology_note && (
        <p className="muted small portfolio-methodology">{data.methodology_note}</p>
      )}
    </div>
  );
}
