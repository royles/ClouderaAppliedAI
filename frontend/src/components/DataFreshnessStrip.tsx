import { useEffect, useState } from "react";
import { DataFreshness, fetchDataFreshness } from "../api";

function formatTs(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 16).replace("T", " ");
  return d.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function DataFreshnessStrip() {
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
    <div className="data-freshness-strip" role="status" aria-label="Data freshness">
      <span className="data-freshness-label">Data freshness</span>
      <span className="data-freshness-item">
        Warehouse <strong>{formatTs(data.warehouse_loaded_at)}</strong>
      </span>
      <span className="data-freshness-item">
        Metrics cache <strong>{formatTs(data.customer_metrics_at)}</strong>
      </span>
      <span className="data-freshness-item">
        Portfolio cache <strong>{formatTs(data.portfolio_cache_at)}</strong>
      </span>
      <span className="data-freshness-item">
        Churn scores{" "}
        <strong>
          {data.churn_scored_at
            ? `${formatTs(data.churn_scored_at)} (${data.churn_customer_count.toLocaleString()} customers)`
            : "Not scored"}
        </strong>
      </span>
    </div>
  );
}
