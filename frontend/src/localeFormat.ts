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

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
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
