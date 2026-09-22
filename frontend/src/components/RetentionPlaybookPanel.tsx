import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  CustomerSegment,
  fetchRetentionPlaybook,
  RetentionPlaybook,
  RetentionPlaybookItem,
} from "../api";
import { CUSTOMER_BASE, customerPath } from "../appRoutes";
import { cohortSearchString } from "../cohortQuery";
import { formatMoneyIls, formatNumber } from "../localeFormat";
import { retentionRecommendedAction } from "../i18n/recommendedActions";
import ChurnBadge from "../ChurnBadge";
import { displayCustomerName } from "../pii";

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
  const [data, setData] = useState<RetentionPlaybook | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
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

  const listHref = `${CUSTOMER_BASE}${cohortSearchString({
    segment,
    sortBy: "customer_value",
    sortOrder: "desc",
    metric: "at_risk",
    page: 1,
  })}`;

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
              const actionCopy = retentionRecommendedAction(t, item.recommended_action);
              return (
              <li key={item.customer_id} className="playbook-queue-item">
                <div className="playbook-queue-rank">{idx + 1}</div>
                <div className="playbook-queue-body">
                  <Link to={customerPath(item.customer_id)} className="playbook-customer-link">
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
                  <p className="playbook-action-title">{actionCopy.title}</p>
                  <p className="muted small">{actionCopy.detail}</p>
                </div>
              </li>
            );
            })}
          </ol>
          <Link to={listHref} className="playbook-view-all">
            {t("assistant.retention.openList")}
          </Link>
        </>
      )}
    </div>
  );
}
