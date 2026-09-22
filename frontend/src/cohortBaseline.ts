import { PortfolioAnalytics, ValueHistoryPoint } from "./api";
import i18n from "./i18n";

export function valuesByPeriod(
  rows: ValueHistoryPoint[],
  periods: string[],
  pick: (row: ValueHistoryPoint) => number,
): (number | null)[] {
  const byPeriod = new Map(rows.map((r) => [r.period, pick(r)]));
  return periods.map((p) => byPeriod.get(p) ?? null);
}

export function shareOfBook(cohort: number, book: number, digits = 1): number | null {
  if (!Number.isFinite(cohort) || !Number.isFinite(book) || book <= 0) return null;
  return (cohort / book) * 100;
}

export function formatShareOfBook(cohort: number, book: number, digits = 1): string | null {
  const pct = shareOfBook(cohort, book, digits);
  if (pct == null) return null;
  return i18n.t("business.cohort.shareOfBook", { pct: pct.toFixed(digits) });
}

export function formatDeltaVsBook(
  cohort: number,
  book: number,
  digits = 1,
): string | null {
  const pct = shareOfBook(cohort, book, digits);
  if (pct == null) return null;
  const delta = pct - 100;
  if (Math.abs(delta) < 0.05) return "Same as full book";
  const sign = delta >= 0 ? "+" : "";
  return `${sign}${delta.toFixed(digits)} pts vs book avg mix`;
}

export function latestBookKpis(data: PortfolioAnalytics | null | undefined) {
  return data?.kpis ?? null;
}
