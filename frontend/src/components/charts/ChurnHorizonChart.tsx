import { useTranslation } from "react-i18next";
import { useMemo } from "react";
import { ChurnForecastPoint } from "../../api";
import { ChartPeriodSelection } from "../../chartFilter";
import AnalyticsLineChart, { moneyTooltip } from "./AnalyticsLineChart";

type Props = {
  series: ChurnForecastPoint[];
  baselineSeries?: ChurnForecastPoint[];
  loading?: boolean;
  interactive?: boolean;
  onPeriodSelect?: (selection: ChartPeriodSelection) => void;
};

export default function ChurnHorizonChart({
  series,
  baselineSeries,
  loading,
  interactive,
  onPeriodSelect,
}: Props) {
  const { t } = useTranslation();
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

  const baselineBookActual = useMemo(() => {
    if (!baselineSeries?.length) return null;
    const periods = series.map((p) => p.period);
    const baselineByPeriod = new Map(
      baselineSeries.map((p) => [p.period, p.total_book_value]),
    );
    const baselineTotals = periods.map((period) => baselineByPeriod.get(period) ?? null);
    return baselineTotals.map((v, i) =>
      forecastStart >= 0 && i >= forecastStart ? null : v,
    );
  }, [baselineSeries, series, forecastStart]);

  const baselineByPeriod = useMemo(
    () => new Map(baselineSeries?.map((p) => [p.period, p.total_book_value]) ?? []),
    [baselineSeries],
  );

  const points = series.map((p) => {
    const lines = [
      moneyTooltip("Cohort total book", p.total_book_value),
      moneyTooltip("Expected retained", p.expected_retained_value),
      moneyTooltip("Value at risk", p.value_at_risk),
      `Retention ${((p.implied_retention_rate ?? 0) * 100).toFixed(1)}%`,
    ];
    const ref = baselineByPeriod.get(p.period);
    if (ref != null) {
      lines.push(moneyTooltip("Full book (reference)", ref));
    }
    return {
      period: p.period,
      kind: p.kind,
      tooltipLines: lines,
    };
  });

  const chartSeries = [
    ...(baselineBookActual
      ? [
          {
            id: "baseline-book",
            visualKey: "churn-baseline-book" as const,
            label: "Full book (reference)",
            values: baselineBookActual,
          },
        ]
      : []),
    {
      id: "book",
      visualKey: "churn-book-actual" as const,
      label: baselineBookActual ? "Cohort book (actual)" : "Total book (actual)",
      values: bookActual,
    },
    {
      id: "retained",
      visualKey: "churn-retained" as const,
      label: "Expected retained value",
      values: series.map((p) => p.expected_retained_value),
    },
    {
      id: "risk",
      visualKey: "churn-at-risk" as const,
      label: "Value at churn risk",
      values: series.map((p) => p.value_at_risk),
    },
    {
      id: "book-f",
      visualKey: "churn-book-forecast" as const,
      label: "Projected book (forecast)",
      values: bookForecast,
    },
  ];

  return (
    <AnalyticsLineChart
      title={t("charts.churnHorizon.title")}
      subtitle={t("charts.churnHorizon.subtitle")}
      points={points}
      loading={loading}
      forecastDividerIndex={forecastStart}
      series={chartSeries}
      emptyMessage={t("charts.churnHorizon.empty")}
      interactive={interactive}
      onPeriodSelect={onPeriodSelect}
    />
  );
}
