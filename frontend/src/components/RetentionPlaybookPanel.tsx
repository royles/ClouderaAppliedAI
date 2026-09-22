import { useTranslation } from "react-i18next";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  CustomerSegment,
  fetchRetentionPlaybook,
  PlaybookRecommendedAction,
  RetentionPlaybook,
  RetentionPlaybookItem,
  streamRetentionRecommendation,
} from "../api";
import { CUSTOMER_BASE, customerPath } from "../appRoutes";
import { cohortSearchString } from "../cohortQuery";
import { withCopilotFocus } from "../copilotNavigation";
import { formatMoneyIls, formatNumber } from "../localeFormat";
import { partialJsonStringField } from "../jsonStreamPreview";
import ChurnBadge from "../ChurnBadge";
import { displayCustomerName } from "../pii";
import { useMobileUx } from "../mobileUxContext";
import { apiLocaleCode } from "../i18n/index";

type Props = {
  segment: CustomerSegment;
  cohortLabel?: string | null;
  compact?: boolean;
};

const STREAM_CONCURRENCY = 6;

async function runRetentionStreamPool(
  customerIds: number[],
  locale: string,
  handlers: {
    onMeta: () => void;
    onLlmUnavailable: () => void;
    onDelta: (customerId: number, preview: PlaybookRecommendedAction) => void;
    onDone: (customerId: number, action: PlaybookRecommendedAction) => void;
    onFailed: (customerId: number) => void;
    isCancelled: () => boolean;
  },
): Promise<void> {
  let nextIndex = 0;

  async function worker() {
    while (nextIndex < customerIds.length) {
      if (handlers.isCancelled()) return;
      const customerId = customerIds[nextIndex];
      nextIndex += 1;
      try {
        await streamRetentionRecommendation(customerId, locale, {
          onMeta: () => {
            if (!handlers.isCancelled()) handlers.onMeta();
          },
          onDelta: (_piece, buffer) => {
            if (handlers.isCancelled()) return;
            const title = partialJsonStringField(buffer, "title");
            const detail = partialJsonStringField(buffer, "detail");
            if (!title && !detail) return;
            handlers.onDelta(customerId, {
              action_code: "llm_snippet",
              title: title || "…",
              detail: detail || "",
            });
          },
          onDone: (payload) => {
            if (handlers.isCancelled()) return;
            handlers.onDone(customerId, payload.recommended_action);
          },
          onError: (detail) => {
            if (!handlers.isCancelled()) {
              if (/LLM not configured/i.test(detail)) {
                handlers.onLlmUnavailable();
              }
              handlers.onFailed(customerId);
            }
          },
        });
      } catch {
        if (!handlers.isCancelled()) handlers.onFailed(customerId);
      }
    }
  }

  const workers = Math.min(STREAM_CONCURRENCY, customerIds.length);
  await Promise.all(Array.from({ length: workers }, () => worker()));
}

