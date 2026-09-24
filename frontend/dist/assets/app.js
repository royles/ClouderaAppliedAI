const fmtMoney = (n) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);

const statusPill = (text) => {
  const t = String(text || "").toLowerCase();
  let cls = "pill-muted";
  if (t.includes("effective") && !t.includes("in")) cls = "pill-ok";
  else if (t.includes("ineffective") || t.includes("critical") || t.includes("escalated")) cls = "pill-danger";
  else if (t.includes("partial") || t.includes("remediation") || t.includes("review")) cls = "pill-warn";
  return `<span class="pill ${cls}">${text}</span>`;
};

let searchDebounce;

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  return res.json();
}

function setTableLoading(tbodyId, colspan = 5) {
  const el = document.getElementById(tbodyId);
  if (el) el.innerHTML = `<tr><td colspan="${colspan}" class="empty">Loading…</td></tr>`;
}

function setListLoading(listId) {
  const el = document.getElementById(listId);
  if (el) el.innerHTML = `<li class="empty">Loading…</li>`;
}

function renderOverview(data) {
  const cards = [
    {
      label: "Total controls",
      value: data.control_count ?? 0,
      hint:
        data.golden_controls != null
          ? `${data.golden_controls} MVP golden controls`
          : "EU retail + commercial catalog",
    },
    {
      label: "Control health",
      value: `${data.control_health_pct}%`,
      hint: "Share of tested controls rated effective",
    },
    {
      label: "Open exceptions",
      value: data.open_exceptions,
      hint: "Requires remediation or validation",
    },
    {
      label: "Critical controls",
      value: data.critical_controls,
      hint: "Highest inherent risk tier",
    },
    {
      label: "New AML alerts",
      value: data.alert_status?.New ?? 0,
      hint: "Awaiting analyst review",
    },
  ];
  document.getElementById("overview-cards").innerHTML = cards
    .map(
      (c) => `
    <article class="metric-card">
      <p class="label">${c.label}</p>
      <p class="value">${c.value}</p>
      <p class="hint">${c.hint}</p>
    </article>`
    )
    .join("");
}

function renderDomainFilter(domains, selected = "") {
  const select = document.getElementById("domain-filter");
  if (!select) return;
  select.innerHTML =
    `<option value="">All domains</option>` +
    domains
      .map((d) => {
        const name = typeof d === "string" ? d : d.domain;
        const count = typeof d === "string" ? "" : ` (${d.controls})`;
        return `<option value="${name}">${name}${count}</option>`;
      })
      .join("");
  select.value = selected || "";
}

function renderControls(rows) {
  const body = document.getElementById("controls-body");
  const meta = document.getElementById("control-count-label");
  if (meta) meta.textContent = rows.length ? `${rows.length} shown` : "";
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="5" class="empty">No controls match your filters</td></tr>`;
    return;
  }
  body.innerHTML = rows
    .map(
      (r) => `<tr>
      <td><code>${r.control_code}</code>${r.is_golden ? " ★" : ""}</td>
      <td>${r.control_name}${r.similarity_key ? `<br /><small>${r.similarity_key}</small>` : ""}</td>
      <td>${r.domain}</td>
      <td>${statusPill(r.risk_tier)}</td>
      <td>${statusPill(r.latest_status || "Not Tested")}</td>
    </tr>`
    )
    .join("");
}

function renderAlerts(rows) {
  const body = document.getElementById("alerts-body");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="5" class="empty">No alerts at this risk threshold</td></tr>`;
    return;
  }
  body.innerHTML = rows
    .map(
      (r) => `<tr>
      <td>${r.alert_at}</td>
      <td>${r.alert_type}<br /><small>${r.unit_code} · ${r.channel}</small></td>
      <td>${fmtMoney(r.amount_usd)}</td>
      <td>${(r.risk_score * 100).toFixed(0)}%</td>
      <td>${statusPill(r.status)}</td>
    </tr>`
    )
    .join("");
}

