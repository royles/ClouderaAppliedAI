import { useTranslation } from "react-i18next";
import { PremiumMomentumPoint } from "../../api";
import AnalyticsLineBarChart from "./AnalyticsLineBarChart";
import { moneyTooltip } from "./AnalyticsLineChart";
import { formatTooltipCount } from "./analyticsChartUtils";

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
      `${formatTooltipCount(p.active_policy_count)} ${t("charts.premiumMomentum.legendPolicies")}`,
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
        id: "policies",
        visualKey: "obj-policies",
        label: t("charts.premiumMomentum.legendPolicies"),
        values: series.map((p) => p.active_policy_count),
      }}
      emptyMessage={t("charts.premiumMomentum.empty")}
    />
  );
}
