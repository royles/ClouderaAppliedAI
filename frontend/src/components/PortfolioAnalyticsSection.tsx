import { PortfolioAnalytics } from "../api";
import { formatMoneyIls } from "../formatMoney";
import BookValueChart from "./charts/BookValueChart";
import ChurnHorizonChart from "./charts/ChurnHorizonChart";
import InvestmentReturnsChart from "./charts/InvestmentReturnsChart";

type Props = {
  data: PortfolioAnalytics | null;
  loading: boolean;
  refreshing: boolean;
  cohortLabel?: string | null;
};

function formatPct(rate: number | null | undefined, digits = 1) {
  if (rate == null || Number.isNaN(rate)) return "—";
  return `${(rate * 100).toFixed(digits)}%`;
}

export default function PortfolioAnalyticsSection({
  data,
  loading,
  refreshing,
  cohortLabel,
}: Props) {
  const kpis = data?.kpis;
  const chartLoading = loading && !data;

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
        <div className="portfolio-kpi">
          <span className="label">Total book value</span>
          <strong>{loading ? "…" : formatMoneyIls(kpis?.total_book_value)}</strong>
        </div>
        <div className="portfolio-kpi">
          <span className="label">12m retention (forecast)</span>
          <strong>
            {loading ? "…" : formatPct(kpis?.annual_retention_rate_forecast)}
          </strong>
        </div>
        <div className="portfolio-kpi">
          <span className="label">Value at churn risk</span>
          <strong>{loading ? "…" : formatMoneyIls(kpis?.value_at_risk_12m)}</strong>
        </div>
        <div className="portfolio-kpi">
          <span className="label">Active customers</span>
          <strong>
            {loading ? "…" : (kpis?.active_customers ?? 0).toLocaleString()}
          </strong>
        </div>
        <div className="portfolio-kpi">
          <span className="label">Avg customer value</span>
          <strong>{loading ? "…" : formatMoneyIls(kpis?.avg_customer_value)}</strong>
        </div>
        <div className="portfolio-kpi">
          <span className="label">High-risk book share</span>
          <strong>
            {loading
              ? "…"
              : kpis?.high_risk_book_pct != null
                ? `${kpis.high_risk_book_pct}%`
                : "—"}
          </strong>
          <span className="muted small kpi-sub">
            {kpis?.high_risk_customers ?? 0} high-risk customers
          </span>
        </div>
        <div className="portfolio-kpi">
          <span className="label">Book growth (history)</span>
          <strong>
            {loading
              ? "…"
              : kpis?.book_growth_pct != null
                ? `${kpis.book_growth_pct >= 0 ? "+" : ""}${kpis.book_growth_pct}%`
                : "—"}
          </strong>
        </div>
        <div className="portfolio-kpi">
          <span className="label">Avg policies / customer</span>
          <strong>
            {loading ? "…" : (kpis?.avg_policies_per_customer ?? 0).toFixed(1)}
          </strong>
        </div>
      </div>

      <div
        className={`portfolio-charts-grid${refreshing ? " portfolio-charts-refreshing" : ""}`}
      >
        <BookValueChart history={data?.value_points ?? []} loading={chartLoading} />
        <InvestmentReturnsChart
          series={data?.investment_returns ?? []}
          loading={chartLoading}
        />
        <ChurnHorizonChart series={data?.churn_forecast ?? []} loading={chartLoading} />
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
