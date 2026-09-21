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
  open: boolean;
  onClose: () => void;
  segment: CustomerSegment;
  cohortLabel?: string | null;
};

export default function RetentionPlaybookDrawer({
  open,
  onClose,
  segment,
  cohortLabel,
}: Props) {
  const [data, setData] = useState<RetentionPlaybook | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
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
  }, [open, segment]);

  if (!open) return null;

  const listHref = `${CUSTOMER_BASE}${cohortSearchString({
    segment,
    sortBy: "customer_value",
    sortOrder: "desc",
    metric: "at_risk",
    page: 1,
  })}`;

  return (
    <div className="playbook-backdrop" role="presentation" onClick={onClose}>
      <aside
        className="playbook-drawer"
        role="dialog"
        aria-labelledby="retention-playbook-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="playbook-drawer-head">
          <div>
            <h2 id="retention-playbook-title">Retention playbook</h2>
            <p className="muted small">
              {cohortLabel ? `${cohortLabel} · ` : ""}
              Prioritized by value at churn risk (next best action per customer).
            </p>
          </div>
          <button type="button" className="playbook-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>
        {loading && <p className="muted small">Loading queue…</p>}
        {!loading && data && data.items.length === 0 && (
          <p className="muted small">No scored at-risk customers in this cohort yet.</p>
        )}
        {!loading && data && data.items.length > 0 && (
          <>
            <p className="muted small playbook-queue-meta">
              Showing {data.items.length} of {data.total.toLocaleString()} at-risk customers
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
                        At risk {formatMoneyIls(item.value_at_risk)} · Book{" "}
                        {formatMoneyIls(item.customer_value)}
                      </span>
                    </div>
                    <p className="playbook-action-title">{item.recommended_action.title}</p>
                    <p className="muted small">{item.recommended_action.detail}</p>
                  </div>
                </li>
              ))}
            </ol>
            <Link to={listHref} className="playbook-view-all" onClick={onClose}>
              Open full at-risk customer list →
            </Link>
          </>
        )}
      </aside>
    </div>
  );
}