function renderExceptions(rows) {
  const body = document.getElementById("exceptions-body");
  const open = rows.filter((r) => r.status !== "Closed");
  if (!open.length) {
    body.innerHTML = `<tr><td colspan="5" class="empty">No open exceptions</td></tr>`;
    return;
  }
  body.innerHTML = open
    .map(
      (r) => `<tr data-id="${r.exception_id}" data-status="${r.status}">
      <td>${r.title}<br /><small>${r.control_code} · ${r.unit_code}</small></td>
      <td>${statusPill(r.severity)}</td>
      <td>${r.due_date}</td>
      <td>${statusPill(r.status)}</td>
      <td>
        <button type="button" class="btn btn-ghost advance-btn" data-id="${r.exception_id}">Advance</button>
      </td>
    </tr>`
    )
    .join("");
}

function renderAudit(rows) {
  const list = document.getElementById("audit-list");
  if (!rows.length) {
    list.innerHTML = `<li class="empty">No audit events yet</li>`;
    return;
  }
  list.innerHTML = rows
    .map(
      (r) => `<li>
      <time>${r.event_at}</time>
      <strong>${r.action}</strong> — ${r.actor}
      <div>${r.detail}</div>
    </li>`
    )
    .join("");
}

const STATUS_FLOW = ["Open", "In Remediation", "Pending Validation", "Closed"];

