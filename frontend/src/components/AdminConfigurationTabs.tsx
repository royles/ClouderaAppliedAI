import { useState } from "react";
import AdminDataSourcePanel from "./AdminDataSourcePanel";
import AdminKpiBenchmarksPanel from "./AdminKpiBenchmarksPanel";

type ConfigTab = "warehouse" | "kpi_benchmarks";

export default function AdminConfigurationTabs() {
  const [tab, setTab] = useState<ConfigTab>("warehouse");

  return (
    <section className="panel admin-config-tabs-panel">
      <h2>Configuration</h2>
      <p className="muted small">
        Warehouse connectivity and business KPI objectives used on The business page.
      </p>
      <div className="admin-config-tabs" role="tablist" aria-label="Admin configuration">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "warehouse"}
          className={`admin-config-tab${tab === "warehouse" ? " is-active" : ""}`}
          onClick={() => setTab("warehouse")}
        >
          Warehouse backend
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "kpi_benchmarks"}
          className={`admin-config-tab${tab === "kpi_benchmarks" ? " is-active" : ""}`}
          onClick={() => setTab("kpi_benchmarks")}
        >
          Business KPI benchmarks
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
