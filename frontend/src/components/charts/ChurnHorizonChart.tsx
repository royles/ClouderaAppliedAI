import { useMemo } from "react";
import { ChurnForecastPoint } from "../../api";
import { ChartPeriodSelection } from "../../chartFilter";
import AnalyticsLineChart, { moneyTooltip } from "./AnalyticsLineChart";

type Props = {
  series: ChurnForecastPoint[];
  loading?: boolean;
  interactive?: boolean;
  onPeriodSelect?: (selection: ChartPeriodSelection) => void;
};

export default function ChurnHorizonChart({
  series,
  loading,
  interactive,
  onPeriodSelect,
}: Props) {
  const forecastStart = useMemo(
    () => series.findIndex((p) => p.kind === "forecast"),
    [series],
  );

  const bookActual = series.map((p, i) =>
    forecastStart >= 0 && i >= forecastStart ? null : p.total_book_value,
  );
  const bookForecast = series.map((p, i) => {
    if (forecastStart < 0) return null;
    if (i >= forecastStart - 1) return p.total_book_value;
    return null;
  });
  if (forecastStart > 0) {
    bookForecast[forecastStart - 1] = series[forecastStart - 1].total_book_value;
  }

  const points = series.map((p) => ({
    period: p.period,
    kind: p.kind,
    tooltipLines: [
      moneyTooltip("Total book", p.total_book_value),
      moneyTooltip("Expected retained", p.expected_retained_value),
      moneyTooltip("Value at risk", p.value_at_risk),
      `Retention ${((p.implied_retention_rate ?? 0) * 100).toFixed(1)}%`,
    ],
  }));

  return (
    <AnalyticsLineChart
      title="Churn horizon"
      subtitle="Retained vs at-risk value; dashed blue = survival forecast of total book."
      points={points}
      loading={loading}
      forecastDividerIndex={forecastStart}
      series={[
        {
          id: "book",
          visualKey: "churn-book-actual",
          label: "Total book (actual)",
          values: bookActual,
        },
        {
          id: "retained",
          visualKey: "churn-retained",
          label: "Expected retained value",
          values: series.map((p) => p.expected_retained_value),
        },
        {
          id: "risk",
          visualKey: "churn-at-risk",
          label: "Value at churn risk",
          values: series.map((p) => p.value_at_risk),
        },
        {
          id: "book-f",
          visualKey: "churn-book-forecast",
          label: "Projected book (forecast)",
          values: bookForecast,
        },
      ]}
      emptyMessage="No churn horizon data for this cohort."
      interactive={interactive}
      onPeriodSelect={onPeriodSelect}
    />
  );
}
