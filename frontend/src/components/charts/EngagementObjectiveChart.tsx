import { EngagementTrendPoint } from "../../api";
import AnalyticsLineChart from "./AnalyticsLineChart";
import { formatTooltipCount } from "./analyticsChartUtils";

type Props = {
  series: EngagementTrendPoint[];
  loading?: boolean;
};

export default function EngagementObjectiveChart({ series, loading }: Props) {
  const points = series.map((p) => ({
    period: p.period,
    kind: "actual" as const,
    tooltipLines: [
      `${formatTooltipCount(p.interaction_events)} total interactions`,
      `${formatTooltipCount(p.digital_touchpoints)} digital touchpoints`,
      `${formatTooltipCount(p.review_events)} reviews`,
    ],
  }));

  return (
    <AnalyticsLineChart
      title="Customer engagement"
      subtitle="Digital & service touchpoints — customer at the center pillar."
      points={points}
      loading={loading}
      interactive={false}
      valueFormat="count"
      series={[
        {
          id: "interactions",
          visualKey: "obj-engagement",
          label: "All interactions",
          values: series.map((p) => p.interaction_events),
        },
        {
          id: "digital",
          visualKey: "obj-digital",
          label: "Digital touchpoints",
          values: series.map((p) => p.digital_touchpoints),
        },
      ]}
      emptyMessage="No interaction history for the active book yet."
    />
  );
}
