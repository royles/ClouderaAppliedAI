import { useTranslation } from "react-i18next";
import { useState } from "react";
import AdminAppearancePanel from "./AdminAppearancePanel";
import AdminDataSourcePanel from "./AdminDataSourcePanel";
import AdminKpiBenchmarksPanel from "./AdminKpiBenchmarksPanel";
import AdminLlmProviderPanel from "./AdminLlmProviderPanel";

type ConfigTab = "warehouse" | "llm" | "kpi_benchmarks" | "appearance";

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
          aria-selected={tab === "llm"}
          className={`admin-config-tab${tab === "llm" ? " is-active" : ""}`}
          onClick={() => setTab("llm")}
        >
          {t("admin.config.tabs.llm")}
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
        <button
          type="button"
          role="tab"
          aria-selected={tab === "appearance"}
          className={`admin-config-tab${tab === "appearance" ? " is-active" : ""}`}
          onClick={() => setTab("appearance")}
        >
          {t("admin.config.tabs.appearance")}
        </button>
      </div>
      <div className="admin-config-tab-panel" role="tabpanel">
        {tab === "warehouse" && <AdminDataSourcePanel layout="embedded" />}
        {tab === "llm" && <AdminLlmProviderPanel />}
        {tab === "kpi_benchmarks" && <AdminKpiBenchmarksPanel />}
        {tab === "appearance" && <AdminAppearancePanel />}
      </div>
    </section>
  );
}
