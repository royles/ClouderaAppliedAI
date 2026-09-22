import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { CustomerSummary } from "../api";
import ChurnBadge from "../ChurnBadge";
import CustomerAvatar from "./CustomerAvatar";
import ReviewStarRating from "./ReviewStarRating";
import { formatMoneyIls } from "../localeFormat";
import {
  displayCustomerId,
  displayCustomerName,
  formatCity,
  formatLastLogin,
  maskDate,
  maskEmail,
  maskPhone,
  maskStreet,
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
  | "avg_review_rating"
  | "review_count"
>;

/** Extra profile fields for the customer detail hero card (not shown on directory tiles). */
export type CustomerCardProfileDetails = {
  customer_type_dsc?: string | null;
  birth_date?: string | null;
  marital_status_dsc?: string | null;
  street_name?: string | null;
  communication_dsc?: string | null;
  last_interaction_ts?: string | null;
  churn_scored_at?: string | null;
  churn_model_version?: string | null;
};

type BaseProps = {
  customer: CustomerSummaryCardData;
  showRank?: boolean;
  rank?: number;
  className?: string;
  /** Full profile block for detail view — single source for customer demographics. */
  profileDetails?: CustomerCardProfileDetails | null;
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

function formatAddress(
  street: string | null | undefined,
  city: string | null | undefined,
  emDash: string,
): string {
  const parts = [maskStreet(street), formatCity(city)].filter((x) => x !== emDash);
  return parts.length ? parts.join(", ") : emDash;
}

export default function CustomerSummaryCard(props: Props) {
  const { t } = useTranslation();
  const emDash = t("common.emDash");
  const { customer, showRank, rank, className = "", profileDetails } = props;
  const showProfile = Boolean(profileDetails);
  const cardClass = `customer-card${props.variant === "static" ? " customer-card-static" : ""}${showProfile ? " customer-card-full-profile" : ""}${className ? ` ${className}` : ""}`;

  const body = (
    <>
      <div className="customer-card-top">
        <CustomerAvatar
          customerId={customer.customer_id}
          customerName={customer.customer_name}
          size={showProfile ? "lg" : "md"}
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
                {!showProfile &&
                  formatCity(customer.city_name) !== emDash &&
                  ` · ${formatCity(customer.city_name)}`}
              </p>
              <ReviewStarRating
                average={customer.avg_review_rating}
                reviewCount={customer.review_count}
                compact={!showProfile}
                className="customer-card-review-stars"
              />
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

      {showProfile && profileDetails && (
        <dl className="customer-card-profile">
          <div>
            <dt>{t("customer.profile.type")}</dt>
            <dd>{profileDetails.customer_type_dsc ?? emDash}</dd>
          </div>
          <div>
            <dt>{t("customer.profile.birthDate")}</dt>
            <dd>{maskDate(profileDetails.birth_date)}</dd>
          </div>
          <div>
            <dt>{t("customer.profile.maritalStatus")}</dt>
            <dd>{profileDetails.marital_status_dsc ?? emDash}</dd>
          </div>
          <div className="customer-card-profile-span2">
            <dt>{t("customer.profile.address")}</dt>
            <dd>
              {formatAddress(
                profileDetails.street_name,
                customer.city_name,
                emDash,
              )}
            </dd>
          </div>
          <div>
            <dt>{t("customer.profile.communication")}</dt>
            <dd>{profileDetails.communication_dsc ?? emDash}</dd>
          </div>
          <div>
            <dt>{t("customer.card.lastLogin")}</dt>
            <dd>{formatLastLogin(customer.last_login)}</dd>
          </div>
          <div>
            <dt>{t("customer.profile.lastInteraction")}</dt>
            <dd>
              {profileDetails.last_interaction_ts
                ? formatLastLogin(profileDetails.last_interaction_ts)
                : emDash}
            </dd>
          </div>
          {profileDetails.churn_scored_at && (
            <div className="customer-card-profile-span2">
              <dt>{t("customer.card.churnScored")}</dt>
              <dd>
                {formatLastLogin(profileDetails.churn_scored_at)}
                {profileDetails.churn_model_version
                  ? ` · ${profileDetails.churn_model_version}`
                  : ""}
              </dd>
            </div>
          )}
        </dl>
      )}

      <dl className="customer-card-stats">
        <div>
          <dt>{t("customer.card.policies")}</dt>
          <dd>{customer.policy_count ?? 0}</dd>
        </div>
        <div>
          <dt>{t("customer.card.investments")}</dt>
          <dd>{customer.investment_count ?? 0}</dd>
        </div>
        {!showProfile && (
          <div>
            <dt>{t("customer.card.lastLogin")}</dt>
            <dd>{formatLastLogin(customer.last_login)}</dd>
          </div>
        )}
        {showProfile && (
          <div>
            <dt>{t("customer.table.columns.email")}</dt>
            <dd className="customer-card-stat-contact">{maskEmail(customer.email)}</dd>
          </div>
        )}
        {showProfile && (
          <div>
            <dt>{t("customer.table.columns.mobile")}</dt>
            <dd className="customer-card-stat-contact">{maskPhone(customer.mobile_no)}</dd>
          </div>
        )}
      </dl>

      {!showProfile && (
        <p className="customer-card-contact muted small">
          <span>{maskEmail(customer.email)}</span>
          <span className="customer-card-contact-sep" aria-hidden>
            ·
          </span>
          <span>{maskPhone(customer.mobile_no)}</span>
        </p>
      )}

      {showProfile && (
        <p className="muted small customer-card-privacy">{t("customer.privacyNotice")}</p>
      )}
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
