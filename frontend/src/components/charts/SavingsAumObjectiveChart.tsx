import { SavingsAumTrendPoint } from "../../api";
import AnalyticsLineChart, { moneyTooltip } from "./AnalyticsLineChart";
import { formatTooltipCount } from "./analyticsChartUtils";

type Props = {
  series: SavingsAumTrendPoint[];
  loading?: boolean;
};

export default function SavingsAumObjectiveChart({ series, loading }: Props) {
  const points = series.map((p) => ({
    period: p.period,
    kind: "actual" as const,
    tooltipLines: [
      moneyTooltip("Accumulation (AUM)", p.accumulation_total),
      `${formatTooltipCount(p.active_savers)} active savers`,
      `${formatTooltipCount(p.savings_policies)} savings policies`,
    ],
  }));

  return (
    <AnalyticsLineChart
      title="Long-term savings (AUM)"
      subtitle="Pension, provident & savings accumulation — Migdal profitable growth pillar."
      points={points}
      loading={loading}
      interactive={false}
      series={[
        {
          id: "aum",
          visualKey: "obj-aum",
          label: "Accumulation",
          values: series.map((p) => p.accumulation_total),
        },
      ]}
      emptyMessage="No savings snapshot history for the active book yet."
    />
  );
}
