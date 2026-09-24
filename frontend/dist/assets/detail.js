(function () {
  const fmtMoney = (n) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(n);

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

  const DETAIL_ROUTE = /^#\/(controls|alerts|exceptions|audit)\/(\d+)$/;

  function parseDetailHash() {
    const m = (location.hash || "").match(DETAIL_ROUTE);
    if (!m) return null;
    return { kind: m[1], id: m[2] };
  }

  function navigateToDetail(kind, id) {
    location.hash = `#/${kind}/${id}`;
  }

  function closeDetailView() {
    if (location.hash && DETAIL_ROUTE.test(location.hash)) {
      history.pushState(null, "", location.pathname + location.search);
    }
    showDashboardHome();
  }

  function showDashboardHome() {
    document.getElementById("dashboard-home")?.classList.remove("hidden");
    const detail = document.getElementById("detail-view");
    detail?.classList.add("hidden");
    detail?.setAttribute("aria-hidden", "true");
    document.title = "Banking Control Solution";
  }

  function showDetailShell(title) {
    document.getElementById("dashboard-home")?.classList.add("hidden");
    const detail = document.getElementById("detail-view");
    detail?.classList.remove("hidden");
    detail?.setAttribute("aria-hidden", "false");
    const titleEl = document.getElementById("detail-title");
    if (titleEl) titleEl.textContent = title;
  }

  function dlRow(label, valueHtml) {
    return `<div class="detail-dl-row"><dt>${label}</dt><dd>${valueHtml}</dd></div>`;
  }

  function relatedEntityLink(entityType, entityId) {
    const t = String(entityType || "").toLowerCase();
    const id = String(entityId || "").trim();
    if (!id || !/^\d+$/.test(id)) return null;
    if (t === "control") return { kind: "controls", label: `Control #${id}` };
    if (t === "exception") return { kind: "exceptions", label: `Exception #${id}` };
    if (t === "alert" || t === "transaction") return { kind: "alerts", label: `Alert #${id}` };
    return null;
  }

  function renderControlDetail(data) {
    const c = data.control;
    document.title = `${c.control_code} · Banking Control Solution`;
    const meta = [
      dlRow("Domain", c.domain),
      dlRow("Risk tier", statusPill(c.risk_tier)),
      dlRow("Latest test status", statusPill(data.latest_status || "Not Tested")),
      dlRow("Owner", c.owner),
      dlRow("Frequency", c.frequency),
      dlRow("Golden MVP", c.is_golden ? "Yes ★" : "No"),
      c.similarity_key ? dlRow("Similarity group", `<code>${c.similarity_key}</code>`) : "",
    ].join("");

    const assessments = data.assessments?.length
      ? `<div class="table-wrap"><table><thead><tr>
          <th>Date</th><th>Unit</th><th>Status</th><th>Tester</th><th>Evidence</th>
        </tr></thead><tbody>${data.assessments
          .map(
            (a) => `<tr>
            <td>${a.assessment_date}</td>
            <td>${a.unit_code}</td>
            <td>${statusPill(a.status)}</td>
            <td>${a.tester}</td>
            <td>${a.evidence_ref || "—"}${a.notes ? `<br /><small>${a.notes}</small>` : ""}</td>
          </tr>`
          )
          .join("")}</tbody></table></div>`
      : `<p class="empty">No assessments recorded yet.</p>`;

    const exceptions = data.exceptions?.length
      ? `<ul class="detail-link-list">${data.exceptions
          .map(
            (e) => `<li>
            <button type="button" class="detail-entity-link" data-detail="exceptions" data-id="${e.exception_id}">
              ${e.title} · ${e.unit_code} · ${statusPill(e.status)}
            </button>
          </li>`
          )
          .join("")}</ul>`
      : `<p class="empty">No exceptions linked to this control.</p>`;

    return `
      <p class="detail-lead"><code>${c.control_code}</code> — ${c.control_name}</p>
      <section class="detail-section">
        <h3>Overview</h3>
        <dl class="detail-dl">${meta}</dl>
        <p class="detail-description">${c.description}</p>
      </section>
      <section class="detail-section">
        <h3>Recent assessments</h3>
        ${assessments}
      </section>
      <section class="detail-section">
        <h3>Related exceptions</h3>
        ${exceptions}
      </section>`;
  }

  function renderAlertDetail(data) {
    const a = data.alert;
    document.title = `Alert ${a.alert_id} · Banking Control Solution`;
    return `
      <p class="detail-lead">${a.alert_type} · ${fmtMoney(a.amount_usd)}</p>
      <section class="detail-section">
        <h3>Transaction summary</h3>
        <dl class="detail-dl">
          ${dlRow("Alert time", a.alert_at)}
          ${dlRow("Status", statusPill(a.status))}
          ${dlRow("Risk score", `${(a.risk_score * 100).toFixed(0)}%`)}
          ${dlRow("Customer reference", `<code>${a.customer_ref}</code>`)}
          ${dlRow("Channel", a.channel)}
          ${dlRow("Business unit", `${a.unit_name} (${a.unit_code}) · ${a.region}`)}
        </dl>
      </section>
      <section class="detail-section">
        <h3>Analyst narrative</h3>
        <p class="detail-description">${a.narrative}</p>
      </section>`;
  }

  function renderExceptionDetail(data) {
    const e = data.exception;
    document.title = `${e.title} · Banking Control Solution`;
    return `
      <p class="detail-lead">${e.title}</p>
      <section class="detail-section">
        <h3>Exception</h3>
        <dl class="detail-dl">
          ${dlRow("Severity", statusPill(e.severity))}
          ${dlRow("Status", statusPill(e.status))}
          ${dlRow("Opened", e.opened_at)}
          ${dlRow("Due date", e.due_date)}
          ${dlRow("Assignee", e.assignee)}
          ${dlRow("Business unit", `${e.unit_name} (${e.unit_code}) · ${e.region}`)}
        </dl>
        <p class="detail-description">${e.description}</p>
      </section>
      <section class="detail-section">
        <h3>Linked control</h3>
        <p>
          <button type="button" class="detail-entity-link" data-detail="controls" data-id="${e.control_id}">
            <code>${e.control_code}</code> — ${e.control_name} (${e.domain}, ${e.risk_tier})
          </button>
        </p>
      </section>
      <section class="detail-section">
        <h3>Workflow</h3>
        <p class="hint">Advance the exception through remediation stages from the dashboard list, or use the button below.</p>
        <button type="button" class="btn btn-secondary" id="detail-exception-advance" data-id="${e.exception_id}" data-status="${e.status}">
          Advance status
        </button>
      </section>`;
  }

  function renderAuditDetail(data) {
    const ev = data.event;
    document.title = `Audit · ${ev.action}`;
    const related = relatedEntityLink(ev.entity_type, ev.entity_id);
    const relatedHtml = related
      ? `<button type="button" class="detail-entity-link" data-detail="${related.kind}" data-id="${ev.entity_id}">
          Open ${related.label}
        </button>`
      : `<span>${ev.entity_type} · ${ev.entity_id}</span>`;

    return `
      <p class="detail-lead">${ev.action}</p>
      <section class="detail-section">
        <h3>Event</h3>
        <dl class="detail-dl">
          ${dlRow("When", ev.event_at)}
          ${dlRow("Actor", ev.actor)}
          ${dlRow("Action", ev.action)}
          ${dlRow("Related record", relatedHtml)}
        </dl>
        <p class="detail-description">${ev.detail}</p>
      </section>`;
  }

  const DETAIL_TITLES = {
    controls: "Control detail",
    alerts: "Transaction alert detail",
    exceptions: "Control exception detail",
    audit: "Audit trail detail",
  };

  async function loadDetailView(kind, id) {
    showDetailShell(DETAIL_TITLES[kind] || "Detail");
    const body = document.getElementById("detail-body");
    if (!body) return;
    body.innerHTML = `<p class="empty">Loading…</p>`;

    try {
      let html;
      if (kind === "controls") {
        html = renderControlDetail(await api(`/api/controls/${id}`));
      } else if (kind === "alerts") {
        html = renderAlertDetail(await api(`/api/alerts/${id}`));
      } else if (kind === "exceptions") {
        html = renderExceptionDetail(await api(`/api/exceptions/${id}`));
      } else if (kind === "audit") {
        html = renderAuditDetail(await api(`/api/audit-log/${id}`));
      } else {
        throw new Error("Unknown detail type");
      }
      body.innerHTML = html;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      body.innerHTML = `<p class="empty pane-error">${msg}</p>`;
    }
  }

  async function routeFromHash() {
    const route = parseDetailHash();
    if (!route) {
      showDashboardHome();
      return;
    }
    await loadDetailView(route.kind, route.id);
  }

  const STATUS_FLOW = ["Open", "In Remediation", "Pending Validation", "Closed"];

  async function advanceExceptionFromDetail(id, currentStatus) {
    const idx = STATUS_FLOW.indexOf(currentStatus);
    const next = STATUS_FLOW[Math.min(idx + 1, STATUS_FLOW.length - 1)] || "In Remediation";
    await api(`/api/exceptions/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: next }),
    });
    await loadDetailView("exceptions", id);
    if (typeof window.loadExceptions === "function") window.loadExceptions();
    if (typeof window.loadOverview === "function") window.loadOverview(true);
    if (typeof window.loadAudit === "function") window.loadAudit();
  }

  function initDetailRouting() {
    document.getElementById("detail-back")?.addEventListener("click", () => closeDetailView());

    document.getElementById("detail-view")?.addEventListener("click", (e) => {
      const link = e.target.closest(".detail-entity-link");
      if (link?.dataset.detail && link.dataset.id) {
        navigateToDetail(link.dataset.detail, link.dataset.id);
        return;
      }
      const adv = e.target.closest("#detail-exception-advance");
      if (adv) {
        void advanceExceptionFromDetail(adv.dataset.id, adv.dataset.status);
      }
    });

    document.querySelector(".main-content")?.addEventListener("click", (e) => {
      if (e.target.closest(".advance-btn")) return;
      const row = e.target.closest("[data-detail]");
      if (!row?.dataset.detail || !row.dataset.id) return;
      navigateToDetail(row.dataset.detail, row.dataset.id);
    });

    document.querySelector(".main-content")?.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      const row = e.target.closest("[data-detail]");
      if (!row?.dataset.detail || !row.dataset.id) return;
      e.preventDefault();
      navigateToDetail(row.dataset.detail, row.dataset.id);
    });

    window.addEventListener("hashchange", () => {
      void routeFromHash();
    });

    void routeFromHash();
  }

  window.navigateToDetail = navigateToDetail;
  window.initDetailRouting = initDetailRouting;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDetailRouting);
  } else {
    initDetailRouting();
  }
})();
