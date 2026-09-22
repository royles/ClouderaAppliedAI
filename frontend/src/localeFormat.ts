import i18n from "./i18n";

export function intlLocale(): string {
  return i18n.language?.startsWith("he") ? "he-IL" : "en-IL";
}

export function formatMoneyIls(n?: number | null): string {
  if (n == null || Number.isNaN(n)) return "—";
  return new Intl.NumberFormat(intlLocale(), {
    style: "currency",
    currency: "ILS",
    maximumFractionDigits: 0,
  }).format(n);
}

export function formatNumber(n: number): string {
  return n.toLocaleString(intlLocale());
}

export function formatDateTime(iso: string | null | undefined, empty = "—"): string {
  if (!iso) return empty;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 16).replace("T", " ");
  return d.toLocaleString(intlLocale(), {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function formatMonthYear(yearMonth: string): string {
  const [y, m] = yearMonth.split("-");
  if (!y || !m) return yearMonth;
  return new Date(Number(y), Number(m) - 1, 1).toLocaleString(intlLocale(), {
    month: "short",
    year: "numeric",
  });
}

export function formatBytes(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)} GB`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} MB`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)} KB`;
  return `${n} B`;
}

/** Format a unitless rate in 0–1 range as a percentage string. */
export function formatRatePercent(
  rate: number | null | undefined,
  digits = 1,
  empty = "—",
): string {
  if (rate == null || Number.isNaN(rate)) return empty;
  return `${(rate * 100).toFixed(digits)}%`;
}

export function qualityStatusClass(status: string): string {
  if (status === "critical") return "quality-badge quality-critical";
  if (status === "warn") return "quality-badge quality-warn";
  return "quality-badge quality-ok";
}
