import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import {
  BedrockStatus,
  CustomerInsights,
  fetchBedrockStatus,
  fetchCustomerInsights,
} from "../api";
import InsightActionModal from "./InsightActionModal";

type Props = {
  customerId: number;
  churnTier?: string | null;
};

type OpenAction = {
  recommendation: string;
  source: "recommendation" | "experience_note";
};

function insightSubtitle(
  insights: CustomerInsights | null,
  bedrockStatus: BedrockStatus | null,
  loading: boolean,
  t: TFunction,
): string {
  if (loading && !insights) {
    if (bedrockStatus?.configured) {
      return t("customer.insights.loadingBedrock");
    }
    return t("customer.insights.loadingLocal");
  }
  if (!insights) {
    return t("customer.insights.idleHint");
  }
  if (insights.source === "bedrock" || insights.source === "openai_compatible") {
    const model = insights.model_id ? ` (${insights.model_id})` : "";
    return insights.source === "openai_compatible"
      ? t("customer.insights.llmGenerated", { model })
      : t("customer.insights.bedrockGenerated", { model });
  }
  if (insights.bedrock_configured) {
    if (insights.fallback_reason) {
      return t("customer.insights.fallbackReason", { reason: insights.fallback_reason });
    }
    return t("customer.insights.fallbackGeneric");
  }
  return t("customer.insights.localOnly");
}

export default function CustomerInsightsPanel({ customerId, churnTier }: Props) {
  const { t } = useTranslation();
  const [insights, setInsights] = useState<CustomerInsights | null>(null);
  const [bedrockStatus, setBedrockStatus] = useState<BedrockStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [openAction, setOpenAction] = useState<OpenAction | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchBedrockStatus()
      .then((status) => {
        if (!cancelled) setBedrockStatus(status);
      })
      .catch(() => {
        if (!cancelled) setBedrockStatus(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const load = useCallback(
    async (refresh: boolean) => {
      setError(null);
      if (refresh) setRefreshing(true);
      else setLoading(true);
      try {
        setInsights(await fetchCustomerInsights(customerId, { refresh }));
      } catch (e) {
        setError(e instanceof Error ? e.message : t("customer.insights.loadError"));
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
          setError(e instanceof Error ? e.message : t("customer.insights.loadError"));
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
    insights?.primary_focus === "retention"
      ? t("customer.insights.focusChurn")
      : t("customer.insights.focusUpsell");

  const actionMeta = insights?.recommendation_actions ?? [];
  const fromLlm =
    insights?.source === "bedrock" || insights?.source === "openai_compatible";
  const subtitle = insightSubtitle(insights, bedrockStatus, loading, t);

  return (
    <>
      <section className="panel insights-panel">
        <div className="panel-head">
          <div>
            <h2>{t("customer.insights.title")}</h2>
            <p className="muted small insights-subtitle">{subtitle}</p>
          </div>
          <div className="toolbar">
            <button
              type="button"
              className="btn secondary"
              disabled={loading || refreshing}
              onClick={() => load(true)}
            >
              {refreshing ? t("common.loading") : t("customer.insights.refresh")}
            </button>
          </div>
        </div>

        {loading && !insights && (
          <p className="muted">
            {bedrockStatus?.configured ? t("customer.insights.loadingBedrock") : t("customer.insights.loadingLocal")}
          </p>
        )}
        {error && <p className="error">{error}</p>}

        {insights && (
          <>
            <div className="insights-meta">
              <span
                className={
                  fromLlm ? "source-badge source-bedrock" : "source-badge source-local"
                }
              >
                {fromLlm
                  ? insights.source === "openai_compatible"
                    ? t("customer.insights.poweredLlm")
                    : t("customer.insights.poweredBedrock")
                  : t("customer.insights.localAdvisor")}
              </span>
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
                <span className="muted small">
                  {t("customer.insights.churnTier", { tier: churnTier })}
                </span>
              )}
              {fromLlm && insights.model_id && (
                <span
                  className="muted small"
                  title={t("customer.insights.modelIdTitle")}
                >
                  {t("customer.insights.modelId", { id: insights.model_id })}
                </span>
              )}
              {insights.cached && (
                <span className="muted small">{t("customer.insights.cachedCopy")}</span>
              )}
              {insights.generated_at && (
                <span className="muted small">
                  {t("customer.insights.generatedAt", { at: insights.generated_at })}
                </span>
              )}
            </div>

            <p className="insights-summary">{insights.summary}</p>

            <h2 className="insights-subhead">{t("customer.insights.recommendedActions")}</h2>
            <ul className="insights-list">
              {insights.recommendations.map((item, idx) => {
                const meta = actionMeta[idx];
                const actionable = meta?.actionable ?? false;
                return (
                  <li key={item}>
                    {actionable ? (
                      <button
                        type="button"
                        className="insight-action-link"
                        onClick={() =>
                          setOpenAction({ recommendation: item, source: "recommendation" })
                        }
                      >
                        {item}
                      </button>
                    ) : (
                      item
                    )}
                  </li>
                );
              })}
            </ul>

            {insights.experience_note && (
              <p className="insights-note">
                <span className="label">{t("customer.insights.bestNextTouch")}</span>
                {insights.experience_note_actionable ? (
                  <button
                    type="button"
                    className="insight-action-link inline"
                    onClick={() =>
                      setOpenAction({
                        recommendation: insights.experience_note!,
                        source: "experience_note",
                      })
                    }
                  >
                    {insights.experience_note}
                  </button>
                ) : (
                  insights.experience_note
                )}
              </p>
            )}

            {!fromLlm && insights.fallback_reason && (
              <p className="error small insights-hint">
                {t("customer.insights.bedrockError", { reason: insights.fallback_reason })}
              </p>
            )}

            {!fromLlm && !insights.bedrock_configured && (
              <p className="muted small insights-hint">
                {t("customer.insights.envHint")}
              </p>
            )}

            {!fromLlm && insights.bedrock_configured && !insights.fallback_reason && (
              <p className="muted small insights-hint">
                {t("customer.insights.regionHint")}
              </p>
            )}
          </>
        )}
      </section>

      {openAction && (
        <InsightActionModal
          customerId={customerId}
          recommendation={openAction.recommendation}
          source={openAction.source}
          onClose={() => setOpenAction(null)}
        />
      )}
    </>
  );
}
