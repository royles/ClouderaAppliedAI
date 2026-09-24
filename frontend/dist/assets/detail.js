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

  function renderRelatedControls(related) {
    if (!related?.length) {
      return `<p class="empty">No peer controls share the same similarity group.</p>`;
    }
    return `<ul class="detail-link-list related-controls-list">${related
      .map(
        (r) => `<li>
        <button type="button" class="detail-entity-link related-control-link" data-detail="controls" data-id="${r.control_id}">
          <code>${r.control_code}</code> — ${r.control_name}
          <span class="related-meta">${r.domain} · ${r.relation_label || r.relation}${r.is_golden ? " · ★" : ""}</span>
        </button>
      </li>`
      )
      .join("")}</ul>`;
  }

  function renderProcessGraphSection(graph) {
    if (!graph) {
      return `<section class="detail-section">
        <h3>Process sequence</h3>
        <p class="empty">This control is not yet mapped to a reference process chain.</p>
      </section>`;
    }
    return `<section class="detail-section detail-section-graph">
      <h3>Process sequence (DAG)</h3>
      <p class="hint">${graph.flow_name} — ${graph.flow_description}</p>
      <div class="control-dag-wrap">
        <svg id="control-flow-graph" class="control-dag-svg" role="img" aria-label="Horizontal control sequence graph"></svg>
      </div>
    </section>`;
  }

  function paintControlFlowGraph(graph) {
    const svg = document.getElementById("control-flow-graph");
    if (!svg || !graph?.nodes?.length) return;

    const NODE_W = 132;
    const NODE_H = 52;
    const LAYER_GAP = 48;
    const ROW_GAP = 16;
    const PAD = 20;

    const byLayer = new Map();
    graph.nodes.forEach((n) => {
      const layer = n.layer ?? 0;
      if (!byLayer.has(layer)) byLayer.set(layer, []);
      byLayer.get(layer).push(n);
    });
    byLayer.forEach((list) => list.sort((a, b) => a.control_code.localeCompare(b.control_code)));

    const positions = new Map();
    let maxLayer = 0;
    let maxRows = 1;
    byLayer.forEach((list, layer) => {
      maxLayer = Math.max(maxLayer, layer);
      maxRows = Math.max(maxRows, list.length);
      list.forEach((n, i) => {
        positions.set(n.control_code, {
          x: PAD + layer * (NODE_W + LAYER_GAP),
          y: PAD + i * (NODE_H + ROW_GAP),
          node: n,
        });
      });
    });

    const width = PAD * 2 + (maxLayer + 1) * NODE_W + maxLayer * LAYER_GAP;
    const rows = Math.max(...[...byLayer.values()].map((l) => l.length));
    const height = PAD * 2 + rows * NODE_H + (rows - 1) * ROW_GAP;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = "";

    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    defs.innerHTML = `<marker id="dag-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(147, 164, 188, 0.95)"></path>
    </marker>`;
    svg.appendChild(defs);

    (graph.edges || []).forEach((e) => {
      const from = positions.get(e.from);
      const to = positions.get(e.to);
      if (!from || !to) return;
      const x1 = from.x + NODE_W;
      const y1 = from.y + NODE_H / 2;
      const x2 = to.x;
      const y2 = to.y + NODE_H / 2;
      const midX = (x1 + x2) / 2;
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute(
        "d",
        `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`
      );
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", "rgba(147, 164, 188, 0.55)");
      path.setAttribute("stroke-width", "1.5");
      path.setAttribute("marker-end", "url(#dag-arrow)");
      svg.appendChild(path);

      if (e.label) {
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", String(midX));
        label.setAttribute("y", String((y1 + y2) / 2 - 4));
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("class", "control-dag-edge-label");
        label.textContent = e.label.length > 22 ? `${e.label.slice(0, 20)}…` : e.label;
        svg.appendChild(label);
      }
    });

    positions.forEach(({ x, y, node }) => {
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      g.setAttribute("class", `control-dag-node${node.is_current ? " is-current" : ""}`);
      if (node.control_id) {
        g.setAttribute("data-id", String(node.control_id));
        g.setAttribute("role", "link");
        g.setAttribute("tabindex", "0");
      }

      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("x", String(x));
      rect.setAttribute("y", String(y));
      rect.setAttribute("width", String(NODE_W));
      rect.setAttribute("height", String(NODE_H));
      rect.setAttribute("rx", "8");
      g.appendChild(rect);

      const code = document.createElementNS("http://www.w3.org/2000/svg", "text");
      code.setAttribute("x", String(x + NODE_W / 2));
      code.setAttribute("y", String(y + 20));
      code.setAttribute("text-anchor", "middle");
      code.setAttribute("class", "control-dag-code");
      code.textContent = node.control_code;
      g.appendChild(code);

      const name = document.createElementNS("http://www.w3.org/2000/svg", "text");
      name.setAttribute("x", String(x + NODE_W / 2));
      name.setAttribute("y", String(y + 38));
      name.setAttribute("text-anchor", "middle");
      name.setAttribute("class", "control-dag-name");
      const shortName =
        (node.control_name || "").length > 24
          ? `${node.control_name.slice(0, 22)}…`
          : node.control_name || "";
      name.textContent = shortName;
      g.appendChild(name);

      svg.appendChild(g);
    });
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
      ${renderProcessGraphSection(data.process_graph)}
      <section class="detail-section">
        <h3>Related controls</h3>
        <p class="hint">Peers with the same similarity / objective grouping (harmonization set).</p>
        ${renderRelatedControls(data.related_controls)}
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
        const controlData = await api(`/api/controls/${id}`);
        html = renderControlDetail(controlData);
        body.innerHTML = html;
        paintControlFlowGraph(controlData.process_graph);
        return;
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
      const dagNode = e.target.closest(".control-dag-node[data-id]");
      if (dagNode?.dataset.id) {
        navigateToDetail("controls", dagNode.dataset.id);
        return;
      }
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

    document.getElementById("detail-view")?.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      const dagNode = e.target.closest(".control-dag-node[data-id]");
      if (!dagNode) return;
      e.preventDefault();
      navigateToDetail("controls", dagNode.dataset.id);
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
