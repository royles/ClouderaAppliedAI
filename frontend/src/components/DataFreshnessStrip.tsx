import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { DataFreshness, fetchDataFreshness } from "../api";
import { formatDateTime } from "../localeFormat";

function formatTs(iso: string | null | undefined): string {
  return formatDateTime(iso);
}

export default function DataFreshnessStrip() {
  const { t } = useTranslation();
  const [data, setData] = useState<DataFreshness | null>(null);

  useEffect(() => {
    let cancelled = false;
    void fetchDataFreshness()
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch(() => {
        if (!cancelled) setData(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!data) return null;

  return (
    <div className="data-freshness-strip" role="status" aria-label={t("app.dataFreshness.label")}>
      <span className="data-freshness-label">{t("app.dataFreshness.label")}</span>
      <span className="data-freshness-item">
        {t("app.dataFreshness.warehouse")}{" "}
        <strong>{formatTs(data.warehouse_loaded_at)}</strong>
      </span>
      <span className="data-freshness-item">
        {t("app.dataFreshness.metricsCache")}{" "}
        <strong>{formatTs(data.customer_metrics_at)}</strong>
      </span>
      <span className="data-freshness-item">
        {t("app.dataFreshness.portfolioCache")}{" "}
        <strong>{formatTs(data.portfolio_cache_at)}</strong>
      </span>
      <span className="data-freshness-item">
        {t("app.dataFreshness.churnScores")}{" "}
        <strong>
          {data.churn_scored_at
            ? t("app.dataFreshness.churnScored", {
                date: formatTs(data.churn_scored_at),
                count: data.churn_customer_count.toLocaleString(),
              })
            : t("customer.churn.notScored")}
        </strong>
      </span>
    </div>
  );
}
