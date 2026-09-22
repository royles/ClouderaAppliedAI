import { useTranslation } from "react-i18next";
import { PremiumMomentumPoint } from "../../api";
import AnalyticsLineBarChart from "./AnalyticsLineBarChart";
import { moneyTooltip } from "./AnalyticsLineChart";

type Props = {
  series: PremiumMomentumPoint[];
  loading?: boolean;
};

export default function PremiumMomentumChart({ series, loading }: Props) {
  const { t } = useTranslation();
  const points = series.map((p) => ({
    period: p.period,
    kind: "actual" as const,
    tooltipLines: [
      moneyTooltip(t("charts.premiumMomentum.legendPremium"), p.monthly_premium_total),
      t("charts.premiumMomentum.tooltipAvgPolicies", {
        avg: (p.avg_policies_per_customer ?? 0).toFixed(2),
      }),
      t("charts.premiumMomentum.tooltipPolicyCount", {
        count: p.active_policy_count,
      }),
    ],
  }));

  return (
    <AnalyticsLineBarChart
      title={t("charts.premiumMomentum.title")}
      subtitle={t("charts.premiumMomentum.subtitle")}
      points={points}
      loading={loading}
      line={{
        id: "premium",
        visualKey: "obj-premium",
        label: t("charts.premiumMomentum.legendPremium"),
        values: series.map((p) => p.monthly_premium_total),
      }}
      bars={{
        id: "avg-policies",
        visualKey: "obj-policies",
        label: t("charts.premiumMomentum.legendAvgPolicies"),
        values: series.map((p) => p.avg_policies_per_customer ?? 0),
      }}
      barFormat="average"
      emptyMessage={t("charts.premiumMomentum.empty")}
    />
  );
}
