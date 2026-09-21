import { ValueHistoryPoint } from "../../api";
import AnalyticsLineChart, { moneyTooltip } from "./AnalyticsLineChart";

type Props = {
  history: ValueHistoryPoint[];
  loading?: boolean;
};

export default function BookValueChart({ history, loading }: Props) {
  const points = history.map((p) => ({
    period: p.period,
    kind: "actual" as const,
    tooltipLines: [
      moneyTooltip("Total", p.total_value),
      moneyTooltip("Investments", p.investment_value),
      moneyTooltip("Coverage", p.coverage_value),
    ],
  }));

  return (
    <AnalyticsLineChart
      title="Book value"
      subtitle="Total customer value — investments plus coverage & savings."
      points={points}
      loading={loading}
      series={[
        {
          id: "total",
          label: "Total book",
          className: "chart-line-total",
          values: history.map((p) => p.total_value),
        },
        {
          id: "investment",
          label: "Investments",
          className: "chart-line-investment",
          values: history.map((p) => p.investment_value),
        },
        {
          id: "coverage",
          label: "Coverage",
          className: "chart-line-coverage",
          values: history.map((p) => p.coverage_value),
          dashed: true,
        },
      ]}
      emptyMessage="No book history for this cohort."
    />
  );
}
