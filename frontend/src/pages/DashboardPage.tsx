import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import {
  CustomerSegment,
  DomainCount,
  fetchOverview,
  fetchPortfolioAnalytics,
  Overview,
  PortfolioAnalytics,
} from "../api";
import { BUSINESS_BASE } from "../appRoutes";
import Breadcrumbs from "../components/Breadcrumbs";
import DomainFilterGrid from "../components/DomainFilterGrid";
import PortfolioAnalyticsSection from "../components/PortfolioAnalyticsSection";
import { parseBusinessSegment, patchBusinessSegment } from "../dashboardUrl";
import {
  PORTFOLIO_PREFETCH_SEGMENTS,
  PortfolioSegmentCache,
  prefetchPortfolioAnalytics,
} from "../portfolioSegmentCache";

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
  const portfolioCacheRef = useRef<PortfolioSegmentCache>(new Map());
  const prefetchStartedRef = useRef(false);
  const segmentRef = useRef(segment);
  segmentRef.current = segment;

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

  const applySegmentFromCache = useCallback((seg: CustomerSegment) => {
    const cached = portfolioCacheRef.current.get(seg);
    if (cached) {
      setPortfolioAnalytics(cached);
      setPortfolioLoading(false);
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    if (location.pathname !== BUSINESS_BASE || overviewLoading) return;
    if (applySegmentFromCache(segment)) return;

    let cancelled = false;
    setPortfolioLoading(true);
    void (async () => {
      try {
        const data = await fetchPortfolioAnalytics(segment);
        if (cancelled) return;
        portfolioCacheRef.current.set(segment, data);
        if (segmentRef.current === segment) {
          setPortfolioAnalytics(data);
        }
      } catch {
        if (!cancelled && segmentRef.current === segment) {
          setPortfolioAnalytics(null);
        }
      } finally {
        if (!cancelled && segmentRef.current === segment) {
          setPortfolioLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [segment, overviewLoading, location.pathname, applySegmentFromCache]);

  useEffect(() => {
    if (location.pathname !== BUSINESS_BASE || overviewLoading) return;
    if (prefetchStartedRef.current) return;
    prefetchStartedRef.current = true;

    void (async () => {
      try {
        const cache = await prefetchPortfolioAnalytics(PORTFOLIO_PREFETCH_SEGMENTS);
        portfolioCacheRef.current = cache;
        const active = segmentRef.current;
        if (cache.has(active)) {
          setPortfolioAnalytics(cache.get(active)!);
          setPortfolioLoading(false);
        }
      } catch {
        /* segment effect falls back to single-segment fetch */
      }
    })();
  }, [overviewLoading, location.pathname]);

  const setSegment = (next: CustomerSegment) => {
    applySegmentFromCache(next);
    setSearchParams((prev) => patchBusinessSegment(prev, next), { replace: true });
  };

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
          segment={segment}
        />
      </section>
    </>
  );
}
