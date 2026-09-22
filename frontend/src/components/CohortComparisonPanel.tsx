import { useTranslation } from "react-i18next";
import { CustomerSegment, DomainCount, PortfolioAnalytics } from "../api";
import { formatShareOfBook } from "../cohortBaseline";
import { formatMoneyIls } from "../formatMoney";
import { cohortSegmentLabel } from "../i18n/segments";
import { formatNumber } from "../localeFormat";
import i18n from "../i18n";

type Props = {
  primaryLabel: string;
  compareLabel: string;
  primary: PortfolioAnalytics;
  compare: PortfolioAnalytics;
  primarySegment: CustomerSegment;
  compareSegment: CustomerSegment;
};

function deltaPct(primary: number, compare: number): string {
  if (!compare) return i18n.t("common.emDash");
  const pct = ((primary - compare) / compare) * 100;
  const sign = pct >= 0 ? "+" : "";
  return i18n.t("business.compare.deltaVsCompare", {
    sign,
    pct: pct.toFixed(1),
  });
}

export default function CohortComparisonPanel({
  primaryLabel,
  compareLabel,
  primary,
  compare,
}: Props) {
  const { t } = useTranslation();
  const pk = primary.kpis;
  const ck = compare.kpis;
  if (!pk || !ck) return null;

  const rows: Array<{
    labelKey: string;
    primary: string;
    compare: string;
    delta: string;
  }> = [
    {
      labelKey: "business.compareRows.activeCustomers",
      primary: formatNumber(pk.active_customers),
      compare: formatNumber(ck.active_customers),
      delta: deltaPct(pk.active_customers, ck.active_customers),
    },
    {
      labelKey: "business.compareRows.totalBookValue",
      primary: formatMoneyIls(pk.total_book_value),
      compare: formatMoneyIls(ck.total_book_value),
      delta:
        formatShareOfBook(pk.total_book_value, ck.total_book_value) ?? deltaPct(
          pk.total_book_value,
          ck.total_book_value,
        ),
    },
    {
      labelKey: "business.compareRows.valueAtChurnRisk",
      primary: formatMoneyIls(pk.value_at_risk_12m),
      compare: formatMoneyIls(ck.value_at_risk_12m),
      delta: deltaPct(pk.value_at_risk_12m, ck.value_at_risk_12m),
    },
    {
      labelKey: "business.compareRows.retentionForecast",
      primary:
        pk.annual_retention_rate_forecast != null
          ? `${(pk.annual_retention_rate_forecast * 100).toFixed(2)}%`
          : t("common.emDash"),
      compare:
        ck.annual_retention_rate_forecast != null
          ? `${(ck.annual_retention_rate_forecast * 100).toFixed(2)}%`
          : t("common.emDash"),
      delta:
        pk.annual_retention_rate_forecast != null &&
        ck.annual_retention_rate_forecast != null
          ? t("business.compare.deltaPts", {
              pts: (
                (pk.annual_retention_rate_forecast - ck.annual_retention_rate_forecast) *
                100
              ).toFixed(2),
            })
          : t("common.emDash"),
    },
  ];

  return (
    <div className="cohort-comparison-panel">
      <div className="cohort-comparison-head">
        <h3 className="subsection-title">{t("business.compare.panelTitle")}</h3>
        <p className="muted small">{t("business.compare.panelLede")}</p>
      </div>
      <div className="cohort-comparison-grid">
        <div className="cohort-comparison-col cohort-comparison-col-head">
          <span className="muted small">{t("business.compare.metric")}</span>
          <span className="cohort-comparison-primary-tag">{primaryLabel}</span>
          <span className="cohort-comparison-compare-tag">{compareLabel}</span>
          <span className="muted small">{t("business.compare.delta")}</span>
        </div>
        {rows.map((row) => (
          <div key={row.labelKey} className="cohort-comparison-row">
            <span className="cohort-comparison-metric">{t(row.labelKey)}</span>
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
  if (segment === "customers_all") return i18n.t("cohort.fullBook");
  const match = overview?.domains.find((d) => d.filter_key === segment);
  return match?.domain ?? cohortSegmentLabel(i18n.t, segment);
}
