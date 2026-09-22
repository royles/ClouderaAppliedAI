import { useTranslation } from "react-i18next";

type Props = {
  average: number | null | undefined;
  reviewCount?: number | null;
  className?: string;
  compact?: boolean;
};

function starFill(average: number, starIndex: number): "full" | "half" | "empty" {
  const avg = Math.min(5, Math.max(0, average));
  if (avg >= starIndex) return "full";
  if (avg >= starIndex - 0.5) return "half";
  return "empty";
}

export default function ReviewStarRating({
  average,
  reviewCount,
  className = "",
  compact = false,
}: Props) {
  const { t } = useTranslation();

  if (average == null || Number.isNaN(average)) {
    return (
      <p className={`review-star-rating review-star-rating-empty muted small${className ? ` ${className}` : ""}`}>
        {t("customer.card.reviewsNone")}
      </p>
    );
  }

  const avgLabel = average.toFixed(1);
  const count = reviewCount ?? 0;
  const ariaLabel =
    count > 0
      ? t("customer.card.reviewsStarsA11y", { avg: avgLabel, count })
      : t("customer.card.reviewsStarsA11yNoCount", { avg: avgLabel });

  return (
    <div
      className={`review-star-rating${compact ? " review-star-rating-compact" : ""}${className ? ` ${className}` : ""}`}
      role="img"
      aria-label={ariaLabel}
    >
      <span className="review-star-rating-stars" aria-hidden>
        {[1, 2, 3, 4, 5].map((i) => (
          <span
            key={i}
            className={`review-star-rating-star review-star-rating-star-${starFill(average, i)}`}
          >
            ★
          </span>
        ))}
      </span>
      {!compact && (
        <span className="review-star-rating-meta muted small" aria-hidden>
          {count > 0
            ? t("customer.card.reviewsAvg", { avg: avgLabel, count })
            : t("customer.card.reviewsAvgShort", { avg: avgLabel })}
        </span>
      )}
    </div>
  );
}
