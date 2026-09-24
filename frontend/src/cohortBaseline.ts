import { ValueHistoryPoint } from "./api";
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
