import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  fetchKpiBenchmarks,
  KpiBenchmark,
  updateKpiBenchmarks,
} from "../api";
import { formatMoneyIls } from "../formatMoney";

type RowState = KpiBenchmark & { targetInput: string; amberInput: string };

function formatTargetPreview(row: KpiBenchmark, raw: string): string {
  const parsed = parseFloat(raw);
  if (!raw.trim() || Number.isNaN(parsed) || parsed <= 0) {
    return "Auto (from portfolio)";
  }
  if (row.unit_kind === "money") return formatMoneyIls(parsed);
  if (row.unit_kind === "integer") return parsed.toLocaleString();
  if (row.unit_kind === "ratio") return `${(parsed * 100).toFixed(1)}%`;
  if (row.unit_kind === "percent") return `${parsed}%`;
  return String(parsed);
}

function rowToState(row: KpiBenchmark): RowState {
  return {
    ...row,
    targetInput:
      row.target_value != null && row.target_value > 0 ? String(row.target_value) : "",
    amberInput: String(row.amber_threshold),
  };
}

function amberHelp(direction: string): string {
  if (direction === "lower") {
    return "Amber up to this multiple of the objective (e.g. 1.2 = 20% over limit).";
  }
  return "Amber when at least this fraction of the objective (e.g. 0.85 = 85%).";
}

export default function AdminKpiBenchmarksPanel() {
  const { t } = useTranslation();
  const [rows, setRows] = useState<RowState[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedNote, setSavedNote] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchKpiBenchmarks();
      setRows(data.benchmarks.map(rowToState));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load KPI benchmarks");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const patchRow = (key: string, patch: Partial<RowState>) => {
    setRows((prev) => prev.map((r) => (r.kpi_key === key ? { ...r, ...patch } : r)));
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSavedNote(null);
    try {
      const payload = rows.map((r) => {
        const targetRaw = r.targetInput.trim();
        const amberRaw = r.amberInput.trim();
        return {
          kpi_key: r.kpi_key,
          display_label: r.display_label,
          description: r.description ?? "",
          enabled: r.enabled,
          target_value:
            targetRaw === "" ? null : Number.isNaN(parseFloat(targetRaw)) ? null : parseFloat(targetRaw),
          amber_threshold: Number.isNaN(parseFloat(amberRaw)) ? r.amber_threshold : parseFloat(amberRaw),
        };
      });
      const updated = await updateKpiBenchmarks(payload);
      setRows(updated.benchmarks.map(rowToState));
      setSavedNote(t("admin.kpiBenchmarks.saved"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="muted small">{t("admin.loading")}</p>;
  }

  return (
    <div className="admin-kpi-benchmarks">
      <p className="muted small">{t("admin.kpiBenchmarks.lede")}</p>
      {savedNote && <p className="admin-datasource-success">{savedNote}</p>}
      {error && <p className="error">{error}</p>}

      <form onSubmit={onSubmit}>
        <div className="table-wrap">
          <table className="data-table admin-kpi-table">
            <thead>
              <tr>
                <th scope="col" className="visually-hidden">
                  Enabled
                </th>
                <th>{t("admin.kpiBenchmarks.columns.kpi")}</th>
                <th>{t("admin.kpiBenchmarks.columns.target")}</th>
                <th>{t("admin.kpiBenchmarks.columns.unit")}</th>
                <th>{t("admin.kpiBenchmarks.columns.direction")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.kpi_key}>
                  <td>
                    <input
                      type="checkbox"
                      checked={row.enabled}
                      onChange={(e) => patchRow(row.kpi_key, { enabled: e.target.checked })}
                      aria-label={`Enable ${row.display_label}`}
                    />
                  </td>
                  <td>
                    <strong>{row.display_label}</strong>
                    <span className="muted small admin-kpi-key">{row.kpi_key}</span>
                    {row.description ? (
                      <span className="muted small admin-kpi-desc">{row.description}</span>
                    ) : null}
                  </td>
                  <td>
                    <input
                      type="text"
                      className="admin-kpi-input"
                      value={row.targetInput}
                      onChange={(e) => patchRow(row.kpi_key, { targetInput: e.target.value })}
                      placeholder={t("admin.kpiBenchmarks.placeholderAuto")}
                    />
                    <span className="muted small">
                      Preview: {formatTargetPreview(row, row.targetInput)}
                    </span>
                  </td>
                  <td>
                    <input
                      type="text"
                      className="admin-kpi-input admin-kpi-input-narrow"
                      value={row.amberInput}
                      onChange={(e) => patchRow(row.kpi_key, { amberInput: e.target.value })}
                    />
                    <span className="muted small">{amberHelp(row.direction)}</span>
                  </td>
                  <td>
                    <code>{row.direction}</code>
                    <span className="muted small">{row.unit_kind}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="admin-datasource-actions">
          <button type="submit" className="btn primary" disabled={saving}>
            {saving ? t("admin.kpiBenchmarks.saving") : t("admin.kpiBenchmarks.save")}
          </button>
        </div>
      </form>
    </div>
  );
}