async function advanceException(id) {
  const row = document.querySelector(`tr[data-id="${id}"]`);
  const current = row?.dataset.status;
  const idx = STATUS_FLOW.indexOf(current);
  const next = STATUS_FLOW[Math.min(idx + 1, STATUS_FLOW.length - 1)] || "In Remediation";
  await api(`/api/exceptions/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: next }),
  });
  await loadExceptions();
  await loadOverview(true);
  await loadAudit();
}

function setStatusPill(el, text, tone, title) {
  if (!el) return;
  el.textContent = text;
  el.className = `pill pill-${tone}`;
  if (title != null) el.title = title;
}

async function loadStatusChips() {
  const apiPill = document.getElementById("api-health-pill");
  const dbPill = document.getElementById("health-pill");
  const llmPill = document.getElementById("llm-health-pill");
  try {
    const h = await api("/api/health");
    const versionTitle = h.version ? `Banking Control v${h.version}` : "Banking Control Solution";

    if (h.status === "ok" && h.api === "ok") {
      setStatusPill(apiPill, "API online", "ok", `${versionTitle} · REST API responding`);
    } else {
      setStatusPill(apiPill, "API degraded", "warn", versionTitle);
    }

    if (h.database === "ready") {
      const dbTitle = [
        versionTitle,
        h.control_count != null ? `${h.control_count} controls` : "",
        h.golden_count != null ? `${h.golden_count} golden` : "",
      ]
        .filter(Boolean)
        .join(" · ");
      setStatusPill(dbPill, "Database ready", "ok", dbTitle);
    } else if (h.database === "error") {
      setStatusPill(dbPill, "Database error", "danger", versionTitle);
    } else {
      setStatusPill(dbPill, "Database missing", "danger", `${versionTitle} · run init-database job`);
    }

    if (h.llm_link === "online") {
      const provider = h.llm_provider === "openai_compatible" ? "local" : h.llm_provider || "provider";
      setStatusPill(llmPill, "LLM online", "ok", `Assistant link ready (${provider})`);
    } else if (h.llm_link === "offline") {
      setStatusPill(
        llmPill,
        "LLM offline",
        "warn",
        "Configure Bedrock or local LLM via settings (⚙)"
      );
    } else {
      setStatusPill(llmPill, "LLM unknown", "muted", versionTitle);
    }
  } catch {
    setStatusPill(apiPill, "API offline", "danger", "Cannot reach /api/health");
    setStatusPill(dbPill, "Database unknown", "muted", "");
    setStatusPill(llmPill, "LLM unknown", "muted", "");
  }
}

window.loadStatusChips = loadStatusChips;

async function loadOverview(refresh = false) {
  const cards = document.getElementById("overview-cards");
  if (cards && !cards.querySelector(".metric-card")) {
    cards.innerHTML = `<p class="empty">Loading metrics…</p>`;
  }
  const data = await api(`/api/overview${refresh ? "?refresh=1" : ""}`);
  renderOverview(data);
  return data;
}

async function loadDomainOptions() {
  const domains = await api("/api/domains");
  renderDomainFilter(domains, document.getElementById("domain-filter")?.value || "");
  return domains;
}

async function loadControls(domain = "", goldenOnly = false, search = "") {
  setTableLoading("controls-body");
  const params = new URLSearchParams();
  if (domain) params.set("domain", domain);
  if (goldenOnly) params.set("golden", "true");
  if (search.trim()) params.set("search", search.trim());
  params.set("limit", "500");
  const rows = await api(`/api/controls?${params}`);
  renderControls(rows);
}

async function loadAlerts(minRisk = 0) {
  setTableLoading("alerts-body");
  const rows = await api(`/api/alerts?min_risk=${minRisk}`);
  renderAlerts(rows);
}

async function loadExceptions() {
  setTableLoading("exceptions-body");
  const rows = await api("/api/exceptions?limit=100");
  renderExceptions(rows);
}

async function loadAudit() {
  setListLoading("audit-list");
  const rows = await api("/api/audit-log?limit=25");
  renderAudit(rows);
}

function showPaneError(targetId, message) {
  const el = document.getElementById(targetId);
  if (!el) return;
  el.innerHTML = `<tr><td colspan="5" class="empty pane-error">${message}</td></tr>`;
}

async function refreshDashboard() {
  const btn = document.getElementById("refresh-btn");
  btn?.setAttribute("disabled", "true");
  try {
    await Promise.all([
      loadStatusChips(),
      loadOverview(true),
      loadDomainOptions(),
      loadControls(
        document.getElementById("domain-filter")?.value || "",
        document.getElementById("golden-filter")?.checked || false,
        document.getElementById("control-search")?.value || ""
      ),
      loadAlerts(Number(document.getElementById("risk-slider")?.value || 0) / 100),
      loadExceptions(),
      loadAudit(),
    ]);
  } finally {
    btn?.removeAttribute("disabled");
  }
}

async function boot() {
  await loadStatusChips();

  const jobs = [
    { name: "overview", run: () => loadOverview(), target: "overview-cards" },
    { name: "domains", run: () => loadDomainOptions(), target: null },
    { name: "controls", run: () => loadControls(), target: "controls-body" },
    { name: "alerts", run: () => loadAlerts(), target: "alerts-body" },
    { name: "exceptions", run: () => loadExceptions(), target: "exceptions-body" },
    { name: "audit", run: () => loadAudit(), target: "audit-list" },
  ];
  await Promise.all(
    jobs.map(async ({ name, run, target }) => {
      try {
        await run();
      } catch (err) {
        if (!target) return;
        const msg = err instanceof Error ? err.message : String(err);
        if (target === "overview-cards") {
          document.getElementById(target).innerHTML =
            `<p class="empty pane-error">${name}: ${msg}</p>`;
        } else if (target === "audit-list") {
          document.getElementById(target).innerHTML =
            `<li class="empty pane-error">${name}: ${msg}</li>`;
        } else {
          showPaneError(target, `${name}: ${msg}`);
        }
      }
    })
  );

  const reloadControls = () => {
    loadControls(
      document.getElementById("domain-filter").value,
      document.getElementById("golden-filter").checked,
      document.getElementById("control-search").value
    );
  };
  document.getElementById("domain-filter").addEventListener("change", reloadControls);
  document.getElementById("golden-filter").addEventListener("change", reloadControls);
  document.getElementById("control-search").addEventListener("input", () => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(reloadControls, 250);
  });

  const slider = document.getElementById("risk-slider");
  const label = document.getElementById("risk-label");
  slider.addEventListener("input", () => {
    const v = Number(slider.value) / 100;
    label.textContent = v.toFixed(2);
    loadAlerts(v);
  });

  document.getElementById("refresh-btn").addEventListener("click", () => refreshDashboard());

  document.getElementById("exceptions-body").addEventListener("click", (e) => {
    const btn = e.target.closest(".advance-btn");
    if (btn) advanceException(btn.dataset.id);
  });
}

boot().catch((err) => {
  console.error(err);
  document.body.insertAdjacentHTML(
    "beforeend",
    `<p class="empty" style="padding:2rem">Failed to load dashboard: ${err.message}</p>`
  );
});
