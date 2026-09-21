import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProductCatalog, ProductCatalog, ProductCatalogItem } from "../api";
import { CUSTOMER_BASE } from "../appRoutes";
import Breadcrumbs from "../components/Breadcrumbs";
import { cohortSearchString } from "../cohortQuery";

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
}: {
  product: ProductCatalogItem;
  maxCustomers: number;
}) {
  const level = heatLevel(product.customer_count, maxCustomers);
  const href = `${CUSTOMER_BASE}${cohortSearchString({
    segment: "customers_all",
    policyTypeCode: product.policy_type_code,
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
  const [catalog, setCatalog] = useState<ProductCatalog | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    void fetchProductCatalog()
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
  }, []);

  const maxCustomers = catalog?.max_customer_count ?? 0;

  const legend = useMemo(
    () => [
      { level: "peak", label: "Highest uptake" },
      { level: "high", label: "Strong" },
      { level: "med", label: "Moderate" },
      { level: "low", label: "Lighter" },
    ],
    [],
  );

  return (
    <>
      <Breadcrumbs items={[{ label: "Products" }]} />
      <section className="panel">
        <div className="panel-head">
          <div>
            <h1 className="section-title">Products</h1>
            <p className="muted small">
              Policy products grouped by class. Darker cards hold more customers — click to open
              the customer list for that product.
            </p>
          </div>
          <ul className="product-heatmap-legend" aria-label="Customer count intensity">
            {legend.map((item) => (
              <li key={item.level}>
                <span className={`product-heat-swatch product-heat-${item.level}`} />
                {item.label}
              </li>
            ))}
          </ul>
        </div>
        {loading && <p className="muted small">Loading product catalog…</p>}
        {error && <p className="error">{error}</p>}
        {catalog &&
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
