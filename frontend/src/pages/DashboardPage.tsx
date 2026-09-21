import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import {
  CustomerSegment,
  DomainCount,
  fetchOverview,
  fetchPortfolioAnalytics,
  Overview,
  PortfolioAnalytics,
} from "../api";
import { BUSINESS_BASE, CUSTOMER_BASE } from "../appRoutes";
import Breadcrumbs from "../components/Breadcrumbs";
import DomainFilterGrid from "../components/DomainFilterGrid";
import PortfolioAnalyticsSection from "../components/PortfolioAnalyticsSection";
import { cohortSearchString } from "../cohortQuery";
import { parseBusinessSegment, patchBusinessSegment } from "../dashboardUrl";
export default function DashboardPage() {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const segment = useMemo(() => parseBusinessSegment(searchParams), [searchParams]);

  const [overview, setOverview] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [portfolioAnalytics, setPortfolioAnalytics] = useState<PortfolioAnalytics | null>(
    null,
  );
  const [portfolioLoading, setPortfolioLoading] = useState(true);
  const [overviewUpdatedAt, setOverviewUpdatedAt] = useState<Date | null>(null);
  const portfolioRequestRef = useRef(0);
  const portfolioSegmentRef = useRef<CustomerSegment | null>(null);

  const activeDomain = useMemo((): DomainCount | null => {
    if (segment === "customers_all" || !overview?.domains) return null;
    const match = overview.domains.find((d) => d.filter_key === segment);
    return match ?? null;
  }, [segment, overview]);

  useEffect(() => {
    if (location.pathname !== BUSINESS_BASE) return;

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
          setError(e instanceof Error ? e.message : "Failed to load overview");
        }
      } finally {
        if (!cancelled) setOverviewLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [location.pathname, location.key]);

  const loadPortfolioAnalytics = useCallback(async (seg: CustomerSegment) => {
    const requestId = ++portfolioRequestRef.current;
    if (portfolioSegmentRef.current !== seg) {
      setPortfolioAnalytics(null);
      portfolioSegmentRef.current = seg;
    }
    setPortfolioLoading(true);
    try {
      const data = await fetchPortfolioAnalytics(seg);
      if (requestId !== portfolioRequestRef.current) return;
      setPortfolioAnalytics(data);
    } catch {
      if (requestId === portfolioRequestRef.current) {
        setPortfolioAnalytics(null);
      }
    } finally {
      if (requestId === portfolioRequestRef.current) {
        setPortfolioLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    if (location.pathname !== BUSINESS_BASE || overviewLoading) return;

    void loadPortfolioAnalytics(segment);

    return () => {
      portfolioRequestRef.current += 1;
    };
  }, [
    segment,
    loadPortfolioAnalytics,
    location.pathname,
    location.key,
    overviewLoading,
  ]);

  const setSegment = (next: CustomerSegment) => {
    setSearchParams((prev) => patchBusinessSegment(prev, next), { replace: true });
  };

  const customerListHref = `${CUSTOMER_BASE}${cohortSearchString({ segment })}`;

  if (overviewLoading && !overview) {
    return (
      <>
        <Breadcrumbs items={[{ label: "The business" }]} />
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

  return (
    <>
      <Breadcrumbs items={[{ label: "The business" }]} />
      <section className="panel">
        <div className="panel-head">
          <div>
            <h1>Warehouse overview</h1>
            <p className="muted small">
              Click a card to set the cohort for portfolio analytics. Customer search
              and lists live on{" "}
              <Link to={customerListHref}>the customer</Link> area (same filters).
            </p>
          </div>
          {overviewUpdatedAt && (
            <p className="muted small data-freshness">
              Counts refreshed {overviewUpdatedAt.toLocaleTimeString()}
            </p>
          )}
        </div>
        <DomainFilterGrid
          overview={overview}
          segment={segment}
          onSelect={setSegment}
          helperText="Click a card to filter analytics. Click again to clear."
        />
        <PortfolioAnalyticsSection
          data={portfolioAnalytics}
          loading={portfolioLoading && !portfolioAnalytics}
          refreshing={portfolioLoading && portfolioAnalytics != null}
          cohortLabel={activeDomain?.domain ?? null}
        />
      </section>
    </>
  );
}
