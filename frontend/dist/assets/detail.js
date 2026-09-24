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

  const DETAIL_ROUTE = /^#\/(controls|alerts|exceptions|audit)\/(new|\d+)$/;

  function parseDetailHash() {
    const m = (location.hash || "").match(DETAIL_ROUTE);
    if (!m) return null;
    return { kind: m[1], id: m[2] };
  }

  function isCreateControlRoute(route) {
    return route?.kind === "controls" && route.id === "new";
  }

  function navigateToDetail(kind, id) {
    location.hash = `#/${kind}/${id}`;
  }

  function navigateToCreateControl() {
    location.hash = "#/controls/new";
  }

  function setDetailAddControlVisible(visible) {
    document.getElementById("detail-add-control")?.classList.toggle("hidden", !visible);
  }

  function closeDetailView() {
    if (location.hash && DETAIL_ROUTE.test(location.hash)) {
      history.pushState(null, "", location.pathname + location.search);
    }
    showDashboardHome();
  }

  function setTimelineDockVisible(visible) {
    document.getElementById("activity-timeline-dock")?.classList.toggle("hidden", !visible);
  }

  function showDashboardHome() {
    document.getElementById("dashboard-home")?.classList.remove("hidden");
    const detail = document.getElementById("detail-view");
    detail?.classList.add("hidden");
    detail?.setAttribute("aria-hidden", "true");
    setTimelineDockVisible(true);
    document.title = "Banking Control Solution";
  }

  function showDetailShell(title, { showAddControl = false } = {}) {
    document.getElementById("dashboard-home")?.classList.add("hidden");
    const detail = document.getElementById("detail-view");
    detail?.classList.remove("hidden");
    detail?.setAttribute("aria-hidden", "false");
    setTimelineDockVisible(false);
    const titleEl = document.getElementById("detail-title");
    if (titleEl) titleEl.textContent = title;
    setDetailAddControlVisible(showAddControl);
  }

  async function apiJson(path, options) {
    const res = await fetch(path, options);
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = null;
    }
    if (!res.ok) {
      const msg =
        (data && (data.detail?.validation_errors?.join?.("; ") || data.detail?.message || data.detail)) ||
        text ||
        res.statusText;
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
    return data;
  }

  let recommendTimer = null;

  function renderSimilarControlsList(rows) {
    if (!rows?.length) {
      return `<p class="empty">No close catalog matches yet — keep typing name and description.</p>`;
    }
    return `<ul class="detail-link-list control-recommend-list">${rows
      .map(
        (r) => `<li>
        <button type="button" class="detail-entity-link" data-detail="controls" data-id="${r.control_id}">
          <code>${escapeHtml(r.control_code)}</code> — ${escapeHtml(r.control_name)}
          <span class="related-meta">${escapeHtml(r.relation_label || r.relation)} · score ${r.score}</span>
        </button>
      </li>`
      )
      .join("")}</ul>`;
  }

  function renderControlCreateForm(options) {
    const domains = options?.domains || [];
    const domainOpts = domains
      .map(
        (d) =>
          `<option value="${escapeHtml(d.code)}">${escapeHtml(d.code)} — ${escapeHtml(d.default_owner)}</option>`
      )
      .join("");
    const riskOpts = (options?.risk_tiers || [])
      .map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`)
      .join("");
    const freqOpts = (options?.frequencies || [])
      .map((f) => `<option value="${escapeHtml(f)}">${escapeHtml(f)}</option>`)
      .join("");

    return `
      <p class="detail-lead">Define a new catalog control. We validate completeness, compare peers, and run an initial simulation test.</p>
      <form id="control-create-form" class="control-create-form">
        <section class="detail-section">
          <h3>Control definition</h3>
          <div class="control-create-grid">
            <label class="field">
              <span>Control name</span>
              <input name="control_name" required minlength="8" maxlength="200" placeholder="e.g. Real-time mule account detection" />
            </label>
            <label class="field">
              <span>Domain</span>
              <select name="domain" required>${domainOpts}</select>
            </label>
            <label class="field">
              <span>Risk tier</span>
              <select name="risk_tier" required>${riskOpts}</select>
            </label>
            <label class="field">
              <span>Owner</span>
              <input name="owner" required maxlength="120" placeholder="Control owner" />
            </label>
            <label class="field">
              <span>Frequency</span>
              <select name="frequency" required>${freqOpts}</select>
            </label>
            <label class="field">
              <span>Control code (optional)</span>
              <input name="control_code" maxlength="16" placeholder="Auto-assigned (e.g. AML-045)" pattern="[A-Za-z]{2,8}-[0-9]{3,4}" />
            </label>
            <label class="field field-wide">
              <span>Description</span>
              <textarea name="description" required minlength="40" maxlength="8000" rows="5" placeholder="Objective, scope, evidence, and how the control operates…"></textarea>
            </label>
            <label class="field field-wide">
              <span>Similarity group (optional)</span>
              <input name="similarity_key" maxlength="80" placeholder="Harmonization key — suggested when recommendations load" />
            </label>
          </div>
          <div class="control-create-actions">
            <button type="submit" class="btn btn-primary">Create control &amp; run simulation</button>
            <button type="button" class="btn btn-ghost" id="control-create-cancel">Cancel</button>
          </div>
          <p id="control-create-status" class="hint" role="status"></p>
        </section>
        <section class="detail-section" id="control-recommend-section">
          <h3>Catalog recommendations</h3>
          <p class="hint">Similar and related controls from the catalog, plus optional LLM commentary.</p>
          <div id="control-recommend-llm" class="control-recommend-llm assistant-msg-text"></div>
          <div id="control-recommend-similar">${renderSimilarControlsList([])}</div>
        </section>
        <section class="detail-section hidden" id="control-create-result">
          <h3>Create result</h3>
          <div id="control-create-result-body"></div>
        </section>
      </form>`;
  }

  function bindControlCreateForm(options) {
    const form = document.getElementById("control-create-form");
    if (!form) return;
    const domainSelect = form.querySelector('[name="domain"]');
    const ownerInput = form.querySelector('[name="owner"]');
    domainSelect?.addEventListener("change", () => {
      const code = domainSelect.value;
      const match = (options?.domains || []).find((d) => d.code === code);
      if (match && ownerInput && !ownerInput.value.trim()) {
        ownerInput.value = match.default_owner;
      }
      queueRecommendations(form);
    });
    if (domainSelect && ownerInput) {
      const initial = (options?.domains || []).find((d) => d.code === domainSelect.value);
      if (initial && !ownerInput.value) ownerInput.value = initial.default_owner;
    }

    const queueFields = ["control_name", "description", "domain", "risk_tier"];
    queueFields.forEach((name) => {
      form.querySelector(`[name="${name}"]`)?.addEventListener("input", () => queueRecommendations(form));
    });

    document.getElementById("control-create-cancel")?.addEventListener("click", () => closeDetailView());

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      void submitControlCreate(form);
    });
  }

  function queueRecommendations(form) {
    clearTimeout(recommendTimer);
    recommendTimer = setTimeout(() => void fetchControlRecommendations(form), 650);
  }

  async function fetchControlRecommendations(form) {
    const fd = new FormData(form);
    const control_name = String(fd.get("control_name") || "").trim();
    const description = String(fd.get("description") || "").trim();
    if (control_name.length < 8 || description.length < 20) return;
    const status = document.getElementById("control-create-status");
    if (status) status.textContent = "Checking catalog for similar controls…";
    try {
      const data = await apiJson("/api/controls/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          control_name,
          description,
          domain: fd.get("domain"),
          risk_tier: fd.get("risk_tier"),
        }),
      });
      const llmEl = document.getElementById("control-recommend-llm");
      const similarEl = document.getElementById("control-recommend-similar");
      if (similarEl) similarEl.innerHTML = renderSimilarControlsList(data.similar_controls);
      if (llmEl && typeof window.setAssistantMessageBody === "function") {
        window.setAssistantMessageBody(llmEl, "assistant", data.llm?.summary || "");
      } else if (llmEl) {
        llmEl.textContent = data.llm?.summary || "";
      }
      const simInput = form.querySelector('[name="similarity_key"]');
      if (simInput && !simInput.value && data.suggested_similarity_key) {
        simInput.placeholder = `Suggested: ${data.suggested_similarity_key}`;
      }
      if (status) status.textContent = "";
    } catch (err) {
      if (status) status.textContent = err instanceof Error ? err.message : "Recommendations unavailable";
    }
  }

  async function submitControlCreate(form) {
    const status = document.getElementById("control-create-status");
    const fd = new FormData(form);
    const payload = Object.fromEntries(fd.entries());
    if (status) status.textContent = "Validating, comparing to catalog, and running simulation…";
    form.querySelector('[type="submit"]')?.setAttribute("disabled", "true");
    try {
      const result = await apiJson("/api/controls", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, run_simulation: true }),
      });
      const resultSection = document.getElementById("control-create-result");
      const resultBody = document.getElementById("control-create-result-body");
      resultSection?.classList.remove("hidden");
      const sim = result.simulation?.outputs;
      const warnings = result.catalog_review?.warnings || [];
      resultBody.innerHTML = `
        <p class="detail-lead"><code>${escapeHtml(result.control_code)}</code> created (id ${result.control_id}).</p>
        ${warnings.length ? `<ul class="control-create-warnings">${warnings.map((w) => `<li>${escapeHtml(w)}</li>`).join("")}</ul>` : ""}
        ${
          sim
            ? `<dl class="detail-dl">
            ${dlRow("Simulation status", statusPill(sim.status))}
            ${dlRow("Summary", escapeHtml(sim.summary || "—"))}
            ${dlRow("Exception rate", sim.metrics?.exception_rate_pct != null ? `${sim.metrics.exception_rate_pct}%` : "—")}
          </dl>`
            : `<p class="empty">${escapeHtml(result.simulation_error || "Simulation did not run.")}</p>`
        }
        <button type="button" class="btn btn-primary" id="control-create-open" data-id="${result.control_id}">Open control detail</button>`;
      document.getElementById("control-create-open")?.addEventListener("click", (ev) => {
        navigateToDetail("controls", ev.currentTarget.dataset.id);
      });
      if (status) status.textContent = "Control created successfully.";
      if (typeof window.loadControls === "function") window.loadControls();
      if (typeof window.loadOverview === "function") window.loadOverview(true);
    } catch (err) {
      if (status) status.textContent = err instanceof Error ? err.message : "Create failed";
    } finally {
      form.querySelector('[type="submit"]')?.removeAttribute("disabled");
    }
  }

  async function loadControlCreateView() {
    showDetailShell("Create control", { showAddControl: false });
    document.title = "Create control · Banking Control Solution";
    const body = document.getElementById("detail-body");
    if (!body) return;
    body.innerHTML = `<p class="empty">Loading form…</p>`;
    try {
      const options = await api("/api/controls/form-options");
      body.innerHTML = renderControlCreateForm(options);
      bindControlCreateForm(options);
    } catch (err) {
      body.innerHTML = `<p class="empty pane-error">${err instanceof Error ? err.message : String(err)}</p>`;
    }
  }

  function dlRow(label, valueHtml) {
    return `<div class="detail-dl-row"><dt>${label}</dt><dd>${valueHtml}</dd></div>`;
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderStandardsSection(refs) {
    if (!refs?.length) return "";
    return `<section class="detail-section">
      <h3>Industry standards &amp; guidance</h3>
      <p class="hint">Public sources from regulators and standards bodies (external links).</p>
      <ul class="standards-link-list">
        ${refs
          .map(
            (r) => `<li>
          <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(r.label)}</a>
        </li>`
          )
          .join("")}
      </ul>
    </section>`;
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

  let dagResizeObserver = null;

  function measureDagWrapWidth(wrap) {
    if (!wrap) return 640;
    const w = wrap.clientWidth;
    return Math.max(280, w > 0 ? w : 640);
  }

  function estimateEdgeLabelWidth(label) {
    const text = String(label || "");
    return Math.min(text.length, 32) * 6.4 + 14;
  }

  function ensureDagResizeObserver() {
    if (dagResizeObserver || typeof ResizeObserver === "undefined") return;
    dagResizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const graph = entry.target._processGraph;
        if (graph) paintControlFlowGraph(graph);
      }
    });
  }

  function appendEdgeLabel(labelLayer, x, y, text) {
    const labelText = String(text || "");
    if (!labelText) return;
    const w = estimateEdgeLabelWidth(labelText);
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("class", "control-dag-edge-label-group");
    const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bg.setAttribute("class", "control-dag-edge-label-bg");
    bg.setAttribute("x", String(x - w / 2));
    bg.setAttribute("y", String(y - 12));
    bg.setAttribute("width", String(w));
    bg.setAttribute("height", "16");
    bg.setAttribute("rx", "4");
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", String(x));
    label.setAttribute("y", String(y));
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("dominant-baseline", "middle");
    label.setAttribute("class", "control-dag-edge-label");
    label.textContent = labelText;
    group.appendChild(bg);
    group.appendChild(label);
    labelLayer.appendChild(group);
  }

  function paintControlFlowGraph(graph) {
    const svg = document.getElementById("control-flow-graph");
    if (!svg || !graph?.nodes?.length) return;

    const wrap = svg.closest(".control-dag-wrap");
    if (wrap) {
      wrap._processGraph = graph;
      ensureDagResizeObserver();
      dagResizeObserver?.observe(wrap);
    }

    const NODE_H = 54;
    const ROW_GAP = 16;
    const PAD_X = 12;
    const PAD_Y = 22;
    const MIN_NODE_W = 84;
    const MIN_LAYER_GAP = 52;
    const LABEL_CLEARANCE = 10;

    const layerOf = new Map();
    graph.nodes.forEach((n) => layerOf.set(n.control_code, n.layer ?? 0));

    const byLayer = new Map();
    graph.nodes.forEach((n) => {
      const layer = n.layer ?? 0;
      if (!byLayer.has(layer)) byLayer.set(layer, []);
      byLayer.get(layer).push(n);
    });
    byLayer.forEach((list) => list.sort((a, b) => a.control_code.localeCompare(b.control_code)));

    const maxLayer = Math.max(...graph.nodes.map((n) => n.layer ?? 0));
    const numCols = maxLayer + 1;
    const gapCount = Math.max(0, maxLayer);

    const gapNeeded = new Array(gapCount).fill(MIN_LAYER_GAP);
    (graph.edges || []).forEach((e) => {
      if (!e.label) return;
      const fromL = layerOf.get(e.from);
      const toL = layerOf.get(e.to);
      if (fromL === undefined || toL === undefined || fromL === toL) return;
      const lo = Math.min(fromL, toL);
      const hi = Math.max(fromL, toL);
      const span = hi - lo;
      const perGap = estimateEdgeLabelWidth(e.label) / Math.max(1, span);
      for (let g = lo; g < hi; g += 1) {
        gapNeeded[g] = Math.max(gapNeeded[g], perGap + LABEL_CLEARANCE);
      }
    });

    const containerWidth = measureDagWrapWidth(wrap);
    const totalGapMin = gapNeeded.reduce((sum, g) => sum + g, 0);
    let nodeW = Math.floor((containerWidth - PAD_X * 2 - totalGapMin) / numCols);
    nodeW = Math.max(MIN_NODE_W, nodeW);

    let totalGap = totalGapMin;
    let width = PAD_X * 2 + numCols * nodeW + totalGap;
    if (width < containerWidth && gapCount > 0) {
      const extra = containerWidth - width;
      const weights = gapNeeded.slice();
      const weightSum = weights.reduce((a, b) => a + b, 0) || gapCount;
      gapNeeded.forEach((g, i) => {
        gapNeeded[i] = g + (extra * weights[i]) / weightSum;
      });
      totalGap = gapNeeded.reduce((sum, g) => sum + g, 0);
      width = PAD_X * 2 + numCols * nodeW + totalGap;
    }

    const layerX = new Map();
    let xCursor = PAD_X;
    for (let layer = 0; layer <= maxLayer; layer += 1) {
      layerX.set(layer, xCursor);
      xCursor += nodeW;
      if (layer < maxLayer) xCursor += gapNeeded[layer];
    }

    const maxRows = Math.max(1, ...[...byLayer.values()].map((l) => l.length));
    const columnHeight = maxRows * NODE_H + Math.max(0, maxRows - 1) * ROW_GAP;

    const positions = new Map();
    byLayer.forEach((list, layer) => {
      const blockH = list.length * NODE_H + Math.max(0, list.length - 1) * ROW_GAP;
      const startY = PAD_Y + (columnHeight - blockH) / 2;
      const x = layerX.get(layer) ?? PAD_X;
      list.forEach((n, i) => {
        positions.set(n.control_code, {
          x,
          y: startY + i * (NODE_H + ROW_GAP),
          node: n,
        });
      });
    });

    const height = PAD_Y * 2 + columnHeight;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.removeAttribute("width");
    svg.removeAttribute("height");
    svg.innerHTML = "";

    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    defs.innerHTML = `<marker id="dag-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(147, 164, 188, 0.95)"></path>
    </marker>`;
    svg.appendChild(defs);

    const edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    edgeLayer.setAttribute("class", "control-dag-edges");
    const labelLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    labelLayer.setAttribute("class", "control-dag-edge-labels");

    const labelSlots = new Map();
    (graph.edges || []).forEach((e) => {
      const from = positions.get(e.from);
      const to = positions.get(e.to);
      if (!from || !to) return;
      const x1 = from.x + nodeW;
      const y1 = from.y + NODE_H / 2;
      const x2 = to.x;
      const y2 = to.y + NODE_H / 2;
      const goingForward = x2 >= x1;
      const startX = goingForward ? x1 : from.x;
      const endX = goingForward ? x2 : to.x + nodeW;
      const curve = Math.max(22, Math.abs(x2 - x1) * 0.12, Math.abs(y2 - y1) * 0.4);
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      if (goingForward) {
        path.setAttribute(
          "d",
          `M ${x1} ${y1} C ${x1 + curve} ${y1}, ${x2 - curve} ${y2}, ${x2} ${y2}`
        );
        path.setAttribute("marker-end", "url(#dag-arrow)");
      } else {
        path.setAttribute(
          "d",
          `M ${from.x} ${y1} C ${from.x - curve} ${y1}, ${to.x + nodeW + curve} ${y2}, ${to.x + nodeW} ${y2}`
        );
        path.setAttribute("marker-end", "url(#dag-arrow)");
      }
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", "rgba(147, 164, 188, 0.5)");
      path.setAttribute("stroke-width", "1.25");
      edgeLayer.appendChild(path);

      if (!e.label) return;
      const corridorW = Math.abs(endX - startX);
      const labelW = estimateEdgeLabelWidth(e.label);
      if (corridorW < labelW + 8) return;

      const midX = (startX + endX) / 2;
      const midY = (y1 + y2) / 2;
      const slotKey = `${Math.round(midX)}:${Math.round(midY)}`;
      const slot = labelSlots.get(slotKey) ?? 0;
      labelSlots.set(slotKey, slot + 1);
      const laneOffset = 16 + slot * 13;
      const labelY =
        Math.abs(y2 - y1) < 4
          ? Math.min(from.y, to.y) - 8 - slot * 12
          : midY - laneOffset;

      appendEdgeLabel(labelLayer, midX, labelY, e.label);
    });

    svg.appendChild(edgeLayer);

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
      rect.setAttribute("width", String(nodeW));
      rect.setAttribute("height", String(NODE_H));
      rect.setAttribute("rx", "6");
      g.appendChild(rect);

      const fo = document.createElementNS("http://www.w3.org/2000/svg", "foreignObject");
      fo.setAttribute("x", String(x));
      fo.setAttribute("y", String(y));
      fo.setAttribute("width", String(nodeW));
      fo.setAttribute("height", String(NODE_H));
      const maxNameChars = Math.max(18, Math.floor(nodeW / 5.2));
      const shortName =
        (node.control_name || "").length > maxNameChars
          ? `${node.control_name.slice(0, maxNameChars - 1)}…`
          : node.control_name || "";
      fo.innerHTML = `<div xmlns="http://www.w3.org/1999/xhtml" class="control-dag-node-inner">
        <span class="control-dag-code">${escapeHtml(node.control_code)}</span>
        <span class="control-dag-name">${escapeHtml(shortName)}</span>
      </div>`;
      g.appendChild(fo);

      svg.appendChild(g);
    });

    svg.appendChild(labelLayer);
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
        <p class="detail-description detail-description-rich">${escapeHtml(c.description)}</p>
      </section>
      ${renderStandardsSection(data.standards_refs)}
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
    if (kind === "controls" && id === "new") {
      await loadControlCreateView();
      return;
    }

    showDetailShell(DETAIL_TITLES[kind] || "Detail", { showAddControl: kind === "controls" });
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
        requestAnimationFrame(() => paintControlFlowGraph(controlData.process_graph));
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
    document.getElementById("detail-add-control")?.addEventListener("click", () => navigateToCreateControl());

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
