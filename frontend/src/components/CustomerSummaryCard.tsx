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

export type CustomerSummaryCardData = Pick<
  CustomerSummary,
  | "customer_id"
  | "customer_name"
  | "city_name"
  | "email"
  | "mobile_no"
  | "last_login"
  | "policy_count"
  | "investment_count"
  | "customer_value"
  | "churn_probability"
  | "churn_risk_tier"
>;

type BaseProps = {
  customer: CustomerSummaryCardData;
  showRank?: boolean;
  rank?: number;
  className?: string;
};

type LinkProps = BaseProps & {
  variant?: "link";
  to: string;
  linkState?: { businessReturn?: string };
};

type StaticProps = BaseProps & {
  variant: "static";
};

type Props = LinkProps | StaticProps;

export default function CustomerSummaryCard(props: Props) {
  const { customer, showRank, rank, className = "" } = props;
  const cardClass = `customer-card${props.variant === "static" ? " customer-card-static" : ""}${className ? ` ${className}` : ""}`;

  const body = (
    <>
      <div className="customer-card-top">
        <div className="customer-card-identity">
          {showRank && rank != null && (
            <span className="customer-card-rank" aria-label={`Rank ${rank}`}>
              #{rank}
            </span>
          )}
          <h3 className="customer-card-name">{displayCustomerName(customer.customer_name)}</h3>
          <p className="muted small customer-card-id">
            {displayCustomerId(customer.customer_id)}
            {formatCity(customer.city_name) !== "—"
              ? ` · ${formatCity(customer.city_name)}`
              : ""}
          </p>
          <p className="customer-card-value">
            <span className="label">Customer value</span>
            <strong>{formatMoneyIls(customer.customer_value)}</strong>
          </p>
        </div>
        <ChurnBadge
          probability={customer.churn_probability}
          tier={customer.churn_risk_tier}
        />
      </div>

      <dl className="customer-card-stats">
        <div>
          <dt>Policies</dt>
          <dd>{customer.policy_count ?? 0}</dd>
        </div>
        <div>
          <dt>Investments</dt>
          <dd>{customer.investment_count ?? 0}</dd>
        </div>
        <div>
          <dt>Last login</dt>
          <dd>{formatLastLogin(customer.last_login)}</dd>
        </div>
      </dl>

      <p className="customer-card-contact muted small">
        <span>{maskEmail(customer.email)}</span>
        <span className="customer-card-contact-sep" aria-hidden>
          ·
        </span>
        <span>{maskPhone(customer.mobile_no)}</span>
      </p>
    </>
  );

  if (props.variant === "static") {
    return (
      <article className={cardClass} aria-label="Customer summary">
        {body}
      </article>
    );
  }

  return (
    <Link to={props.to} state={props.linkState} className={cardClass}>
      {body}
    </Link>
  );
}
