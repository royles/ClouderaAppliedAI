import { ValueHistoryPoint } from "./api";

export type CustomerChurnInput = {
  probability: number;
  tier?: string | null;
};

export type ChurnTier = "HIGH" | "MEDIUM" | "LOW";

export type ForecastScenario = "high_lapse" | "medium_trend" | "low_trend" | "none";

export type ExtendedValuePoint = ValueHistoryPoint & {
  kind: "actual" | "forecast";
  forecast_step?: number;
  is_predicted_lapse?: boolean;
};

const HIGH_LAPSE_MONTHS = 3;
const TREND_FORECAST_MONTHS = 12;

export function normalizeChurnTier(tier?: string | null): ChurnTier | null {
  const key = (tier ?? "").trim().toUpperCase();
  if (key === "HIGH" || key === "MEDIUM" || key === "LOW") return key;
  return null;
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

function avgMonthlyDeltas(
  history: ValueHistoryPoint[],
  recentOnly: boolean,
): { total: number; investment: number; coverage: number } {
  if (history.length < 2) {
    return { total: 0, investment: 0, coverage: 0 };
  }
  const startIdx = recentOnly ? Math.max(1, history.length - 3) : 1;
  let sumT = 0;
  let sumI = 0;
  let sumC = 0;
  let n = 0;
  for (let i = startIdx; i < history.length; i += 1) {
    sumT += history[i].total_value - history[i - 1].total_value;
    sumI += history[i].investment_value - history[i - 1].investment_value;
    sumC += history[i].coverage_value - history[i - 1].coverage_value;
    n += 1;
  }
  if (n === 0) return { total: 0, investment: 0, coverage: 0 };
  return { total: sumT / n, investment: sumI / n, coverage: sumC / n };
}

function buildLapseForecast(
  last: ValueHistoryPoint,
  monthsToChurn: number,
): ExtendedValuePoint[] {
  const lastValue = last.total_value;
  if (monthsToChurn <= 0 || lastValue <= 0) return [];

  const rows: ExtendedValuePoint[] = [];
  for (let step = 1; step <= monthsToChurn; step += 1) {
    const period = addMonthsToPeriod(last.period, step);
    const remaining = Math.max(0, 1 - step / monthsToChurn);
    const totalValue = Math.round(lastValue * remaining * 100) / 100;
    rows.push({
      period,
      investment_value: 0,
      coverage_value: 0,
      total_value: totalValue,
      kind: "forecast",
      forecast_step: step,
      is_predicted_lapse: step === monthsToChurn,
    });
  }
  return rows;
}

function buildHistoryTrendForecast(
  history: ValueHistoryPoint[],
  last: ValueHistoryPoint,
  recentOnly: boolean,
  horizonMonths: number,
): ExtendedValuePoint[] {
  const deltas = avgMonthlyDeltas(history, recentOnly);
  let total = last.total_value;
  let investment = last.investment_value;
  let coverage = last.coverage_value;

  const rows: ExtendedValuePoint[] = [];
  for (let step = 1; step <= horizonMonths; step += 1) {
    total = Math.max(0, total + deltas.total);
    investment = Math.max(0, investment + deltas.investment);
    coverage = Math.max(0, coverage + deltas.coverage);
    rows.push({
      period: addMonthsToPeriod(last.period, step),
      investment_value: Math.round(investment * 100) / 100,
      coverage_value: Math.round(coverage * 100) / 100,
      total_value: Math.round(total * 100) / 100,
      kind: "forecast",
      forecast_step: step,
      is_predicted_lapse: false,
    });
  }
  return rows;
}

export function buildCustomerValueWithChurnForecast(
  history: ValueHistoryPoint[],
  churn: CustomerChurnInput | null | undefined,
): {
  points: ExtendedValuePoint[];
  scenario: ForecastScenario;
  monthsToChurn: number;
  forecastHorizonMonths: number;
  predictedLapsePeriod: string | null;
  valueAtRisk: number;
  lastActualValue: number;
} | null {
  if (history.length === 0) return null;

  const last = history[history.length - 1];
  const lastValue = last.total_value;
  const probability = churn?.probability ?? 0;
  const tier = normalizeChurnTier(churn?.tier);

  const actualPoints: ExtendedValuePoint[] = history.map((p) => ({
    ...p,
    kind: "actual" as const,
  }));

  if (!churn || !tier) {
    return {
      points: actualPoints,
      scenario: "none",
      monthsToChurn: 0,
      forecastHorizonMonths: 0,
      predictedLapsePeriod: null,
      valueAtRisk: lastValue * probability,
      lastActualValue: lastValue,
    };
  }

  let forecastPoints: ExtendedValuePoint[] = [];
  let scenario: ForecastScenario = "none";
  let monthsToChurn = 0;
  let forecastHorizonMonths = 0;

  if (tier === "HIGH") {
    scenario = "high_lapse";
    monthsToChurn = HIGH_LAPSE_MONTHS;
    forecastHorizonMonths = HIGH_LAPSE_MONTHS;
    forecastPoints = buildLapseForecast(last, HIGH_LAPSE_MONTHS);
  } else if (tier === "MEDIUM") {
    scenario = "medium_trend";
    forecastHorizonMonths = TREND_FORECAST_MONTHS;
    forecastPoints = buildHistoryTrendForecast(
      history,
      last,
      true,
      TREND_FORECAST_MONTHS,
    );
  } else {
    scenario = "low_trend";
    forecastHorizonMonths = TREND_FORECAST_MONTHS;
    forecastPoints = buildHistoryTrendForecast(
      history,
      last,
      false,
      TREND_FORECAST_MONTHS,
    );
  }

  return {
    points: [...actualPoints, ...forecastPoints],
    scenario,
    monthsToChurn,
    forecastHorizonMonths,
    predictedLapsePeriod:
      forecastPoints.find((p) => p.is_predicted_lapse)?.period ??
      forecastPoints[forecastPoints.length - 1]?.period ??
      null,
    valueAtRisk: Math.round(lastValue * probability * 100) / 100,
    lastActualValue: lastValue,
  };
}
