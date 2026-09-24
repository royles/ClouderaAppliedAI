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

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  return res.json();
}

function renderOverview(data) {
  const cards = [
    {
      label: "Control health",
      value: `${data.control_health_pct}%`,
      hint: `${data.control_count} controls in catalog`,
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

function renderControls(rows) {
  const body = document.getElementById("controls-body");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="5" class="empty">No controls</td></tr>`;
    return;
  }
  body.innerHTML = rows
    .map(
      (r) => `<tr>
      <td><code>${r.control_code}</code></td>
      <td>${r.control_name}</td>
      <td>${r.domain}</td>
      <td>${statusPill(r.risk_tier)}</td>
      <td>${statusPill(r.latest_status || "Not Tested")}</td>
    </tr>`
    )
    .join("");
}

function renderAlerts(rows) {
  const body = document.getElementById("alerts-body");
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

async function loadOverview(refresh = false) {
  const data = await api(`/api/overview${refresh ? "?refresh=1" : ""}`);
  renderOverview(data);
}

async function loadControls(domain = "") {
  const q = domain ? `?domain=${encodeURIComponent(domain)}` : "";
  const rows = await api(`/api/controls${q}`);
  renderControls(rows);
  const domains = [...new Set(rows.map((r) => r.domain))].sort();
  const select = document.getElementById("domain-filter");
  const current = select.value;
  select.innerHTML =
    `<option value="">All domains</option>` +
    domains.map((d) => `<option value="${d}">${d}</option>`).join("");
  select.value = current || "";
}

async function loadAlerts(minRisk = 0) {
  const rows = await api(`/api/alerts?min_risk=${minRisk}`);
  renderAlerts(rows);
}

async function loadExceptions() {
  const rows = await api("/api/exceptions?limit=100");
  renderExceptions(rows);
}

async function loadAudit() {
  const rows = await api("/api/audit-log?limit=25");
  renderAudit(rows);
}

async function boot() {
  const health = document.getElementById("health-pill");
  try {
    const h = await api("/api/health");
    health.textContent = h.database === "ready" ? "Database ready" : "Database missing";
    health.className = `pill ${h.database === "ready" ? "pill-ok" : "pill-danger"}`;
  } catch {
    health.textContent = "API offline";
    health.className = "pill pill-danger";
    return;
  }

  await Promise.all([loadOverview(), loadControls(), loadAlerts(), loadExceptions(), loadAudit()]);

  document.getElementById("domain-filter").addEventListener("change", (e) => {
    loadControls(e.target.value);
  });

  const slider = document.getElementById("risk-slider");
  const label = document.getElementById("risk-label");
  slider.addEventListener("input", () => {
    const v = Number(slider.value) / 100;
    label.textContent = v.toFixed(2);
    loadAlerts(v);
  });

  document.getElementById("refresh-btn").addEventListener("click", () => loadOverview(true));

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
