import { Link } from "react-router-dom";
import { CustomerSummary } from "../api";
import ChurnBadge from "../ChurnBadge";
import { formatMoneyIls } from "../formatMoney";
import {
  displayCustomerId,
  displayCustomerName,
  formatCity,
  formatLastLogin,
  maskEmail,
  maskPhone,
} from "../pii";

type Props = {
  customers: CustomerSummary[];
  showRank: boolean;
  rankStart: number;
  dashboardReturn: string;
};

export default function CustomerCardGrid({
  customers,
  showRank,
  rankStart,
  dashboardReturn,
}: Props) {
  if (customers.length === 0) {
    return <p className="muted customer-grid-empty">No customers match this filter.</p>;
  }

  return (
    <ul className="customer-card-grid">
      {customers.map((c, index) => {
        const rank = rankStart + index;
        return (
          <li key={c.customer_id}>
            <Link
              to={`/customers/${c.customer_id}`}
              state={{ dashboardReturn }}
              className="customer-card"
            >
              <div className="customer-card-top">
                <div className="customer-card-identity">
                  {showRank && (
                    <span className="customer-card-rank" aria-label={`Rank ${rank}`}>
                      #{rank}
                    </span>
                  )}
                  <h3 className="customer-card-name">
                    {displayCustomerName(c.customer_name)}
                  </h3>
                  <p className="muted small customer-card-id">
                    {displayCustomerId(c.customer_id)}
                    {formatCity(c.city_name) !== "—"
                      ? ` · ${formatCity(c.city_name)}`
                      : ""}
                  </p>
                  <p className="customer-card-value">
                    <span className="label">Customer value</span>
                    <strong>{formatMoneyIls(c.customer_value)}</strong>
                  </p>
                </div>
                <ChurnBadge
                  probability={c.churn_probability}
                  tier={c.churn_risk_tier}
                />
              </div>

              <dl className="customer-card-stats">
                <div>
                  <dt>Policies</dt>
                  <dd>{c.policy_count ?? 0}</dd>
                </div>
                <div>
                  <dt>Investments</dt>
                  <dd>{c.investment_count ?? 0}</dd>
                </div>
                <div>
                  <dt>Last login</dt>
                  <dd>{formatLastLogin(c.last_login)}</dd>
                </div>
              </dl>

              <p className="customer-card-contact muted small">
                <span>{maskEmail(c.email)}</span>
                <span className="customer-card-contact-sep" aria-hidden>
                  ·
                </span>
                <span>{maskPhone(c.mobile_no)}</span>
              </p>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
