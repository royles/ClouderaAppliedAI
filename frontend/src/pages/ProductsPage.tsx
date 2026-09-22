import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";
import {
  CustomerSegment,
  fetchProductCatalog,
  ProductCatalog,
  ProductCatalogItem,
} from "../api";
import { CUSTOMER_BASE } from "../appRoutes";
import Breadcrumbs from "../components/Breadcrumbs";
import { cohortSearchString } from "../cohortQuery";
import { CUSTOMER_SEGMENTS } from "../customerSegments";
import { parseProductsSearch, patchProductsParams } from "../productsQuery";
import { cohortSegmentLabel } from "../i18n/segments";
import { productClassLabel } from "../i18n/productClasses";
import { formatNumber } from "../localeFormat";
import { useMobileFocus } from "../mobileUxContext";

function heatLevel(count: number, max: number): "low" | "med" | "high" | "peak" {
  if (max <= 0 || count <= 0) return "low";
  const ratio = count / max;
  if (ratio >= 0.85) return "peak";
  if (ratio >= 0.55) return "high";
  if (ratio >= 0.3) return "med";
  return "low";
}

function ProductCard({
  product,
  maxCustomers,
  segment,
  city,
}: {
  product: ProductCatalogItem;
  maxCustomers: number;
  segment: CustomerSegment;
  city: string | null;
}) {
  const { t } = useTranslation();
  const level = heatLevel(product.customer_count, maxCustomers);
  const href = `${CUSTOMER_BASE}${cohortSearchString({
    segment,
    policyTypeCode: product.policy_type_code,
    city,
    page: 1,
  })}`;

  return (
    <Link
      to={href}
      className={`product-heatmap-card product-heat-${level}`}
      title={t("products.customersCount", { count: formatNumber(product.customer_count) })}
    >
      <span className="product-heatmap-count">{formatNumber(product.customer_count)}</span>
      <span className="product-heatmap-name">{product.policy_type_desc}</span>
      <span className="muted small product-heatmap-sub">
        {t("products.activePoliciesCount", {
          count: formatNumber(product.active_policy_count),
        })}
      </span>
    </Link>
  );
}

