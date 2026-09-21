import { DomainCount, Overview } from "../api";
import { CustomerSegment } from "../api";

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
              Counts refreshed {updatedAt.toLocaleTimeString()}
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
                      {policyTotal.toLocaleString()}
                    </div>
                    <div className="stat-label">{d.domain}</div>
                    <div className="stat-policy-foot">
                      {policyActive.toLocaleString()} active · avg{" "}
                      {avgPoliciesPerCustomer.toFixed(1)} / customer
                    </div>
                  </>
                ) : (
                  <>
                    <div className="stat-value">
                      {(d.row_count ?? 0).toLocaleString()}
                    </div>
                    <div className="stat-label">{d.domain}</div>
                    {filterKey === "customers_all" &&
                      policyTotal > 0 &&
                      d.policy_total != null && (
                        <div className="stat-policy-foot">
                          {policyTotal.toLocaleString()} policies ·{" "}
                          {policyActive.toLocaleString()} active
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
