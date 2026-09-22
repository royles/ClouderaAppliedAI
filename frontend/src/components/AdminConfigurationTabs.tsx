import { useTranslation } from "react-i18next";
import { useState } from "react";
import AdminDataSourcePanel from "./AdminDataSourcePanel";
import AdminKpiBenchmarksPanel from "./AdminKpiBenchmarksPanel";

type ConfigTab = "warehouse" | "kpi_benchmarks";

export default function AdminConfigurationTabs() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<ConfigTab>("warehouse");

  return (
    <section className="panel admin-config-tabs-panel">
      <h2>{t("admin.config.title")}</h2>
      <p className="muted small">{t("admin.config.lede")}</p>
      <div className="admin-config-tabs" role="tablist" aria-label={t("admin.config.a11y")}>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "warehouse"}
          className={`admin-config-tab${tab === "warehouse" ? " is-active" : ""}`}
          onClick={() => setTab("warehouse")}
        >
          {t("admin.config.tabs.warehouse")}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "kpi_benchmarks"}
          className={`admin-config-tab${tab === "kpi_benchmarks" ? " is-active" : ""}`}
          onClick={() => setTab("kpi_benchmarks")}
        >
          {t("admin.config.tabs.kpiBenchmarks")}
        </button>
      </div>
      <div className="admin-config-tab-panel" role="tabpanel">
        {tab === "warehouse" ? (
          <AdminDataSourcePanel layout="embedded" />
        ) : (
          <AdminKpiBenchmarksPanel />
        )}
      </div>
    </section>
  );
}
