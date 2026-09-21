import { PremiumMomentumPoint } from "../../api";
import AnalyticsLineChart, { moneyTooltip } from "./AnalyticsLineChart";
import { formatTooltipCount } from "./analyticsChartUtils";

type Props = {
  series: PremiumMomentumPoint[];
  loading?: boolean;
};

export default function PremiumMomentumChart({ series, loading }: Props) {
  const points = series.map((p) => ({
    period: p.period,
    kind: "actual" as const,
    tooltipLines: [
      moneyTooltip("Monthly premium base", p.monthly_premium_total),
      `${formatTooltipCount(p.active_policy_count)} active policies`,
    ],
  }));

  return (
    <AnalyticsLineChart
      title="Active policies & premium"
      subtitle="General insurance momentum — expanding active relationships and premium base."
      points={points}
      loading={loading}
      interactive={false}
      series={[
        {
          id: "premium",
          visualKey: "obj-premium",
          label: "Monthly premium",
          values: series.map((p) => p.monthly_premium_total),
        },
      ]}
      emptyMessage="No policy premium trend for this cohort."
    />
  );
}
