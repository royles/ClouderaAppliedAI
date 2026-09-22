import { useTranslation } from "react-i18next";
import { DomainCount, Overview } from "../api";
import { CustomerSegment } from "../api";
import { appIntlLocale } from "../i18n";
import { formatNumber } from "../localeFormat";

type Props = {
  overview: Overview | null;
  segment: CustomerSegment;
  onSelect: (segment: CustomerSegment) => void;
  helperText?: string;
  updatedAt?: Date | null;
};

export default function DomainFilterGrid({
  overview,
  segment,
  onSelect,
  helperText,
  updatedAt,
}: Props) {
  const { t } = useTranslation();
  const onCardClick = (domain: DomainCount) => {
    const key = domain.filter_key as CustomerSegment;
    onSelect(segment === key ? "customers_all" : key);
  };

  return (
    <>
      {(helperText || updatedAt) && (
        <div className="panel-head domain-filter-head">
          {helperText && <p className="muted small">{helperText}</p>}
          {updatedAt && (
            <p className="muted small data-freshness">
              {t("business.domainFilter.refreshedAt", {
                time: updatedAt.toLocaleTimeString(appIntlLocale()),
              })}
            </p>
          )}
        </div>
      )}
      {overview && (
        <div className="stat-grid">
          {(overview.domains ?? []).map((d) => {
            const filterKey = d.filter_key ?? "customers_all";
            const selected = segment === filterKey;
            const isPolicyBookCard = filterKey === "with_policies";
            const policyTotal = d.policy_total ?? 0;
            const policyActive = d.policy_active ?? 0;
            const customersInCohort = d.row_count ?? 0;
            const avgPoliciesPerCustomer =
              customersInCohort > 0 ? policyTotal / customersInCohort : 0;

            return (
              <button
                key={filterKey + d.domain}
                type="button"
                className={`stat-card stat-card-btn${selected ? " stat-card-selected" : ""}`}
                onClick={() =>
                  onCardClick({ ...d, filter_key: filterKey } as DomainCount)
                }
                title={d.description || d.domain}
              >
                {isPolicyBookCard ? (
                  <>
                    <div className="stat-value">
                      {formatNumber(policyTotal)}
                    </div>
                    <div className="stat-label">{d.domain}</div>
                    <div className="stat-policy-foot">
                      {t("business.domainFilter.policyFoot", {
                        active: formatNumber(policyActive),
                        avg: avgPoliciesPerCustomer.toFixed(1),
                      })}
                    </div>
                  </>
                ) : (
                  <>
                    <div className="stat-value">
                      {formatNumber(d.row_count ?? 0)}
                    </div>
                    <div className="stat-label">{d.domain}</div>
                    {filterKey === "customers_all" &&
                      policyTotal > 0 &&
                      d.policy_total != null && (
                        <div className="stat-policy-foot">
                          {t("business.domainFilter.allBookFoot", {
                            policies: formatNumber(policyTotal),
                            active: formatNumber(policyActive),
                          })}
                        </div>
                      )}
                  </>
                )}
              </button>
            );
          })}
        </div>
      )}
    </>
  );
}
