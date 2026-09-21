import { InvestmentReturnPoint } from "../../api";
import AnalyticsLineChart, { moneyTooltip, pctTooltip } from "./AnalyticsLineChart";

type Props = {
  series: InvestmentReturnPoint[];
  loading?: boolean;
};

export default function InvestmentReturnsChart({ series, loading }: Props) {
  const points = series.map((p) => ({
    period: p.period,
    kind: "actual" as const,
    tooltipLines: [
      moneyTooltip("Balance", p.investment_balance),
      pctTooltip("Period return", p.period_return_pct),
      pctTooltip("Cumulative return", p.cumulative_return_pct),
    ],
  }));

  const hasReturns = series.some((p) => p.period_return_pct != null);

  return (
    <AnalyticsLineChart
      title="Investment returns"
      subtitle="Accumulation balance and month-on-month return on investment tracks."
      points={points}
      loading={loading}
      valueFormat={hasReturns ? "percent" : "money"}
      series={
        hasReturns
          ? [
              {
                id: "cum",
                visualKey: "return-cumulative",
                label: "Cumulative return %",
                values: series.map((p) => p.cumulative_return_pct ?? null),
              },
              {
                id: "period",
                visualKey: "return-period",
                label: "Period return %",
                values: series.map((p) => p.period_return_pct ?? null),
              },
            ]
          : [
              {
                id: "balance",
                visualKey: "return-balance",
                label: "Investment balance",
                values: series.map((p) => p.investment_balance),
              },
            ]
      }
      emptyMessage="No investment history for this cohort."
    />
  );
}
