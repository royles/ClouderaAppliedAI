import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  DataSourceConfig,
  fetchDataSourceConfig,
  testDataSourceConnection,
  updateDataSourceConfig,
} from "../api";

type BackendChoice = "sqlite" | "cdw_jdbc" | "iceberg";

type FormState = {
  backend_type: BackendChoice;
  sqlite_path: string;
  jdbc_url: string;
  jdbc_user: string;
  jdbc_password: string;
  clear_jdbc_password: boolean;
  iceberg_catalog: string;
  iceberg_namespace: string;
  iceberg_rest_uri: string;
  trino_host: string;
  trino_port: string;
  trino_catalog: string;
  trino_schema: string;
  trino_user: string;
  trino_password: string;
  clear_trino_password: boolean;
  trino_use_ssl: boolean;
};

function configToForm(cfg: DataSourceConfig): FormState {
  return {
    backend_type: (cfg.backend_type as BackendChoice) || "sqlite",
    sqlite_path: cfg.sqlite_path ?? "",
    jdbc_url: cfg.jdbc_url ?? "",
    jdbc_user: cfg.jdbc_user ?? "",
    jdbc_password: "",
    clear_jdbc_password: false,
    iceberg_catalog: cfg.iceberg_catalog ?? "",
    iceberg_namespace: cfg.iceberg_namespace ?? "",
    iceberg_rest_uri: cfg.iceberg_rest_uri ?? "",
    trino_host: cfg.trino_host ?? "",
    trino_port: cfg.trino_port != null ? String(cfg.trino_port) : "443",
    trino_catalog: cfg.trino_catalog ?? "",
    trino_schema: cfg.trino_schema ?? "",
    trino_user: cfg.trino_user ?? "",
    trino_password: "",
    clear_trino_password: false,
    trino_use_ssl: cfg.trino_use_ssl ?? true,
  };
}

function buildUpdatePayload(form: FormState): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    backend_type: form.backend_type,
    trino_use_ssl: form.trino_use_ssl,
  };
  if (form.backend_type === "sqlite") {
    payload.sqlite_path = form.sqlite_path.trim() || null;
  }
  if (form.backend_type === "cdw_jdbc" || form.backend_type === "iceberg") {
    payload.jdbc_url = form.jdbc_url.trim() || null;
    payload.jdbc_user = form.jdbc_user.trim() || null;
    payload.trino_host = form.trino_host.trim() || null;
    const port = parseInt(form.trino_port, 10);
    payload.trino_port = Number.isFinite(port) ? port : 443;
    payload.trino_catalog = form.trino_catalog.trim() || null;
    payload.trino_schema = form.trino_schema.trim() || null;
    payload.trino_user = form.trino_user.trim() || null;
    if (form.jdbc_password.trim()) {
      payload.jdbc_password = form.jdbc_password;
    }
    if (form.trino_password.trim()) {
      payload.trino_password = form.trino_password;
    }
    if (form.clear_jdbc_password) payload.clear_jdbc_password = true;
    if (form.clear_trino_password) payload.clear_trino_password = true;
  }
  if (form.backend_type === "iceberg") {
    payload.iceberg_catalog = form.iceberg_catalog.trim() || null;
    payload.iceberg_namespace = form.iceberg_namespace.trim() || null;
    payload.iceberg_rest_uri = form.iceberg_rest_uri.trim() || null;
  }
  return payload;
}