export default function RetentionPlaybookPanel({
  segment,
  cohortLabel,
  compact = false,
}: Props) {
  const { t } = useTranslation();
  const { isPhone, enterMobileContent } = useMobileUx();
  const [data, setData] = useState<RetentionPlaybook | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionsByCustomer, setActionsByCustomer] = useState<
    Record<number, PlaybookRecommendedAction>
  >({});
  const [streamingIds, setStreamingIds] = useState<Set<number>>(() => new Set());
  const [actionsLoading, setActionsLoading] = useState(false);
  const [llmConfigured, setLlmConfigured] = useState(true);
  const streamGenerationRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setActionsByCustomer({});
    setStreamingIds(new Set());
    void fetchRetentionPlaybook({ segment, limit: 25 })
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch(() => {
        if (!cancelled) setData(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [segment]);

  const customerIds = useMemo(
    () => (data?.items ?? []).map((item) => item.customer_id),
    [data],
  );

  useEffect(() => {
    if (customerIds.length === 0) return;

    const generation = streamGenerationRef.current + 1;
    streamGenerationRef.current = generation;
    let cancelled = false;

    setActionsLoading(true);
    setLlmConfigured(true);
    setActionsByCustomer({});
    setStreamingIds(new Set(customerIds));

    const locale = apiLocaleCode();
    let sawLlmMeta = false;

    void runRetentionStreamPool(customerIds, locale, {
      isCancelled: () => cancelled || streamGenerationRef.current !== generation,
      onMeta: () => {
        sawLlmMeta = true;
        setLlmConfigured(true);
      },
      onLlmUnavailable: () => setLlmConfigured(false),
      onDelta: (customerId, preview) => {
        setActionsByCustomer((prev) => ({ ...prev, [customerId]: preview }));
      },
      onDone: (customerId, action) => {
        setActionsByCustomer((prev) => ({ ...prev, [customerId]: action }));
        setStreamingIds((prev) => {
          const next = new Set(prev);
          next.delete(customerId);
          return next;
        });
      },
      onFailed: (customerId) => {
        setStreamingIds((prev) => {
          const next = new Set(prev);
          next.delete(customerId);
          return next;
        });
      },
    }).finally(() => {
      if (cancelled || streamGenerationRef.current !== generation) return;
      if (!sawLlmMeta) {
        setLlmConfigured(false);
      }
      setStreamingIds(new Set());
      setActionsLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [customerIds]);

  const listHref = `${CUSTOMER_BASE}${cohortSearchString({
    segment,
    sortBy: "customer_value",
    sortOrder: "desc",
    metric: "at_risk",
    page: 1,
  })}`;

  const navigateFromQueue = () => {
    if (isPhone) enterMobileContent();
  };

  return (
    <div className={`retention-playbook-panel${compact ? " retention-playbook-panel--compact" : ""}`}>
      {!compact && (
        <p className="muted small">
          {cohortLabel ? `${cohortLabel} · ` : ""}
          {t("assistant.retention.lede")}
        </p>
      )}
      {loading && <p className="muted small">{t("assistant.retention.loadingQueue")}</p>}
      {!loading && data && data.items.length === 0 && (
        <p className="muted small">{t("assistant.retention.emptyCohort")}</p>
      )}
      {!loading && data && data.items.length > 0 && (
        <>
          <p className="muted small playbook-queue-meta">
            {t("assistant.retention.showing", {
              shown: data.items.length,
              total: formatNumber(data.total),
            })}
          </p>
          {!actionsLoading && !llmConfigured && (
            <p className="muted small">{t("assistant.retention.llmUnavailable")}</p>
          )}
          <ol className="playbook-queue">
            {data.items.map((item: RetentionPlaybookItem, idx) => {
              const action = actionsByCustomer[item.customer_id];
              const isStreaming = streamingIds.has(item.customer_id);
              const profileHref = withCopilotFocus(customerPath(item.customer_id), isPhone);
              return (
                <li key={item.customer_id} className="playbook-queue-item">
                  <div className="playbook-queue-rank">{idx + 1}</div>
                  <div className="playbook-queue-body">
                    <Link
                      to={profileHref}
                      className="playbook-customer-link"
                      onClick={navigateFromQueue}
                    >
                      {displayCustomerName(item.customer_name)}
                    </Link>
                    <div className="playbook-queue-meta-row">
                      <ChurnBadge tier={item.churn_risk_tier} probability={item.churn_probability} />
                      <span className="muted small">
                        {t("assistant.retention.atRiskBook", {
                          atRisk: formatMoneyIls(item.value_at_risk),
                          book: formatMoneyIls(item.customer_value),
                        })}
                      </span>
                    </div>
                    {isStreaming && !action && (
                      <p className="muted small playbook-action-loading">
                        {t("assistant.retention.loadingAction")}
                      </p>
                    )}
                    {!actionsLoading && llmConfigured && !action && !isStreaming && (
                      <p className="muted small">{t("assistant.retention.actionMissing")}</p>
                    )}
                    {action && (
                      <>
                        <p
                          className={`playbook-action-title${isStreaming ? " playbook-action-streaming" : ""}`}
                        >
                          {action.title}
                        </p>
                        <p
                          className={`muted small playbook-action-detail${isStreaming ? " playbook-action-streaming" : ""}`}
                        >
                          {action.detail}
                        </p>
                      </>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
          <Link
            to={withCopilotFocus(listHref, isPhone)}
            className="playbook-view-all"
            onClick={navigateFromQueue}
          >
            {t("assistant.retention.openList")}
          </Link>
        </>
      )}
    </div>
  );
}
