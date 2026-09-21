type Props = {
  probability?: number | null;
  tier?: string | null;
};

export default function ChurnBadge({ probability, tier }: Props) {
  if (tier == null && probability == null) {
    return <span className="muted">Not scored</span>;
  }

  const level = (tier ?? "LOW").toUpperCase();
  const pct =
    probability != null ? `${Math.round(probability * 100)}%` : "—";
  const className = `churn-badge churn-${level.toLowerCase()}`;

  return (
    <span className={className} title={`Churn likelihood ${pct}`}>
      {level} · {pct}
    </span>
  );
}
