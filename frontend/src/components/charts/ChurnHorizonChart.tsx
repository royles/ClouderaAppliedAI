import { useMemo } from "react";
import { ChurnForecastPoint } from "../../api";
import AnalyticsLineChart, { moneyTooltip } from "./AnalyticsLineChart";

type Props = {
  series: ChurnForecastPoint[];
  loading?: boolean;
};

export default function ChurnHorizonChart({ series, loading }: Props) {
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
      moneyTooltip("Book", p.total_book_value),
      moneyTooltip("At risk", p.value_at_risk),
      moneyTooltip("Retained", p.expected_retained_value),
      `Retention ${((p.implied_retention_rate ?? 0) * 100).toFixed(1)}%`,
    ],
  }));

  return (
    <AnalyticsLineChart
      title="Churn horizon"
      subtitle="Value at risk, retained book, and 12-month lapse forecast (right of divider)."
      points={points}
      loading={loading}
      forecastDividerIndex={forecastStart}
      series={[
        {
          id: "retained",
          label: "Expected retained",
          className: "chart-line-retained",
          values: series.map((p) => p.expected_retained_value),
        },
        {
          id: "risk",
          label: "Value at risk",
          className: "chart-line-risk",
          values: series.map((p) => p.value_at_risk),
          dashed: true,
        },
        {
          id: "book",
          label: "Total book (actual)",
          className: "chart-line-total",
          values: bookActual,
        },
        {
          id: "book-f",
          label: "Retained book (forecast)",
          className: "chart-line-forecast",
          values: bookForecast,
          dashed: true,
        },
      ]}
      emptyMessage="No churn horizon data for this cohort."
    />
  );
}
