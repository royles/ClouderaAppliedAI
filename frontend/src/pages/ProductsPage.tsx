import { useEffect, useMemo, useState } from "react";
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
import {
  parseProductsSearch,
  patchProductsParams,
  PRODUCT_COHORT_OPTIONS,
} from "../productsQuery";
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
      title={`${product.customer_count.toLocaleString()} customers`}
    >
      <span className="product-heatmap-count">{product.customer_count.toLocaleString()}</span>
      <span className="product-heatmap-name">{product.policy_type_desc}</span>
      <span className="muted small product-heatmap-sub">
        {product.active_policy_count.toLocaleString()} active policies
      </span>
    </Link>
  );
}

export default function ProductsPage() {
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
          setError(e instanceof Error ? e.message : "Failed to load products");
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

  const cohortLabel =
    PRODUCT_COHORT_OPTIONS.find((o) => o.value === segment)?.label ?? segment;
  const filtersActive = segment !== "customers_all" || Boolean(city);

  const legend = useMemo(
    () => [
      { level: "peak", label: "Highest uptake" },
      { level: "high", label: "Strong" },
      { level: "med", label: "Moderate" },
      { level: "low", label: "Lighter" },
    ],
    [],
  );

  const clearFilters = () => {
    setSearchParams(new URLSearchParams(), { replace: true });
  };

  const flatProducts = catalog
    ? catalog.classes.flatMap((g) =>
        g.products.map((p) => ({ ...p, class_label: g.class_label })),
      )
    : [];
  flatProducts.sort((a, b) => b.customer_count - a.customer_count);

  return (
    <>
      {!mobileFocus && <Breadcrumbs items={[{ label: "Products" }]} />}
      <section className="panel">
        <div className="panel-head">
          <div>
            <h1 className="section-title">{mobileFocus ? "Top products" : "Products"}</h1>
            {!mobileFocus && (
            <p className="muted small">
              Policy products grouped by class. Counts reflect the customer filters below — click a
              card to open the matching customer list.
            </p>
            )}
            {filtersActive && (
              <p className="filter-banner">
                Showing{" "}
                <strong>
                  {cohortLabel}
                  {city ? ` · ${city}` : ""}
                </strong>
                <button type="button" className="link-btn" onClick={clearFilters}>
                  Clear filters
                </button>
              </p>
            )}
          </div>
          {!mobileFocus && (
          <ul className="product-heatmap-legend" aria-label="Customer count intensity">
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
            <label htmlFor="product-cohort">Customer cohort</label>
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
              {PRODUCT_COHORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div className="toolbar-item">
            <label htmlFor="product-city">City</label>
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
              <option value="">All cities</option>
              {cityOptions.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>
        </div>
        )}

        {loading && <p className="muted small">Loading product catalog…</p>}
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
                  <span className="muted small">{product.class_label}</span>
                  <strong>{product.customer_count.toLocaleString()} customers</strong>
                </Link>
              </li>
            ))}
          </ul>
        )}
        {!mobileFocus && catalog &&
          catalog.classes.map((group) => (
            <div key={group.class_key} className="product-class-block">
              <div className="product-class-head">
                <h2 className="subsection-title">{group.class_label}</h2>
                <span className="muted small">
                  {group.customer_count.toLocaleString()} customers ·{" "}
                  {group.policy_count.toLocaleString()} policies
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
          <p className="muted small">No policy products in the warehouse.</p>
        )}
      </section>
    </>
  );
}
