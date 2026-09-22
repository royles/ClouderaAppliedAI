import { useTranslation } from "react-i18next";
import { EngagementTrendPoint } from "../../api";
import AnalyticsLineChart from "./AnalyticsLineChart";
import { formatTooltipCount } from "./analyticsChartUtils";

type Props = {
  series: EngagementTrendPoint[];
  loading?: boolean;
};

export default function EngagementObjectiveChart({ series, loading }: Props) {
  const { t } = useTranslation();
  const points = series.map((p) => ({
    period: p.period,
    kind: "actual" as const,
    tooltipLines: [
      `${formatTooltipCount(p.interaction_events)} all interactions`,
      `${formatTooltipCount(p.digital_touchpoints)} digital touchpoints`,
    ],
  }));

  return (
    <AnalyticsLineChart
      title={t("charts.engagementObjective.title")}
      subtitle={t("charts.engagementObjective.subtitle")}
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
      emptyMessage={t("charts.engagementObjective.empty")}
    />
  );
}
