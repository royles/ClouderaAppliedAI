export function formatPeriodLabel(period: string) {
  if (period.length >= 7) {
    const [y, m] = period.split("-");
    const month = new Date(Number(y), Number(m) - 1, 1).toLocaleString("en-GB", {
      month: "short",
    });
    return `${month} ${y?.slice(2)}`;
  }
  return period;
}

export function formatAxisMoney(n: number) {
  if (n >= 1_000_000) return `₪${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `₪${(n / 1_000).toFixed(0)}K`;
  return `₪${n.toFixed(0)}`;
}

export function formatTooltipMoney(n: number) {
  return new Intl.NumberFormat("en-IL", {
    style: "currency",
    currency: "ILS",
    maximumFractionDigits: 0,
  }).format(n);
}

export function formatAxisPct(n: number) {
  return `${n.toFixed(1)}%`;
}

export function linePath(
  values: (number | null)[],
  width: number,
  height: number,
  padX: number,
  padY: number,
  minY: number,
  maxY: number,
): string {
  const span = maxY - minY || 1;
  const stepX = values.length > 1 ? (width - padX * 2) / (values.length - 1) : 0;
  let d = "";
  values.forEach((v, i) => {
    if (v == null) return;
    const x = padX + i * stepX;
    const y = padY + (height - padY * 2) * (1 - (v - minY) / span);
    d += `${d ? " L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
  });
  return d;
}

export type ChartSeries = {
  id: string;
  values: (number | null)[];
  className: string;
  label: string;
  dashed?: boolean;
};