export default function ProductsPage() {
  const { t } = useTranslation();
  const mobileFocus = useMobileFocus();
  const [searchParams, setSearchParams] = useSearchParams();
  const { segment, city } = useMemo(
    () => parseProductsSearch(searchParams),
    [searchParams],
  );

  const [catalog, setCatalog] = useState<ProductCatalog | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    void fetchProductCatalog({ segment, city })
      .then((c) => {
        if (!cancelled) {
          setCatalog(c);
          setError(null);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : t("errors.productsLoadFailed"));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [segment, city]);

  const maxCustomers = catalog?.max_customer_count ?? 0;
  const cityOptions = catalog?.city_options ?? [];

  const cohortLabel = cohortSegmentLabel(t, segment);
  const filtersActive = segment !== "customers_all" || Boolean(city);

  const legend = useMemo(
    () => [
      { level: "peak", label: t("products.legend.highest") },
      { level: "high", label: t("products.legend.strong") },
      { level: "med", label: t("products.legend.moderate") },
      { level: "low", label: t("products.legend.lighter") },
    ],
    [t],
  );

  const clearFilters = () => {
    setSearchParams(new URLSearchParams(), { replace: true });
  };

  const flatProducts = catalog
    ? catalog.classes.flatMap((g) =>
        g.products.map((p) => ({
          ...p,
          class_key: g.class_key,
          class_label: g.class_label,
        })),
      )
    : [];
  flatProducts.sort((a, b) => b.customer_count - a.customer_count);

  const classLabel = (classKey: string, fallback: string) =>
    productClassLabel(t, classKey, fallback);

  return (
    <>
      {!mobileFocus && <Breadcrumbs items={[{ label: t("nav.products.title") }]} />}
      <section className="panel">
        <div className="panel-head">
          <div>
            <h1 className="section-title">
              {mobileFocus ? t("products.mobile.title") : t("nav.products.title")}
            </h1>
            {!mobileFocus && (
            <p className="muted small">{t("products.lede")}</p>
            )}
            {filtersActive && (
              <p className="filter-banner">
                {t("products.filter.banner", {
                  segment: cohortLabel,
                  city: city ? ` · ${city}` : "",
                })}{" "}
                <button type="button" className="link-btn" onClick={clearFilters}>
                  {t("products.filter.clear")}
                </button>
              </p>
            )}
          </div>
          {!mobileFocus && (
          <ul className="product-heatmap-legend" aria-label={t("products.a11y.legend")}>
            {legend.map((item) => (
              <li key={item.level}>
                <span className={`product-heat-swatch product-heat-${item.level}`} />
                {item.label}
              </li>
            ))}
          </ul>
          )}
        </div>

        {!mobileFocus && (
        <div className="toolbar product-filter-toolbar">
          <div className="toolbar-item">
            <label htmlFor="product-cohort">{t("products.filters.cohort")}</label>
            <select
              id="product-cohort"
              className="control"
              value={segment}
              onChange={(e) =>
                setSearchParams(
                  (prev) =>
                    patchProductsParams(prev, {
                      segment: e.target.value as CustomerSegment,
                    }),
                  { replace: true },
                )
              }
            >
              {CUSTOMER_SEGMENTS.map((value) => (
                <option key={value} value={value}>
                  {cohortSegmentLabel(t, value)}
                </option>
              ))}
            </select>
          </div>
          <div className="toolbar-item">
            <label htmlFor="product-city">{t("products.filters.city")}</label>
            <select
              id="product-city"
              className="control"
              value={city ?? ""}
              onChange={(e) =>
                setSearchParams(
                  (prev) =>
                    patchProductsParams(prev, {
                      city: e.target.value ? e.target.value : null,
                    }),
                  { replace: true },
                )
              }
            >
              <option value="">{t("products.filters.allCities")}</option>
              {cityOptions.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>
        </div>
        )}

        {loading && <p className="muted small">{t("products.loading")}</p>}
        {error && <p className="error">{error}</p>}
        {mobileFocus && catalog && (
          <ul className="mobile-product-list">
            {flatProducts.slice(0, 12).map((product) => (
              <li key={product.policy_type_code}>
                <Link
                  to={`${CUSTOMER_BASE}${cohortSearchString({
                    segment,
                    policyTypeCode: product.policy_type_code,
                    city,
                    page: 1,
                  })}`}
                  className="mobile-product-row"
                >
                  <span className="mobile-product-name">{product.policy_type_desc}</span>
                  <span className="muted small">
                    {classLabel(product.class_key ?? "", product.class_label)}
                  </span>
                  <strong>{t("products.customersCount", { count: formatNumber(product.customer_count) })}</strong>
                </Link>
              </li>
            ))}
          </ul>
        )}
        {!mobileFocus && catalog &&
          catalog.classes.map((group) => (
            <div key={group.class_key} className="product-class-block">
              <div className="product-class-head">
                <h2 className="subsection-title">
                  {classLabel(group.class_key, group.class_label)}
                </h2>
                <span className="muted small">
                  {t("products.classStats", {
                    customers: formatNumber(group.customer_count),
                    policies: formatNumber(group.policy_count),
                  })}
                </span>
              </div>
              <div className="product-heatmap-grid">
                {group.products.map((product) => (
                  <ProductCard
                    key={product.policy_type_code}
                    product={product}
                    maxCustomers={maxCustomers}
                    segment={segment}
                    city={city}
                  />
                ))}
              </div>
            </div>
          ))}
        {!loading && !error && catalog?.classes.length === 0 && (
          <p className="muted small">{t("products.empty")}</p>
        )}
      </section>
    </>
  );
}
