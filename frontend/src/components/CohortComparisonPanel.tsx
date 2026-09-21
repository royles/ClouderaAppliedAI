import { CustomerSegment, DomainCount, PortfolioAnalytics } from "../api";
import { formatShareOfBook } from "../cohortBaseline";
import { formatMoneyIls } from "../formatMoney";

type Props = {
  primaryLabel: string;
  compareLabel: string;
  primary: PortfolioAnalytics;
  compare: PortfolioAnalytics;
  primarySegment: CustomerSegment;
  compareSegment: CustomerSegment;
};

function deltaPct(primary: number, compare: number): string {
  if (!compare) return "—";
  const pct = ((primary - compare) / compare) * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}% vs compare`;
}

export default function CohortComparisonPanel({
  primaryLabel,
  compareLabel,
  primary,
  compare,
}: Props) {
  const pk = primary.kpis;
  const ck = compare.kpis;
  if (!pk || !ck) return null;

  const rows: Array<{
    label: string;
    primary: string;
    compare: string;
    delta: string;
  }> = [
    {
      label: "Active customers",
      primary: pk.active_customers.toLocaleString(),
      compare: ck.active_customers.toLocaleString(),
      delta: deltaPct(pk.active_customers, ck.active_customers),
    },
    {
      label: "Total book value",
      primary: formatMoneyIls(pk.total_book_value),
      compare: formatMoneyIls(ck.total_book_value),
      delta:
        formatShareOfBook(pk.total_book_value, ck.total_book_value) ?? deltaPct(
          pk.total_book_value,
          ck.total_book_value,
        ),
    },
    {
      label: "Value at churn risk",
      primary: formatMoneyIls(pk.value_at_risk_12m),
      compare: formatMoneyIls(ck.value_at_risk_12m),
      delta: deltaPct(pk.value_at_risk_12m, ck.value_at_risk_12m),
    },
    {
      label: "12m retention (forecast)",
      primary:
        pk.annual_retention_rate_forecast != null
          ? `${(pk.annual_retention_rate_forecast * 100).toFixed(2)}%`
          : "—",
      compare:
        ck.annual_retention_rate_forecast != null
          ? `${(ck.annual_retention_rate_forecast * 100).toFixed(2)}%`
          : "—",
      delta:
        pk.annual_retention_rate_forecast != null &&
        ck.annual_retention_rate_forecast != null
          ? `${((pk.annual_retention_rate_forecast - ck.annual_retention_rate_forecast) * 100).toFixed(2)} pts`
          : "—",
    },
  ];

  return (
    <div className="cohort-comparison-panel">
      <div className="cohort-comparison-head">
        <h3 className="subsection-title">Cohort comparison</h3>
        <p className="muted small">
          Side-by-side KPIs for the selected card vs a second cohort (charts above stay on the
          primary selection).
        </p>
      </div>
      <div className="cohort-comparison-grid">
        <div className="cohort-comparison-col cohort-comparison-col-head">
          <span className="muted small">Metric</span>
          <span className="cohort-comparison-primary-tag">{primaryLabel}</span>
          <span className="cohort-comparison-compare-tag">{compareLabel}</span>
          <span className="muted small">Delta</span>
        </div>
        {rows.map((row) => (
          <div key={row.label} className="cohort-comparison-row">
            <span className="cohort-comparison-metric">{row.label}</span>
            <strong>{row.primary}</strong>
            <span>{row.compare}</span>
            <span className="cohort-comparison-delta">{row.delta}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function compareDomainLabel(
  overview: { domains: DomainCount[] } | null,
  segment: CustomerSegment,
): string {
  if (segment === "customers_all") return "Full book";
  const match = overview?.domains.find((d) => d.filter_key === segment);
  return match?.domain ?? segment;
}
