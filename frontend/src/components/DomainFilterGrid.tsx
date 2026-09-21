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
                <div className="stat-value">
                  {(d.row_count ?? 0).toLocaleString()}
                </div>
                <div className="stat-label">{d.domain}</div>
              </button>
            );
          })}
        </div>
      )}
    </>
  );
}
