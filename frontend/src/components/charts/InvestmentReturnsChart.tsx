import { InvestmentReturnPoint } from "../../api";
import { valuesByPeriod } from "../../cohortBaseline";
import { ChartPeriodSelection } from "../../chartFilter";
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
  const periods = series.map((p) => p.period);
  const hasReturns = series.some((p) => p.period_return_pct != null);
  const comparing = Boolean(baselineSeries?.length);

  const baselineBalances =
    comparing && baselineSeries
      ? valuesByPeriod(
          baselineSeries.map((p) => ({
            period: p.period,
            total_value: p.investment_balance,
            investment_value: 0,
            coverage_value: 0,
          })),
          periods,
          (p) => p.total_value,
        )
      : null;

  const baselineByPeriod = baselineSeries
    ? new Map(baselineSeries.map((p) => [p.period, p.investment_balance]))
    : null;

  const balanceLabel = comparing ? "Cohort balance" : "Investment balance";

  const points = series.map((p) => {
    const lines = [moneyTooltip(balanceLabel, p.investment_balance)];
    if (hasReturns) {
      lines.push(
        pctTooltip("Cumulative return", p.cumulative_return_pct),
        pctTooltip("Period return", p.period_return_pct),
      );
    }
    const ref = baselineByPeriod?.get(p.period);
    if (ref != null) {
      lines.push(moneyTooltip("Full book balance (reference)", ref));
    }
    return {
      period: p.period,
      kind: "actual" as const,
      tooltipLines: lines,
    };
  });

  const chartSeries = [
    ...(baselineBalances
      ? [
          {
            id: "baseline-balance",
            visualKey: "return-baseline-balance" as const,
            label: "Full book balance (reference)",
            values: baselineBalances,
            axis: "primary" as const,
            valueFormat: "money" as const,
          },
        ]
      : []),
    ...(hasReturns
      ? [
          {
            id: "balance",
            visualKey: "return-balance" as const,
            label: balanceLabel,
            values: series.map((p) => p.investment_balance),
            axis: "primary" as const,
            valueFormat: "money" as const,
          },
          {
            id: "cum",
            visualKey: "return-cumulative" as const,
            label: "Cumulative return %",
            values: series.map((p) => p.cumulative_return_pct ?? null),
            axis: "secondary" as const,
            valueFormat: "percent" as const,
          },
          {
            id: "period",
            visualKey: "return-period" as const,
            label: "Period return %",
            values: series.map((p) => p.period_return_pct ?? null),
            axis: "secondary" as const,
            valueFormat: "percent" as const,
          },
        ]
      : [
          {
            id: "balance",
            visualKey: "return-balance" as const,
            label: balanceLabel,
            values: series.map((p) => p.investment_balance),
            axis: "primary" as const,
            valueFormat: "money" as const,
          },
        ]),
  ];

  return (
    <AnalyticsLineChart
      title="Investment returns"
      subtitle={
        hasReturns
          ? comparing
            ? "Balance on the left; return % on the right. Dashed gray = full book balance."
            : "Investment balance (left) and month-on-month / cumulative return % (right)."
          : "Investment track balances over time."
      }
      points={points}
      loading={loading}
      valueFormat="money"
      series={chartSeries}
      emptyMessage="No investment history for this cohort."
      interactive={interactive}
      onPeriodSelect={onPeriodSelect}
    />
  );
}
