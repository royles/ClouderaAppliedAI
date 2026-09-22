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
import CohortComparisonPanel, {
  compareDomainLabel,
} from "../components/CohortComparisonPanel";
import DomainFilterGrid from "../components/DomainFilterGrid";
import PortfolioAnalyticsSection from "../components/PortfolioAnalyticsSection";
import {
  parseBusinessCompareSegment,
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

const COMPARE_OPTIONS: CustomerSegment[] = [
  "customers_all",
  "with_policies",
  "with_foreclosures",
  "with_investments",
  "with_insurance_status",
  "with_market_products",
];

export default function DashboardPage() {
  const { t } = useTranslation();
  const mobileFocus = useMobileFocus();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const segment = useMemo(() => parseBusinessSegment(searchParams), [searchParams]);
  const compareSegment = useMemo(
    () => parseBusinessCompareSegment(searchParams),
    [searchParams],
  );

  const [overview, setOverview] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [portfolioAnalytics, setPortfolioAnalytics] = useState<PortfolioAnalytics | null>(
    null,
  );
  const [compareAnalytics, setCompareAnalytics] = useState<PortfolioAnalytics | null>(null);
  const [portfolioLoading, setPortfolioLoading] = useState(true);
  const [compareLoading, setCompareLoading] = useState(false);
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
    if (!compareSegment || compareSegment === segment) {
      setCompareAnalytics(null);
      setCompareLoading(false);
      return;
    }

    const cached = portfolioCacheRef.current.get(compareSegment);
    if (cached && cached.segment === compareSegment) {
      setCompareAnalytics(clonePortfolioAnalytics(cached));
      setCompareLoading(false);
      return;
    }

    let cancelled = false;
    setCompareLoading(true);
    void fetchPortfolioAnalytics(compareSegment)
      .then((raw) => {
        if (cancelled) return;
        const data = clonePortfolioAnalytics(raw);
        portfolioCacheRef.current.set(compareSegment, data);
        setCompareAnalytics(data);
      })
      .catch(() => {
        if (!cancelled) setCompareAnalytics(null);
      })
      .finally(() => {
        if (!cancelled) setCompareLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [compareSegment, segment, overviewLoading, location.pathname]);

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
        const cmp = parseBusinessCompareSegment(
          new URLSearchParams(window.location.search),
        );
        if (cmp && cache.has(cmp)) {
          setCompareAnalytics(clonePortfolioAnalytics(cache.get(cmp)!));
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

  const setCompare = (next: CustomerSegment | "") => {
    const compare =
      next === "" || next === "customers_all" || next === segment ? null : next;
    setSearchParams((prev) => patchBusinessSegment(prev, segment, compare), {
      replace: true,
    });
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

  const primaryLabel = compareDomainLabel(overview, segment);
  const compareLabel = compareSegment
    ? compareDomainLabel(overview, compareSegment)
    : null;

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
        {!mobileFocus && (
        <div className="cohort-compare-toolbar">
          <label className="cohort-compare-label" htmlFor="cohort-compare-select">
            {t("business.compare.label")}
          </label>
          <select
            id="cohort-compare-select"
            className="cohort-compare-select"
            value={compareSegment ?? ""}
            onChange={(e) => setCompare(e.target.value as CustomerSegment | "")}
          >
            <option value="">{t("business.compare.none")}</option>
            {COMPARE_OPTIONS.filter((s) => s !== segment).map((s) => (
              <option key={s} value={s}>
                {compareDomainLabel(overview, s)}
              </option>
            ))}
          </select>
        </div>
        )}
        {!mobileFocus && compareSegment &&
          compareSegment !== segment &&
          compareAnalytics &&
          portfolioAnalytics &&
          !compareLoading && (
            <CohortComparisonPanel
              primaryLabel={primaryLabel}
              compareLabel={compareLabel ?? compareSegment}
              primary={portfolioAnalytics}
              compare={compareAnalytics}
              primarySegment={segment}
              compareSegment={compareSegment}
            />
          )}
        {!mobileFocus && compareLoading && compareSegment && (
          <p className="muted small cohort-compare-loading">{t("business.compare.loading")}</p>
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
