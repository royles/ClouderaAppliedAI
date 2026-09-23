import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import AdminConfigurationTabs from "../components/AdminConfigurationTabs";
import Breadcrumbs from "../components/Breadcrumbs";
import WarehouseSchemaDiagram from "../components/WarehouseSchemaDiagram";
import { fetchWarehouseAdmin, WarehouseAdmin } from "../api";
import {
  formatBytes,
  formatDateTime,
  formatNumber,
  qualityStatusClass,
} from "../localeFormat";
import { translateAdminCheck, translateCheckStatus } from "../i18n/adminChecks";
import { useMobileFocus } from "../mobileUxContext";

export default function AdminPage() {
  const { t } = useTranslation();
  const emDash = t("common.emDash");
  const mobileFocus = useMobileFocus();
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
          setError(e instanceof Error ? e.message : t("errors.adminLoadFailed"));
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

  if (mobileFocus) {
    return (
      <section className="panel">
        <h2 className="subsection-title">{t("admin.mobile.snapshotTitle")}</h2>
        {loading && <p className="muted small">{t("common.loading")}</p>}
        {error && <p className="error">{error}</p>}
        {data && (
          <>
            <p className="muted small">
              {data.database_path} · {formatBytes(data.database_size_bytes)}
            </p>
            <p>
              {t("admin.mobile.flags")} <strong>{qualityIssues}</strong> ·{" "}
              {t("admin.mobile.healthFlags")} <strong>{healthIssues}</strong>
            </p>
            <p className="muted small">{t("admin.mobile.desktopHint")}</p>
          </>
        )}
      </section>
    );
  }

  return (
    <>
      <Breadcrumbs items={[{ label: t("nav.admin.title") }]} />
      <section className="panel">
        <h1>{t("admin.title")}</h1>
        <p className="muted small">{t("admin.lede")}</p>
      </section>

      {loading && (
        <section className="panel">
          <p className="muted">{t("admin.loading")}</p>
        </section>
      )}
      {error && (
        <section className="panel">
          <p className="error">{error}</p>
        </section>
      )}

      <AdminConfigurationTabs />

      {data && (
        <>
          <section className="panel">
            <h2>{t("admin.health.title")}</h2>
            <p className="muted small">{t("admin.health.lede")}</p>
            <ul className="admin-health-grid">
              {data.health_checks.map((check) => {
                const copy = translateAdminCheck(t, check);
                return (
                <li
                  key={check.id}
                  className={`admin-health-card admin-health-${check.status}`}
                >
                  <span className={qualityStatusClass(check.status)}>
                    {translateCheckStatus(t, check.status)}
                  </span>
                  <strong>{copy.label}</strong>
                  <p className="muted small">{copy.summary}</p>
                  {copy.detail && (
                    <p className="muted small admin-health-detail">{copy.detail}</p>
                  )}
                </li>
              );
              })}
            </ul>
            {healthIssues > 0 && (
              <p className="muted small admin-health-note">
                {t("admin.health.attentionNote", { count: healthIssues })}
              </p>
            )}
          </section>

          <section className="panel">
            <div className="admin-kpi-grid">
              <div className="admin-kpi">
                <span className="label">{t("admin.kpi.databaseFile.label")}</span>
                <strong className="admin-kpi-mono">{formatBytes(data.database_size_bytes)}</strong>
                <span className="muted small admin-kpi-path">{data.database_path}</span>
              </div>
              <div className="admin-kpi">
                <span className="label">{t("admin.kpi.warehouseLoaded.label")}</span>
                <strong>{formatDateTime(data.warehouse_last_loaded_at, emDash)}</strong>
              </div>
              <div className="admin-kpi">
                <span className="label">{t("admin.kpi.cataloguedTables.label")}</span>
                <strong>{data.tables.length}</strong>
              </div>
              <div className="admin-kpi">
                <span className="label">{t("admin.kpi.qualityFlags.label")}</span>
                <strong>{qualityIssues === 0 ? t("common.none") : qualityIssues}</strong>
                <span className="muted small">{t("admin.kpi.qualityFlags.sub")}</span>
              </div>
            </div>
          </section>

          <section className="panel">
            <h2>{t("admin.tables.title")}</h2>
            <p className="muted small">{t("admin.tables.lede")}</p>
            <div className="table-wrap">
              <table className="data-table admin-table">
                <thead>
                  <tr>
                    <th>{t("admin.tables.columns.table")}</th>
                    <th>{t("admin.tables.columns.layer")}</th>
                    <th>{t("admin.tables.columns.domain")}</th>
                    <th>{t("admin.tables.columns.rows")}</th>
                    <th>{t("admin.tables.columns.lastLoaded")}</th>
                    <th>{t("admin.tables.columns.sourceJob")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.tables.map((row) => (
                    <tr key={row.table_name}>
                      <td>
                        <code className="admin-table-name">{row.table_name}</code>
                        <span className="muted small admin-table-desc">{row.description}</span>
                      </td>
                      <td>{row.layer}</td>
                      <td>{row.domain}</td>
                      <td>{row.table_exists ? formatNumber(row.row_count) : emDash}</td>
                      <td>{formatDateTime(row.last_loaded_at, emDash)}</td>
                      <td className="admin-job-cell">{row.last_source_job ?? row.load_job}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <h2>{t("admin.schema.title")}</h2>
            <p className="muted small">{t("admin.schema.lede")}</p>
            <div className="warehouse-schema-scroll">
              <WarehouseSchemaDiagram
                tables={data.tables}
                relationships={data.relationships}
              />
            </div>
            <details className="admin-er-details">
              <summary>{t("admin.schema.joinReference")}</summary>
              <div className="table-wrap">
                <table className="data-table admin-table-compact">
                  <thead>
                    <tr>
                      <th>{t("admin.schema.joinColumns.from")}</th>
                      <th>{t("admin.schema.joinColumns.to")}</th>
                      <th>{t("admin.schema.joinColumns.join")}</th>
                      <th>{t("admin.schema.joinColumns.cardinality")}</th>
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
            </details>
          </section>

          <section className="panel">
            <h2>{t("admin.quality.title")}</h2>
            <ul className="admin-quality-list">
              {data.quality_checks.map((check) => {
                const copy = translateAdminCheck(t, check);
                return (
                <li key={check.id} className="admin-quality-item">
                  <span className={qualityStatusClass(check.status)}>
                    {translateCheckStatus(t, check.status)}
                  </span>
                  <div>
                    <strong>{copy.label}</strong>
                    <p className="muted small">{copy.summary}</p>
                    {copy.detail && <p className="muted small">{copy.detail}</p>}
                  </div>
                </li>
              );
              })}
            </ul>
          </section>
        </>
      )}
    </>
  );
}
