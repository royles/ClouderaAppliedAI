import { PortfolioAnalytics } from "../api";
import { formatMoneyIls } from "../formatMoney";
import { formatShareOfBook, shareOfBook } from "../cohortBaseline";

type Props = {
  cohortLabel: string;
  cohort: PortfolioAnalytics;
  book: PortfolioAnalytics;
};

function Stat({
  label,
  cohortValue,
  bookValue,
  format = "number",
}: {
  label: string;
  cohortValue: number;
  bookValue: number;
  format?: "number" | "money" | "pct";
}) {
  const share = shareOfBook(cohortValue, bookValue);
  const display =
    format === "money"
      ? formatMoneyIls(cohortValue)
      : format === "pct"
        ? `${cohortValue.toFixed(1)}%`
        : cohortValue.toLocaleString();
  const shareLabel =
    share != null ? `${share.toFixed(1)}% of book` : "—";

  return (
    <div className="cohort-vs-book-stat">
      <span className="cohort-vs-book-stat-label">{label}</span>
      <strong className="cohort-vs-book-stat-value">{display}</strong>
      <span className="cohort-vs-book-stat-share muted small">{shareLabel}</span>
    </div>
  );
}

export default function CohortVsBookBanner({ cohortLabel, cohort, book }: Props) {
  const ck = cohort.kpis;
  const bk = book.kpis;
  if (!ck || !bk) return null;

  const bookShareLabel = formatShareOfBook(ck.total_book_value, bk.total_book_value);

  return (
    <div className="cohort-vs-book-banner" role="status">
      <div className="cohort-vs-book-banner-head">
        <span className="cohort-vs-book-badge">Filtered cohort</span>
        <h3 className="cohort-vs-book-title">{cohortLabel}</h3>
        {bookShareLabel && (
          <p className="cohort-vs-book-lead">
            This slice is <strong>{bookShareLabel}</strong> by total customer value — dashed
            gray lines on the charts show the full active book for comparison.
          </p>
        )}
      </div>
      <div className="cohort-vs-book-stats">
        <Stat label="Customers" cohortValue={ck.active_customers} bookValue={bk.active_customers} />
        <Stat
          label="Total book value"
          cohortValue={ck.total_book_value}
          bookValue={bk.total_book_value}
          format="money"
        />
        <Stat
          label="Policy records"
          cohortValue={ck.total_policies}
          bookValue={bk.total_policies}
        />
        <Stat
          label="Avg customer value"
          cohortValue={ck.avg_customer_value}
          bookValue={bk.avg_customer_value}
          format="money"
        />
      </div>
    </div>
  );
}
