import { useTranslation } from "react-i18next";
import { PortfolioAnalytics } from "../api";
import { formatMoneyIls } from "../formatMoney";
import { formatShareOfBook, shareOfBook } from "../cohortBaseline";
import { formatNumber } from "../localeFormat";

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
  const { t } = useTranslation();
  const share = shareOfBook(cohortValue, bookValue);
  const display =
    format === "money"
      ? formatMoneyIls(cohortValue)
      : format === "pct"
        ? `${cohortValue.toFixed(1)}%`
        : formatNumber(cohortValue);
  const shareLabel =
    share != null
      ? t("business.cohort.shareOfBook", { pct: share.toFixed(1) })
      : t("common.emDash");

  return (
    <div className="cohort-vs-book-stat">
      <span className="cohort-vs-book-stat-label">{label}</span>
      <strong className="cohort-vs-book-stat-value">{display}</strong>
      <span className="cohort-vs-book-stat-share muted small">{shareLabel}</span>
    </div>
  );
}

export default function CohortVsBookBanner({ cohortLabel, cohort, book }: Props) {
  const { t } = useTranslation();
  const ck = cohort.kpis;
  const bk = book.kpis;
  if (!ck || !bk) return null;

  const bookShareLabel = formatShareOfBook(ck.total_book_value, bk.total_book_value);

  return (
    <div className="cohort-vs-book-banner" role="status">
      <div className="cohort-vs-book-banner-head">
        <span className="cohort-vs-book-badge">{t("business.cohort.filteredBadge")}</span>
        <h3 className="cohort-vs-book-title">{cohortLabel}</h3>
        {bookShareLabel && (
          <p className="cohort-vs-book-lead">
            {t("business.cohort.vsBookLead", { share: bookShareLabel })}
          </p>
        )}
      </div>
      <div className="cohort-vs-book-stats">
        <Stat
          label={t("business.vsBookStats.customers")}
          cohortValue={ck.active_customers}
          bookValue={bk.active_customers}
        />
        <Stat
          label={t("business.vsBookStats.totalBookValue")}
          cohortValue={ck.total_book_value}
          bookValue={bk.total_book_value}
          format="money"
        />
        <Stat
          label={t("business.vsBookStats.policyRecords")}
          cohortValue={ck.total_policies}
          bookValue={bk.total_policies}
        />
        <Stat
          label={t("business.vsBookStats.avgCustomerValue")}
          cohortValue={ck.avg_customer_value}
          bookValue={bk.avg_customer_value}
          format="money"
        />
      </div>
    </div>
  );
}
