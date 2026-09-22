import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { CustomerSummary } from "../api";
import ChurnBadge from "../ChurnBadge";
import CustomerAvatar from "./CustomerAvatar";
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
  const { t } = useTranslation();
  const { customer, showRank, rank, className = "" } = props;
  const cardClass = `customer-card${props.variant === "static" ? " customer-card-static" : ""}${className ? ` ${className}` : ""}`;

  const body = (
    <>
      <div className="customer-card-top">
        <CustomerAvatar
          customerId={customer.customer_id}
          customerName={customer.customer_name}
          size="lg"
        />
        <div className="customer-card-main">
          <div className="customer-card-headline">
            <div className="customer-card-identity">
              {showRank && rank != null && (
                <span
                  className="customer-card-rank"
                  aria-label={t("customer.card.rankA11y", { rank })}
                >
                  #{rank}
                </span>
              )}
              <h3 className="customer-card-name">
                {displayCustomerName(customer.customer_name)}
              </h3>
              <p className="muted small customer-card-id">
                {displayCustomerId(customer.customer_id)}
                {formatCity(customer.city_name) !== "—"
                  ? ` · ${formatCity(customer.city_name)}`
                  : ""}
              </p>
            </div>
            <ChurnBadge
              probability={customer.churn_probability}
              tier={customer.churn_risk_tier}
            />
          </div>
          <p className="customer-card-value">
            <span className="label">{t("customer.card.value")}</span>
            <strong>{formatMoneyIls(customer.customer_value)}</strong>
          </p>
        </div>
      </div>

      <dl className="customer-card-stats">
        <div>
          <dt>{t("customer.card.policies")}</dt>
          <dd>{customer.policy_count ?? 0}</dd>
        </div>
        <div>
          <dt>{t("customer.card.investments")}</dt>
          <dd>{customer.investment_count ?? 0}</dd>
        </div>
        <div>
          <dt>{t("customer.card.lastLogin")}</dt>
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
      <article className={cardClass} aria-label={t("customer.card.a11ySummary")}>
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
