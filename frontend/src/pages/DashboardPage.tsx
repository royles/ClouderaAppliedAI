import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
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
import {
  parseBusinessSegment,
  patchBusinessSegment,
} from "../cohortQuery";
import {
  clonePortfolioAnalytics,
  PORTFOLIO_PREFETCH_SEGMENTS,
  portfolioAnalyticsMatchesSegment,
  PortfolioSegmentCache,
  prefetchPortfolioAnalytics,
} from "../portfolioSegmentCache";
import { useMobileFocus } from "../mobileUxContext";

export default function DashboardPage() {
  const { t } = useTranslation();
  const mobileFocus = useMobileFocus();
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
  const [bookBaseline, setBookBaseline] = useState<PortfolioAnalytics | null>(null);

  const syncBookBaselineFromCache = useCallback(() => {
    const all = portfolioCacheRef.current.get("customers_all");
    if (all) setBookBaseline(all);
  }, []);

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

  const applySegmentFromCache = useCallback((seg: CustomerSegment) => {
    const cached = portfolioCacheRef.current.get(seg);
    if (cached && cached.segment === seg) {
      setPortfolioAnalytics(clonePortfolioAnalytics(cached));
      setPortfolioLoading(false);
      syncBookBaselineFromCache();
      return true;
    }
    return false;
  }, [syncBookBaselineFromCache]);

  useEffect(() => {
    if (location.pathname !== BUSINESS_BASE || overviewLoading) return;
    if (applySegmentFromCache(segment)) return;

    let cancelled = false;
    setPortfolioAnalytics((prev) =>
      portfolioAnalyticsMatchesSegment(prev, segment) ? prev : null,
    );
    setPortfolioLoading(true);
    void (async () => {
      try {
        const data = clonePortfolioAnalytics(await fetchPortfolioAnalytics(segment));
        if (cancelled) return;
        portfolioCacheRef.current.set(segment, data);
        syncBookBaselineFromCache();
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
  }, [segment, overviewLoading, location.pathname, applySegmentFromCache, syncBookBaselineFromCache]);

  useEffect(() => {
    if (location.pathname !== BUSINESS_BASE || overviewLoading) return;
    if (prefetchStartedRef.current) return;
    prefetchStartedRef.current = true;

    void (async () => {
      try {
        const cache = await prefetchPortfolioAnalytics(PORTFOLIO_PREFETCH_SEGMENTS);
        for (const [seg, payload] of cache) {
          portfolioCacheRef.current.set(seg, payload);
        }
        syncBookBaselineFromCache();
        const active = segmentRef.current;
        if (segmentRef.current === active && cache.has(active)) {
          setPortfolioAnalytics(clonePortfolioAnalytics(cache.get(active)!));
          setPortfolioLoading(false);
        }
      } catch {
        /* segment effect falls back to single-segment fetch */
      }
    })();
  }, [overviewLoading, location.pathname, syncBookBaselineFromCache]);

  useEffect(() => {
    if (location.pathname !== BUSINESS_BASE || overviewLoading) return;
    if (portfolioCacheRef.current.has("customers_all")) return;
    let cancelled = false;
    void fetchPortfolioAnalytics("customers_all").then((raw) => {
      if (cancelled) return;
      const data = clonePortfolioAnalytics(raw);
      portfolioCacheRef.current.set("customers_all", data);
      setBookBaseline(data);
    });
    return () => {
      cancelled = true;
    };
  }, [overviewLoading, location.pathname]);

  const setSegment = (next: CustomerSegment) => {
    if (!applySegmentFromCache(next)) {
      setPortfolioAnalytics((prev) =>
        portfolioAnalyticsMatchesSegment(prev, next) ? prev : null,
      );
      setPortfolioLoading(true);
    }
    setSearchParams((prev) => patchBusinessSegment(prev, next), { replace: true });
  };

  if (overviewLoading && !overview) {
    return (
      <>
        <Breadcrumbs items={[{ label: t("nav.business.title") }]} />
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
      {!mobileFocus && <Breadcrumbs items={[{ label: t("nav.business.title") }]} />}
      <section className="panel">
        {!mobileFocus && (
        <DomainFilterGrid
          overview={overview}
          segment={segment}
          onSelect={setSegment}
          helperText={t("business.domainFilter.helperAnalytics")}
        />
        )}
        <PortfolioAnalyticsSection
          data={
            portfolioAnalyticsMatchesSegment(portfolioAnalytics, segment)
              ? portfolioAnalytics
              : null
          }
          bookBaseline={bookBaseline}
          loading={portfolioLoading || !portfolioAnalyticsMatchesSegment(portfolioAnalytics, segment)}
          refreshing={false}
          cohortLabel={activeDomain?.domain ?? null}
          segment={segment}
          minimal={mobileFocus}
          chartInteractive={!mobileFocus}
        />
      </section>
    </>
  );
}
