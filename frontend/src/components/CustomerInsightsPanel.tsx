import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import {
  BedrockStatus,
  CustomerInsights,
  fetchBedrockStatus,
  fetchCustomerInsights,
  fetchCustomerInsightsStream,
} from "../api";
import { partialJsonStringField } from "../jsonStreamPreview";
import InsightActionModal from "./InsightActionModal";
import {
  isLlmGeneratedSource,
  llmBrandName,
  LlmProviderKind,
  resolveLlmProvider,
} from "../llmBrand";

type Props = {
  customerId: number;
  churnTier?: string | null;
};

type OpenAction = {
  recommendation: string;
  source: "recommendation" | "experience_note";
};

function proseParagraphs(text: string | undefined | null): string[] {
  if (!text?.trim()) return [];
  return text.split(/\n\n+/).map((p) => p.trim()).filter(Boolean);
}

function brandForSource(
  t: TFunction,
  source: string | null | undefined,
  fallbackProvider: LlmProviderKind,
): string {
  if (source === "openai_compatible") return llmBrandName(t, "openai_compatible");
  if (source === "bedrock") return llmBrandName(t, "bedrock");
  return llmBrandName(t, fallbackProvider);
}

function localOnlyHint(t: TFunction, provider: LlmProviderKind): string {
  if (provider === "openai_compatible") return t("customer.insights.localOnlyPrivateAi");
  if (provider === "bedrock") return t("customer.insights.localOnlyBedrock");
  return t("customer.insights.localOnlyGeneric");
}

function envHint(t: TFunction, provider: LlmProviderKind, brand: string): string {
  if (provider === "openai_compatible") {
    return t("customer.insights.envHintPrivateAi", { brand });
  }
  return t("customer.insights.envHintBedrock", { brand });
}

function insightSubtitle(
  insights: CustomerInsights | null,
  bedrockStatus: BedrockStatus | null,
  loading: boolean,
  t: TFunction,
): string {
  const provider = resolveLlmProvider(bedrockStatus);
  const brand = llmBrandName(t, provider);

  if (loading && !insights) {
    if (bedrockStatus?.configured) {
      return t("customer.insights.loadingLlm", { brand });
    }
    return t("customer.insights.loadingLocal");
  }
  if (!insights) {
    return t("customer.insights.idleHint");
  }
  if (isLlmGeneratedSource(insights.source)) {
    const model = insights.model_id ? ` (${insights.model_id})` : "";
    const insightBrand = brandForSource(t, insights.source, provider);
    return t("customer.insights.generatedBy", { brand: insightBrand, model });
  }
  if (insights.bedrock_configured) {
    if (insights.fallback_reason) {
      return t("customer.insights.fallbackReason", {
        brand,
        reason: insights.fallback_reason,
      });
    }
    return t("customer.insights.fallbackGeneric", { brand });
  }
  return localOnlyHint(t, provider);
}

export default function CustomerInsightsPanel({ customerId, churnTier }: Props) {
  const { t } = useTranslation();
  const [insights, setInsights] = useState<CustomerInsights | null>(null);
  const [bedrockStatus, setBedrockStatus] = useState<BedrockStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [openAction, setOpenAction] = useState<OpenAction | null>(null);
  const [streamPreview, setStreamPreview] = useState("");

  const loadInsights = useCallback(
    async (refresh: boolean, configured: boolean) => {
      setError(null);
      setStreamPreview("");
      if (refresh) setRefreshing(true);
      else setLoading(true);

      const finish = () => {
        setLoading(false);
        setRefreshing(false);
        setStreamPreview("");
      };

      try {
        if (configured) {
          await fetchCustomerInsightsStream(
            customerId,
            {
              onDelta: (_piece, buffer) => {
                const preview =
                  partialJsonStringField(buffer, "guidance") ||
                  partialJsonStringField(buffer, "summary") ||
                  partialJsonStringField(buffer, "preamble") ||
                  t("customer.insights.streamPreview");
                setStreamPreview(preview);
              },
              onDone: (data) => setInsights(data),
            },
            { refresh },
          );
        } else {
          setInsights(await fetchCustomerInsights(customerId, { refresh }));
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : t("customer.insights.loadError"));
      } finally {
        finish();
      }
    },
    [customerId, t],
  );

  const load = useCallback(
    (refresh: boolean) => loadInsights(refresh, Boolean(bedrockStatus?.configured)),
    [bedrockStatus?.configured, loadInsights],
  );

  useEffect(() => {
    let cancelled = false;
    void fetchBedrockStatus()
      .then((status) => {
        if (cancelled) return;
        setBedrockStatus(status);
        return loadInsights(false, status.configured);
      })
      .catch(() => {
        if (!cancelled) void loadInsights(false, false);
      });
    return () => {
      cancelled = true;
    };
  }, [customerId, loadInsights]);

  const focusLabel =
    insights?.primary_focus === "retention"
      ? t("customer.insights.focusChurn")
      : t("customer.insights.focusUpsell");

  const actionMeta = insights?.recommendation_actions ?? [];
  const llmProvider = resolveLlmProvider(bedrockStatus);
  const configuredBrand = llmBrandName(t, llmProvider);
  const fromLlm = isLlmGeneratedSource(insights?.source);
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

        {(loading || refreshing) && !insights && (
          <p className="muted">
            {bedrockStatus?.configured
              ? t("customer.insights.loadingLlm", { brand: configuredBrand })
              : t("customer.insights.loadingLocal")}
          </p>
        )}
        {(loading || refreshing) && streamPreview && (
          <div className="insights-stream-preview" aria-live="polite">
            {streamPreview}
          </div>
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
                  ? t("customer.insights.poweredBy", {
                      brand: brandForSource(t, insights.source, llmProvider),
                    })
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
                  title={t("customer.insights.modelTitle", {
                    brand: brandForSource(t, insights.source, llmProvider),
                  })}
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

            {insights.preamble?.trim() && (
              <p className="insights-preamble">{insights.preamble}</p>
            )}

            <p className="insights-summary">{insights.summary}</p>

            {proseParagraphs(insights.guidance).length > 0 && (
              <>
                <h2 className="insights-subhead">{t("customer.insights.guidanceHeading")}</h2>
                <div className="insights-prose">
                  {proseParagraphs(insights.guidance).map((para) => (
                    <p key={para.slice(0, 48)}>{para}</p>
                  ))}
                </div>
              </>
            )}

            {insights.recommendations.length > 0 && (
              <>
                <h2 className="insights-subhead">{t("customer.insights.outreachHeading")}</h2>
                <div className="insights-outreach">
                  {insights.recommendations.map((item, idx) => {
                    const meta = actionMeta[idx];
                    const actionable = meta?.actionable ?? false;
                    return (
                      <p key={`${idx}-${item.slice(0, 32)}`} className="insights-outreach-item">
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
                      </p>
                    );
                  })}
                </div>
              </>
            )}

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
                {t("customer.insights.llmError", {
                  brand: configuredBrand,
                  reason: insights.fallback_reason,
                })}
              </p>
            )}

            {!fromLlm && !insights.bedrock_configured && (
              <p className="muted small insights-hint">
                {envHint(t, llmProvider, configuredBrand)}
              </p>
            )}

            {!fromLlm &&
              insights.bedrock_configured &&
              !insights.fallback_reason &&
              llmProvider === "bedrock" && (
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
