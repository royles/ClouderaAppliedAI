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
import { formatMoneyIls } from "../formatMoney";
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
          {t("copilot.retention.lede")}
        </p>
      )}
      {loading && <p className="muted small">{t("copilot.retention.loadingQueue")}</p>}
      {!loading && data && data.items.length === 0 && (
        <p className="muted small">{t("copilot.retention.emptyCohort")}</p>
      )}
      {!loading && data && data.items.length > 0 && (
        <>
          <p className="muted small playbook-queue-meta">
            {t("copilot.retention.showing", {
              shown: data.items.length,
              total: data.total.toLocaleString(),
            })}
          </p>
          <ol className="playbook-queue">
            {data.items.map((item: RetentionPlaybookItem, idx) => (
              <li key={item.customer_id} className="playbook-queue-item">
                <div className="playbook-queue-rank">{idx + 1}</div>
                <div className="playbook-queue-body">
                  <Link to={customerPath(item.customer_id)} className="playbook-customer-link">
                    {displayCustomerName(item.customer_name)}
                  </Link>
                  <div className="playbook-queue-meta-row">
                    <ChurnBadge tier={item.churn_risk_tier} probability={item.churn_probability} />
                    <span className="muted small">
                      {t("copilot.retention.atRiskBook", {
                        atRisk: formatMoneyIls(item.value_at_risk),
                        book: formatMoneyIls(item.customer_value),
                      })}
                    </span>
                  </div>
                  <p className="playbook-action-title">{item.recommended_action.title}</p>
                  <p className="muted small">{item.recommended_action.detail}</p>
                </div>
              </li>
            ))}
          </ol>
          <Link to={listHref} className="playbook-view-all">
            {t("copilot.retention.openList")}
          </Link>
        </>
      )}
    </div>
  );
}
