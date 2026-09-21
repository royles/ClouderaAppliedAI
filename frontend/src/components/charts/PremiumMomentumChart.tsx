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
      subtitle="Premium base (left axis) and active policy count (right axis) — one customer may hold many policies."
      points={points}
      loading={loading}
      interactive={false}
      series={[
        {
          id: "premium",
          visualKey: "obj-premium",
          label: "Monthly premium",
          values: series.map((p) => p.monthly_premium_total),
          axis: "primary",
          valueFormat: "money",
        },
        {
          id: "policies",
          visualKey: "obj-policies",
          label: "Active policies",
          values: series.map((p) => p.active_policy_count),
          axis: "secondary",
          valueFormat: "count",
        },
      ]}
      emptyMessage="No policy premium trend for the active book yet."
    />
  );
}
