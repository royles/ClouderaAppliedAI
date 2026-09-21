import { ValueHistoryPoint } from "../../api";
import { ChartPeriodSelection } from "../../chartFilter";
import AnalyticsLineChart, { moneyTooltip } from "./AnalyticsLineChart";

type Props = {
  history: ValueHistoryPoint[];
  loading?: boolean;
  interactive?: boolean;
  onPeriodSelect?: (selection: ChartPeriodSelection) => void;
};

export default function BookValueChart({
  history,
  loading,
  interactive,
  onPeriodSelect,
}: Props) {
  const points = history.map((p) => ({
    period: p.period,
    kind: "actual" as const,
    tooltipLines: [
      moneyTooltip("Total book", p.total_value),
      moneyTooltip("Investments", p.investment_value),
      moneyTooltip("Coverage", p.coverage_value),
    ],
  }));

  return (
    <AnalyticsLineChart
      title="Book value"
      subtitle="Customer book value (sum of each customer's policies) — investments plus coverage & savings."
      points={points}
      loading={loading}
      series={[
        {
          id: "total",
          visualKey: "book-total",
          label: "Total book",
          values: history.map((p) => p.total_value),
        },
        {
          id: "investment",
          visualKey: "book-investment",
          label: "Investments",
          values: history.map((p) => p.investment_value),
        },
        {
          id: "coverage",
          visualKey: "book-coverage",
          label: "Coverage & savings",
          values: history.map((p) => p.coverage_value),
        },
      ]}
      emptyMessage="No book history for this cohort."
      interactive={interactive}
      onPeriodSelect={onPeriodSelect}
    />
  );
}
