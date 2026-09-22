import { useTranslation } from "react-i18next";

type Props = {
  probability?: number | null;
  tier?: string | null;
};

export default function ChurnBadge({ probability, tier }: Props) {
  const { t } = useTranslation();
  if (tier == null && probability == null) {
    return <span className="muted">{t("customer.churn.notScored")}</span>;
  }

  const level = (tier ?? "LOW").toUpperCase();
  const tierLabel = t(`customer.churn.tier.${level}`, { defaultValue: level });
  const pct =
    probability != null ? `${Math.round(probability * 100)}%` : t("common.emDash");
  const className = `churn-badge churn-${level.toLowerCase()}`;

  const label = t("customer.churn.badgeA11y", { tier: tierLabel, pct });

  return (
    <span
      className={className}
      title={t("customer.churn.likelihoodTitle", { pct })}
      aria-label={label}
    >
      {tierLabel} · {pct}
    </span>
  );
}
