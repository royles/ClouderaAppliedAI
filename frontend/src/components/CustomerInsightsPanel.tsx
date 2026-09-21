import { useCallback, useEffect, useState } from "react";
import { CustomerInsights, fetchCustomerInsights } from "../api";

type Props = {
  customerId: number;
  churnTier?: string | null;
};

export default function CustomerInsightsPanel({ customerId, churnTier }: Props) {
  const [insights, setInsights] = useState<CustomerInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(
    async (refresh: boolean) => {
      setError(null);
      if (refresh) setRefreshing(true);
      else setLoading(true);
      try {
        setInsights(await fetchCustomerInsights(customerId, { refresh }));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load insights");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [customerId],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const data = await fetchCustomerInsights(customerId);
        if (!cancelled) setInsights(data);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Could not load insights");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [customerId]);

  const focusLabel =
    insights?.primary_focus === "retention" ? "Retention focus" : "Upsell focus";

  return (
    <section className="panel insights-panel">
      <div className="panel-head">
        <div>
          <h2>AI customer insights</h2>
          <p className="muted small">
            Concise guidance to improve this customer&apos;s experience — powered by
            Amazon Bedrock when configured.
          </p>
        </div>
        <div className="toolbar">
          <button
            type="button"
            className="btn secondary"
            disabled={loading || refreshing}
            onClick={() => load(true)}
          >
            {refreshing ? "Refreshing…" : "Refresh insights"}
          </button>
        </div>
      </div>

      {loading && !insights && <p className="muted">Generating insights…</p>}
      {error && <p className="error">{error}</p>}

      {insights && (
        <>
          <div className="insights-meta">
            <span
              className={
                insights.primary_focus === "retention"
                  ? "focus-badge retention"
                  : "focus-badge upsell"
              }
            >
              {focusLabel}
            </span>
            {churnTier && (
              <span className="muted small">Churn tier: {churnTier}</span>
            )}
            <span className="muted small">
              Source: {insights.source === "bedrock" ? "Amazon Bedrock" : "Local advisor"}
              {insights.cached ? " · cached" : ""}
            </span>
          </div>

          <p className="insights-summary">{insights.summary}</p>

          <h3 className="insights-subhead">Recommended actions</h3>
          <ul className="insights-list">
            {insights.recommendations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          {insights.experience_note && (
            <p className="insights-note">
              <span className="label">Best next touch</span>
              {insights.experience_note}
            </p>
          )}

          {!insights.bedrock_configured && (
            <p className="muted small insights-hint">
              Bedrock is not configured in this environment — showing rule-based guidance.
              Set AWS credentials and model env vars to enable generative insights.
            </p>
          )}
        </>
      )}
    </section>
  );
}
