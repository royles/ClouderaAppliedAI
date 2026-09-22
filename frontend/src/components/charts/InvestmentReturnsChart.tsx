import { useTranslation } from "react-i18next";
import { InvestmentReturnPoint } from "../../api";
import { valuesByPeriod } from "../../cohortBaseline";
import { ChartPeriodSelection } from "../../chartFilter";
import AnalyticsLineBarChart from "./AnalyticsLineBarChart";
import AnalyticsLineChart, { moneyTooltip, pctTooltip } from "./AnalyticsLineChart";

type Props = {
  series: InvestmentReturnPoint[];
  baselineSeries?: InvestmentReturnPoint[];
  loading?: boolean;
  interactive?: boolean;
  onPeriodSelect?: (selection: ChartPeriodSelection) => void;
};

export default function InvestmentReturnsChart({
  series,
  baselineSeries,
  loading,
  interactive,
  onPeriodSelect,
}: Props) {
  const { t } = useTranslation();
  const periods = series.map((p) => p.period);
  const hasReturns = series.some(
    (p) => p.cumulative_return_pct != null || p.period_return_pct != null,
  );
  const comparing = Boolean(baselineSeries?.length);

  const baselineCum =
    comparing && baselineSeries
      ? valuesByPeriod(
          baselineSeries.map((p) => ({
            period: p.period,
            total_value: p.cumulative_return_pct ?? 0,
            investment_value: 0,
            coverage_value: 0,
          })),
          periods,
          (p) => p.total_value,
        )
      : null;

  if (!hasReturns) {
    const balanceLabel = comparing
      ? t("charts.investmentReturns.legendCohortBalance")
      : t("charts.investmentReturns.legendBalance");
    const points = series.map((p) => ({
      period: p.period,
      kind: "actual" as const,
      tooltipLines: [moneyTooltip(balanceLabel, p.investment_balance)],
    }));
    return (
      <AnalyticsLineChart
        title={t("charts.investmentReturns.title")}
        subtitle={t("charts.investmentReturns.subtitleFallback")}
        points={points}
        loading={loading}
        valueFormat="money"
        series={[
          {
            id: "balance",
            visualKey: "return-balance",
            label: balanceLabel,
            values: series.map((p) => p.investment_balance),
            valueFormat: "money",
          },
        ]}
        emptyMessage={t("charts.investmentReturns.empty")}
        interactive={interactive}
        onPeriodSelect={onPeriodSelect}
      />
    );
  }

  const points = series.map((p) => {
    const lines = [
      pctTooltip(t("charts.investmentReturns.legendCumulative"), p.cumulative_return_pct),
      pctTooltip(t("charts.investmentReturns.legendPeriod"), p.period_return_pct),
      moneyTooltip(t("charts.investmentReturns.legendBalance"), p.investment_balance),
    ];
    return {
      period: p.period,
      kind: "actual" as const,
      tooltipLines: lines,
    };
  });

  return (
    <AnalyticsLineBarChart
      title={t("charts.investmentReturns.title")}
      subtitle={t("charts.investmentReturns.subtitle")}
      points={points}
      loading={loading}
      lineFormat="percent"
      barFormat="percent"
      allowSparseBars
      interactive={interactive}
      onPeriodSelect={onPeriodSelect}
      line={{
        id: "cum",
        visualKey: "return-cumulative",
        label: t("charts.investmentReturns.legendCumulative"),
        values: series.map((p) => p.cumulative_return_pct ?? null),
      }}
      bars={{
        id: "period",
        visualKey: "return-period",
        label: t("charts.investmentReturns.legendPeriod"),
        values: series.map((p) => p.period_return_pct ?? null),
      }}
      referenceLine={
        baselineCum
          ? {
              id: "baseline-cum",
              visualKey: "return-baseline-balance",
              label: t("charts.investmentReturns.legendBookCumulative"),
              values: baselineCum,
            }
          : undefined
      }
      emptyMessage={t("charts.investmentReturns.empty")}
    />
  );
}