export default function AdminDataSourcePanel() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedNote, setSavedNote] = useState<string | null>(null);
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [meta, setMeta] = useState<DataSourceConfig | null>(null);
  const [form, setForm] = useState<FormState | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const cfg = await fetchDataSourceConfig();
      setMeta(cfg);
      setForm(configToForm(cfg));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data source settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const patch = (partial: Partial<FormState>) => {
    setForm((prev) => (prev ? { ...prev, ...partial } : prev));
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    setError(null);
    setTestMessage(null);
    try {
      const updated = await updateDataSourceConfig(buildUpdatePayload(form));
      setMeta(updated);
      setForm(configToForm(updated));
      setSavedNote("Settings saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const onTest = async () => {
    if (!form) return;
    setTesting(true);
    setTestMessage(null);
    setError(null);
    try {
      const result = await testDataSourceConnection(buildUpdatePayload(form));
      setTestMessage(
        `${result.ok ? "OK" : "Failed"}: ${result.message}${result.detail ? ` — ${result.detail}` : ""}`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection test failed");
    } finally {
      setTesting(false);
    }
  };

  if (loading || !form) {
    return (
      <section className="panel">
        <h2>Warehouse backend</h2>
        <p className="muted small">Loading backend configuration…</p>
      </section>
    );
  }

  return (
    <section className="panel admin-datasource">
      <h2>Warehouse backend</h2>
      <p className="muted small">
        Choose where Customer 360 reads warehouse data. Admin settings are always stored in the
        local control database; API routes use SQLite until CDW or Iceberg routing is enabled.
      </p>
      {meta?.api_routing_note && (
        <p className="muted small admin-datasource-note">{meta.api_routing_note}</p>
      )}
      {savedNote && <p className="admin-datasource-success">{savedNote}</p>}
      {error && <p className="error">{error}</p>}
      {testMessage && <p className="admin-datasource-test">{testMessage}</p>}

      <form className="admin-datasource-form" onSubmit={onSubmit}>
        <fieldset>
          <legend>Backend type</legend>
          <label className="admin-datasource-radio">
            <input
              type="radio"
              name="backend_type"
              checked={form.backend_type === "sqlite"}
              onChange={() => patch({ backend_type: "sqlite" })}
            />
            SQLite (default)
          </label>
          <label className="admin-datasource-radio">
            <input
              type="radio"
              name="backend_type"
              checked={form.backend_type === "cdw_jdbc"}
              onChange={() => patch({ backend_type: "cdw_jdbc" })}
            />
            Cloudera Data Warehouse (JDBC)
          </label>
          <label className="admin-datasource-radio">
            <input
              type="radio"
              name="backend_type"
              checked={form.backend_type === "iceberg"}
              onChange={() => patch({ backend_type: "iceberg" })}
            />
            Lakehouse (Iceberg)
          </label>
        </fieldset>

        {form.backend_type === "sqlite" && (
          <label className="admin-datasource-field">
            <span>SQLite file path</span>
            <input
              type="text"
              value={form.sqlite_path}
              onChange={(e) => patch({ sqlite_path: e.target.value })}
              placeholder="data/customer360.db"
            />
          </label>
        )}

        {(form.backend_type === "cdw_jdbc" || form.backend_type === "iceberg") && (
          <>
            <label className="admin-datasource-field">
              <span>JDBC URL</span>
              <input
                type="text"
                value={form.jdbc_url}
                onChange={(e) => patch({ jdbc_url: e.target.value })}
                placeholder="jdbc:trino://host:443/hive/default"
              />
            </label>
            <div className="admin-datasource-row">
              <label className="admin-datasource-field">
                <span>CDW host (optional if JDBC URL set)</span>
                <input
                  type="text"
                  value={form.trino_host}
                  onChange={(e) => patch({ trino_host: e.target.value })}
                />
              </label>
              <label className="admin-datasource-field admin-datasource-field-narrow">
                <span>Port</span>
                <input
                  type="text"
                  value={form.trino_port}
                  onChange={(e) => patch({ trino_port: e.target.value })}
                />
              </label>
            </div>
            <div className="admin-datasource-row">
              <label className="admin-datasource-field">
                <span>Catalog</span>
                <input
                  type="text"
                  value={form.trino_catalog}
                  onChange={(e) => patch({ trino_catalog: e.target.value })}
                  placeholder="hive"
                />
              </label>
              <label className="admin-datasource-field">
                <span>Schema</span>
                <input
                  type="text"
                  value={form.trino_schema}
                  onChange={(e) => patch({ trino_schema: e.target.value })}
                  placeholder="default"
                />
              </label>
            </div>
            <div className="admin-datasource-row">
              <label className="admin-datasource-field">
                <span>User</span>
                <input
                  type="text"
                  value={form.trino_user || form.jdbc_user}
                  onChange={(e) => patch({ trino_user: e.target.value, jdbc_user: e.target.value })}
                />
              </label>
              <label className="admin-datasource-field">
                <span>Password</span>
                <input
                  type="password"
                  value={form.trino_password || form.jdbc_password}
                  onChange={(e) =>
                    patch({ trino_password: e.target.value, jdbc_password: e.target.value })
                  }
                  placeholder={meta?.jdbc_password_set ? "•••••• (unchanged if empty)" : ""}
                  autoComplete="new-password"
                />
              </label>
            </div>
            <label className="admin-datasource-checkbox">
              <input
                type="checkbox"
                checked={form.trino_use_ssl}
                onChange={(e) => patch({ trino_use_ssl: e.target.checked })}
              />
              Use TLS for Trino HTTP test
            </label>
          </>
        )}

        {form.backend_type === "iceberg" && (
          <>
            <label className="admin-datasource-field">
              <span>Iceberg REST catalog URI</span>
              <input
                type="text"
                value={form.iceberg_rest_uri}
                onChange={(e) => patch({ iceberg_rest_uri: e.target.value })}
                placeholder="https://catalog.example.com/iceberg"
              />
            </label>
            <div className="admin-datasource-row">
              <label className="admin-datasource-field">
                <span>Catalog name</span>
                <input
                  type="text"
                  value={form.iceberg_catalog}
                  onChange={(e) => patch({ iceberg_catalog: e.target.value })}
                />
              </label>
              <label className="admin-datasource-field">
                <span>Namespace</span>
                <input
                  type="text"
                  value={form.iceberg_namespace}
                  onChange={(e) => patch({ iceberg_namespace: e.target.value })}
                />
              </label>
            </div>
          </>
        )}

        <div className="admin-datasource-actions">
          <button type="button" className="btn secondary" disabled={testing} onClick={() => void onTest()}>
            {testing ? "Testing…" : "Test connection"}
          </button>
          <button type="submit" className="btn primary" disabled={saving}>
            {saving ? "Saving…" : "Save backend settings"}
          </button>
        </div>
        {meta?.updated_at && (
          <p className="muted small">Last updated {new Date(meta.updated_at).toLocaleString()}</p>
        )}
      </form>
    </section>
  );
}
