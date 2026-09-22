import { useTranslation } from "react-i18next";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  CustomerSegment,
  fetchRetentionPlaybook,
  fetchRetentionRecommendations,
  PlaybookRecommendedAction,
  RetentionPlaybook,
  RetentionPlaybookItem,
} from "../api";
import { CUSTOMER_BASE, customerPath } from "../appRoutes";
import { cohortSearchString } from "../cohortQuery";
import { withCopilotFocus } from "../copilotNavigation";
import { formatMoneyIls, formatNumber } from "../localeFormat";
import ChurnBadge from "../ChurnBadge";
import { displayCustomerName } from "../pii";
import { useMobileUx } from "../mobileUxContext";

type Props = {
  segment: CustomerSegment;
  cohortLabel?: string | null;
  compact?: boolean;
};

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
  const [actionsLoading, setActionsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setActionsByCustomer({});
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
    let cancelled = false;
    setActionsLoading(true);
    void fetchRetentionRecommendations(customerIds)
      .then((res) => {
        if (cancelled) return;
        const next: Record<number, PlaybookRecommendedAction> = {};
        for (const row of res.recommendations) {
          next[row.customer_id] = row.recommended_action;
        }
        setActionsByCustomer(next);
      })
      .catch(() => {
        if (!cancelled) setActionsByCustomer({});
      })
      .finally(() => {
        if (!cancelled) setActionsLoading(false);
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
          <ol className="playbook-queue">
            {data.items.map((item: RetentionPlaybookItem, idx) => {
              const action = actionsByCustomer[item.customer_id];
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
                    {actionsLoading && !action && (
                      <p className="muted small playbook-action-loading">
                        {t("assistant.retention.loadingAction")}
                      </p>
                    )}
                    {action && (
                      <>
                        <p className="playbook-action-title">{action.title}</p>
                        <p className="muted small">{action.detail}</p>
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
