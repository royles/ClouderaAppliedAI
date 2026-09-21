import { ValueHistoryPoint } from "../../api";
import { valuesByPeriod } from "../../cohortBaseline";
import { ChartPeriodSelection } from "../../chartFilter";
import AnalyticsLineChart, { moneyTooltip } from "./AnalyticsLineChart";

type Props = {
  history: ValueHistoryPoint[];
  baselineHistory?: ValueHistoryPoint[];
  loading?: boolean;
  interactive?: boolean;
  onPeriodSelect?: (selection: ChartPeriodSelection) => void;
};

export default function BookValueChart({
  history,
  baselineHistory,
  loading,
  interactive,
  onPeriodSelect,
}: Props) {
  const periods = history.map((p) => p.period);
  const baselineTotals =
    baselineHistory && baselineHistory.length > 0
      ? valuesByPeriod(baselineHistory, periods, (p) => p.total_value)
      : null;
  const baselineByPeriod = baselineHistory
    ? new Map(baselineHistory.map((p) => [p.period, p.total_value]))
    : null;

  const totalLabel = baselineTotals ? "Cohort total book" : "Total book";

  const points = history.map((p) => {
    const lines = [
      moneyTooltip(totalLabel, p.total_value),
      moneyTooltip("Investments", p.investment_value),
      moneyTooltip("Coverage & savings", p.coverage_value),
    ];
    const fullBook = baselineByPeriod?.get(p.period);
    if (fullBook != null) {
      lines.push(moneyTooltip("Full book (reference)", fullBook));
    }
    return {
      period: p.period,
      kind: "actual" as const,
      tooltipLines: lines,
    };
  });

  const series = [
    ...(baselineTotals
      ? [
          {
            id: "baseline-total",
            visualKey: "book-baseline-total" as const,
            label: "Full book (reference)",
            values: baselineTotals,
          },
        ]
      : []),
    {
      id: "total",
      visualKey: "book-total" as const,
      label: baselineTotals ? "Cohort total book" : "Total book",
      values: history.map((p) => p.total_value),
    },
    {
      id: "investment",
      visualKey: "book-investment" as const,
      label: "Investments",
      values: history.map((p) => p.investment_value),
    },
    {
      id: "coverage",
      visualKey: "book-coverage" as const,
      label: "Coverage & savings",
      values: history.map((p) => p.coverage_value),
    },
  ];

  return (
    <AnalyticsLineChart
      title="Book value"
      subtitle={
        baselineTotals
          ? "Solid lines = filtered cohort; dashed gray = full active customer book."
          : "Customer book value (sum of each customer's policies) — investments plus coverage & savings."
      }
      points={points}
      loading={loading}
      series={series}
      emptyMessage="No book history for this cohort."
      interactive={interactive}
      onPeriodSelect={onPeriodSelect}
    />
  );
}
