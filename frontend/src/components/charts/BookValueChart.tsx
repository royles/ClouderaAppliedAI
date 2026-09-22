import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
  const periods = history.map((p) => p.period);
  const baselineTotals =
    baselineHistory && baselineHistory.length > 0
      ? valuesByPeriod(baselineHistory, periods, (p) => p.total_value)
      : null;
  const baselineByPeriod = baselineHistory
    ? new Map(baselineHistory.map((p) => [p.period, p.total_value]))
    : null;

  const totalLabel = baselineTotals
    ? t("charts.bookValue.cohortTotalBook")
    : t("charts.bookValue.totalBook");
  const investmentsLabel = t("charts.bookValue.investments");
  const coverageLabel = t("charts.bookValue.coverageSavings");
  const fullBookRefLabel = t("charts.bookValue.fullBookRef");

  const points = history.map((p) => {
    const lines = [
      moneyTooltip(totalLabel, p.total_value),
      moneyTooltip(investmentsLabel, p.investment_value),
      moneyTooltip(coverageLabel, p.coverage_value),
    ];
    const fullBook = baselineByPeriod?.get(p.period);
    if (fullBook != null) {
      lines.push(moneyTooltip(fullBookRefLabel, fullBook));
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
            label: fullBookRefLabel,
            values: baselineTotals,
          },
        ]
      : []),
    {
      id: "total",
      visualKey: "book-total" as const,
      label: totalLabel,
      values: history.map((p) => p.total_value),
    },
    {
      id: "investment",
      visualKey: "book-investment" as const,
      label: investmentsLabel,
      values: history.map((p) => p.investment_value),
    },
    {
      id: "coverage",
      visualKey: "book-coverage" as const,
      label: coverageLabel,
      values: history.map((p) => p.coverage_value),
    },
  ];

  return (
    <AnalyticsLineChart
      title={t("charts.bookValue.title")}
      subtitle={
        baselineTotals
          ? t("charts.bookValue.subtitleCohort")
          : t("charts.bookValue.subtitle")
      }
      points={points}
      loading={loading}
      series={series}
      emptyMessage={t("charts.bookValue.empty")}
      interactive={interactive}
      onPeriodSelect={onPeriodSelect}
    />
  );
}
