import { ValueHistoryPoint } from "./api";

export type CustomerChurnInput = {
  probability: number;
  tier?: string | null;
};

export type ExtendedValuePoint = ValueHistoryPoint & {
  kind: "actual" | "forecast";
  forecast_step?: number;
  is_predicted_lapse?: boolean;
};

/** Median months to lapse for a constant-hazard 12-month churn probability. */
export function predictMonthsToChurn(probability: number): number {
  const p = Math.min(Math.max(probability, 0.01), 0.99);
  const monthlyHazard = -Math.log(1 - p) / 12;
  const medianMonths = Math.log(2) / monthlyHazard;
  return Math.max(1, Math.min(24, Math.round(medianMonths)));
}

/** Advance YYYY-MM-DD or YYYY-MM snapshot period by whole months (month-end dates). */
export function addMonthsToPeriod(period: string, months: number): string {
  const y = Number(period.slice(0, 4));
  const m = Number(period.slice(5, 7));
  if (!Number.isFinite(y) || !Number.isFinite(m)) return period;
  let month = m + months;
  let year = y;
  while (month > 12) {
    month -= 12;
    year += 1;
  }
  while (month < 1) {
    month += 12;
    year -= 1;
  }
  const lastDay = new Date(year, month, 0).getDate();
  return `${year.toString().padStart(4, "0")}-${month.toString().padStart(2, "0")}-${lastDay
    .toString()
    .padStart(2, "0")}`;
}

export function buildCustomerValueWithChurnForecast(
  history: ValueHistoryPoint[],
  churn: CustomerChurnInput | null | undefined,
): {
  points: ExtendedValuePoint[];
  monthsToChurn: number;
  predictedLapsePeriod: string | null;
  valueAtRisk: number;
  lastActualValue: number;
} | null {
  if (history.length === 0) return null;

  const last = history[history.length - 1];
  const lastValue = last.total_value;
  const probability = churn?.probability ?? 0;
  const monthsToChurn =
    churn && probability > 0 ? predictMonthsToChurn(probability) : 0;

  const actualPoints: ExtendedValuePoint[] = history.map((p) => ({
    ...p,
    kind: "actual" as const,
  }));

  if (monthsToChurn <= 0 || lastValue <= 0) {
    return {
      points: actualPoints,
      monthsToChurn: 0,
      predictedLapsePeriod: null,
      valueAtRisk: lastValue * probability,
      lastActualValue: lastValue,
    };
  }

  const forecastPoints: ExtendedValuePoint[] = [];
  for (let step = 1; step <= monthsToChurn; step += 1) {
    const period = addMonthsToPeriod(last.period, step);
    const remaining = Math.max(0, 1 - step / monthsToChurn);
    const totalValue = Math.round(lastValue * remaining * 100) / 100;
    forecastPoints.push({
      period,
      investment_value: 0,
      coverage_value: 0,
      total_value: totalValue,
      kind: "forecast",
      forecast_step: step,
      is_predicted_lapse: step === monthsToChurn,
    });
  }

  return {
    points: [...actualPoints, ...forecastPoints],
    monthsToChurn,
    predictedLapsePeriod: forecastPoints[forecastPoints.length - 1]?.period ?? null,
    valueAtRisk: Math.round(lastValue * probability * 100) / 100,
    lastActualValue: lastValue,
  };
}
