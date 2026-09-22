import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { fetchCustomers, fetchOverview, CustomerSummary, Overview } from "../api";
import { CUSTOMER_BASE, customerPath } from "../appRoutes";
import Breadcrumbs from "../components/Breadcrumbs";
import ChurnBadge from "../ChurnBadge";
import CustomerDirectoryPanel from "../components/CustomerDirectoryPanel";
import DomainFilterGrid from "../components/DomainFilterGrid";
import { parseCohortSearch, patchCohortParams } from "../cohortQuery";
import { displayCustomerId, displayCustomerName, formatCity } from "../pii";
import { loadRecentCustomerIds } from "../recentCustomers";
import { useMobileFocus } from "../mobileUxContext";

export default function CustomerHubPage() {
  const { t } = useTranslation();
  const mobileFocus = useMobileFocus();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { segment } = useMemo(() => parseCohortSearch(searchParams), [searchParams]);

  const [overview, setOverview] = useState<Overview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [overviewUpdatedAt, setOverviewUpdatedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recentDetails, setRecentDetails] = useState<CustomerSummary[]>([]);

  useEffect(() => {
    if (location.pathname !== CUSTOMER_BASE) return;

    let cancelled = false;
    (async () => {
      setOverviewLoading(true);
      try {
        const ov = await fetchOverview();
        if (!cancelled) {
          setOverview(ov);
          setOverviewUpdatedAt(new Date());
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : t("errors.overviewLoadFailed"));
        }
      } finally {
        if (!cancelled) setOverviewLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [location.pathname, location.key]);

  useEffect(() => {
    const recentIds = loadRecentCustomerIds();
    if (recentIds.length === 0) {
      setRecentDetails([]);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const lists = await Promise.all(
          recentIds.map((id) =>
            fetchCustomers({ q: String(id), limit: 1 }).then((r) => r.customers[0]),
          ),
        );
        if (!cancelled) {
          setRecentDetails(lists.filter(Boolean) as CustomerSummary[]);
        }
      } catch {
        if (!cancelled) setRecentDetails([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [location.key]);

  const setSegment = (next: typeof segment) => {
    setSearchParams((prev) => patchCohortParams(prev, { segment: next, page: 1 }), {
      replace: true,
    });
  };

  if (overviewLoading && !overview) {
    return (
      <>
        <Breadcrumbs items={[{ label: t("nav.customer.title") }]} />
        <section className="panel">
          <div className="skeleton skeleton-title" />
          <div className="stat-grid">
            {[1, 2, 3, 4, 5].map((n) => (
              <div key={n} className="skeleton skeleton-stat" />
            ))}
          </div>
        </section>
      </>
    );
  }

  if (error && !overview) return <p className="error">{error}</p>;

  const listReturn = location.pathname + location.search;

  return (
    <>
      {!mobileFocus && <Breadcrumbs items={[{ label: t("nav.customer.title") }]} />}
      {!mobileFocus && (
      <section className="panel">
        <DomainFilterGrid
          overview={overview}
          segment={segment}
          onSelect={setSegment}
          helperText={t("business.domainFilter.helperCustomerList")}
          updatedAt={overviewUpdatedAt}
        />
      </section>
      )}

      <CustomerDirectoryPanel
        segment={segment}
        overviewDomains={overview?.domains}
        overviewReady={!overviewLoading}
        onClearFilter={() => setSegment("customers_all")}
        compact={mobileFocus}
      />

      {!mobileFocus && recentDetails.length > 0 && (
        <section className="panel">
          <h2>{t("customer.recent.title")}</h2>
          <ul className="customer-hub-list">
            {recentDetails.map((c) => (
              <li key={c.customer_id}>
                <Link
                  to={customerPath(c.customer_id)}
                  state={{ businessReturn: listReturn }}
                  className="customer-hub-row"
                >
                  <span className="customer-hub-name">
                    {displayCustomerName(c.customer_name)}
                  </span>
                  <span className="muted small">{displayCustomerId(c.customer_id)}</span>
                  <ChurnBadge
                    probability={c.churn_probability}
                    tier={c.churn_risk_tier}
                  />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
