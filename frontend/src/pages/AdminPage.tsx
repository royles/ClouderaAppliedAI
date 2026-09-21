import { useEffect, useState } from "react";
import AdminDataSourcePanel from "../components/AdminDataSourcePanel";
import Breadcrumbs from "../components/Breadcrumbs";
import { fetchWarehouseAdmin, WarehouseAdmin } from "../api";

function formatBytes(n: number) {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)} GB`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} MB`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)} KB`;
  return `${n} B`;
}

function formatWhen(iso: string | null | undefined) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function statusClass(status: string) {
  if (status === "critical") return "quality-badge quality-critical";
  if (status === "warn") return "quality-badge quality-warn";
  return "quality-badge quality-ok";
}

export default function AdminPage() {
  const [data, setData] = useState<WarehouseAdmin | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const admin = await fetchWarehouseAdmin();
        if (!cancelled) {
          setData(admin);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load admin data");
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const qualityIssues =
    data?.quality_checks.filter((c) => c.status !== "ok").length ?? 0;
  const healthIssues =
    data?.health_checks.filter((c) => c.status !== "ok").length ?? 0;

  return (
    <>
      <Breadcrumbs items={[{ label: "Data & admin" }]} />
      <section className="panel">
        <h1>Warehouse &amp; data admin</h1>
        <p className="muted small">
          Table inventory, load timestamps, DDS relationships, and completeness checks for
          the Customer 360 SQLite warehouse.
        </p>
      </section>

      {loading && (
        <section className="panel">
          <p className="muted">Loading admin metadata…</p>
        </section>
      )}
      {error && (
        <section className="panel">
          <p className="error">{error}</p>
        </section>
      )}

      <AdminDataSourcePanel />

      {data && (
        <>
          <section className="panel">
            <h2>System health</h2>
            <p className="muted small">
              Runtime checks for API, warehouse database, Bedrock, and churn scoring.
            </p>
            <ul className="admin-health-grid">
              {data.health_checks.map((check) => (
                <li
                  key={check.id}
                  className={`admin-health-card admin-health-${check.status}`}
                >
                  <span className={statusClass(check.status)}>{check.status}</span>
                  <strong>{check.label}</strong>
                  <p className="muted small">{check.summary}</p>
                  {check.detail && (
                    <p className="muted small admin-health-detail">{check.detail}</p>
                  )}
                </li>
              ))}
            </ul>
            {healthIssues > 0 && (
              <p className="muted small admin-health-note">
                {healthIssues} check{healthIssues === 1 ? "" : "s"} need attention (warn or
                critical).
              </p>
            )}
          </section>

          <section className="panel">
            <div className="admin-kpi-grid">
              <div className="admin-kpi">
                <span className="label">Database file</span>
                <strong className="admin-kpi-mono">{formatBytes(data.database_size_bytes)}</strong>
                <span className="muted small admin-kpi-path">{data.database_path}</span>
              </div>
              <div className="admin-kpi">
                <span className="label">Warehouse last loaded</span>
                <strong>{formatWhen(data.warehouse_last_loaded_at)}</strong>
              </div>
              <div className="admin-kpi">
                <span className="label">Catalogued tables</span>
                <strong>{data.tables.length}</strong>
              </div>
              <div className="admin-kpi">
                <span className="label">Quality flags</span>
                <strong>{qualityIssues === 0 ? "None" : qualityIssues}</strong>
                <span className="muted small">Non-OK completeness checks</span>
              </div>
            </div>
          </section>

          <section className="panel">
            <h2>Table overview</h2>
            <p className="muted small">
              Row counts are live; last loaded reflects the most recent seed or cache refresh
              job that touched each table.
            </p>
            <div className="table-wrap">
              <table className="data-table admin-table">
                <thead>
                  <tr>
                    <th>Table</th>
                    <th>Layer</th>
                    <th>Domain</th>
                    <th>Rows</th>
                    <th>Last loaded</th>
                    <th>Source job</th>
                  </tr>
                </thead>
                <tbody>
                  {data.tables.map((t) => (
                    <tr key={t.table_name}>
                      <td>
                        <code className="admin-table-name">{t.table_name}</code>
                        <span className="muted small admin-table-desc">{t.description}</span>
                      </td>
                      <td>{t.layer}</td>
                      <td>{t.domain}</td>
                      <td>{t.table_exists ? t.row_count.toLocaleString() : "—"}</td>
                      <td>{formatWhen(t.last_loaded_at)}</td>
                      <td className="admin-job-cell">{t.last_source_job ?? t.load_job}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <h2>How tables relate</h2>
            <p className="muted small">
              Logical joins used by the Customer 360 API (warehouse DDS + application caches).
            </p>
            <div className="table-wrap">
              <table className="data-table admin-table-compact">
                <thead>
                  <tr>
                    <th>From</th>
                    <th>To</th>
                    <th>Join</th>
                    <th>Cardinality</th>
                  </tr>
                </thead>
                <tbody>
                  {data.relationships.map((r) => (
                    <tr key={`${r.from_table}-${r.to_table}-${r.label}`}>
                      <td>
                        <code>{r.from_table}</code>.{r.from_column}
                      </td>
                      <td>
                        <code>{r.to_table}</code>.{r.to_column}
                      </td>
                      <td>{r.label}</td>
                      <td>{r.cardinality}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <details className="admin-er-details">
              <summary>ER diagram (Mermaid)</summary>
              <pre className="admin-er-mermaid">{data.relationship_diagram}</pre>
            </details>
          </section>

          <section className="panel">
            <h2>Completeness &amp; quality</h2>
            <ul className="admin-quality-list">
              {data.quality_checks.map((check) => (
                <li key={check.id} className="admin-quality-item">
                  <span className={statusClass(check.status)}>{check.status}</span>
                  <div>
                    <strong>{check.label}</strong>
                    <p className="muted small">{check.summary}</p>
                    {check.detail && <p className="muted small">{check.detail}</p>}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </>
  );
}
