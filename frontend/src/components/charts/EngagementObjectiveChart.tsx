import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { EngagementTrendPoint } from "../../api";
import AnalyticsBarChart from "./AnalyticsBarChart";
import { formatTooltipCount } from "./analyticsChartUtils";

type Props = {
  series: EngagementTrendPoint[];
  loading?: boolean;
};

export default function EngagementObjectiveChart({ series, loading }: Props) {
  const { t } = useTranslation();

  const points = useMemo(
    () =>
      series
        .filter((p) => p.avg_review_rating != null && !Number.isNaN(p.avg_review_rating))
        .map((p) => ({
          period: p.period,
          value: p.avg_review_rating as number,
          tooltipLines: [
            t("charts.engagementObjective.tooltipAvg", {
              avg: (p.avg_review_rating as number).toFixed(2),
            }),
            t("charts.engagementObjective.tooltipCount", {
              count: formatTooltipCount(p.review_events),
            }),
          ],
        })),
    [series, t],
  );

  return (
    <AnalyticsBarChart
      title={t("charts.engagementObjective.title")}
      subtitle={t("charts.engagementObjective.subtitle")}
      points={points}
      visualKey="obj-engagement"
      loading={loading}
      emptyMessage={t("charts.engagementObjective.empty")}
      yMin={0}
      yMax={5}
      legendLabel={t("charts.engagementObjective.legend")}
    />
  );
}
