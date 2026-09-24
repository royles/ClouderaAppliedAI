(function () {
  const PAGE_SIZE = 35;
  const POLL_MS = 5000;

  const state = {
    items: [],
    hasMore: true,
    loading: false,
    loadingMore: false,
    polling: false,
    maxAlertId: 0,
    observer: null,
    pollTimer: null,
  };

  function alertRowHtml(r, extraClass = "") {
    const fmtMoney = window.fmtMoney || ((n) => String(n));
    const statusPill = window.statusPill || ((t) => t);
    return `<tr class="data-row ${extraClass}" tabindex="0" role="link" data-detail="alerts" data-id="${r.alert_id}" data-alert-id="${r.alert_id}" aria-label="Open transaction alert">
      <td>${r.alert_at}</td>
      <td>${r.alert_type}<br /><small>${r.unit_code} · ${r.channel}</small></td>
      <td>${fmtMoney(r.amount_usd)}</td>
      <td>${(r.risk_score * 100).toFixed(0)}%</td>
      <td>${statusPill(r.status)}</td>
    </tr>`;
  }

  function buildAlertParams(extra = {}) {
    const params = new URLSearchParams();
    params.set("limit", String(extra.limit != null ? extra.limit : PAGE_SIZE));
    const minRisk = Number(document.getElementById("risk-slider")?.value || 0) / 100;
    params.set("min_risk", String(minRisk));
    const statusFilter = window.getAlertStatusFilter?.();
    if (statusFilter) params.set("status", statusFilter);
    // Live poll must not apply timeline date brush — new alerts would be excluded.
    if (!extra.live && typeof window.appendActivityTimeParams === "function") {
      window.appendActivityTimeParams(params);
    }
    if (extra.live) params.set("live", "true");
    Object.entries(extra).forEach(([k, v]) => {
      if (k === "live" || k === "limit") return;
      if (v != null) params.set(k, String(v));
    });
    return params;
  }

  function sortNewestFirst(rows) {
    return rows.slice().sort((a, b) => b.alert_id - a.alert_id);
  }

  async function fetchAlertsPage(extra = {}) {
    const params = buildAlertParams(extra);
    const res = await fetch(`/api/alerts?${params}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  function syncMaxId() {
    if (!state.items.length) {
      state.maxAlertId = 0;
      return;
    }
    state.maxAlertId = Math.max(...state.items.map((r) => r.alert_id));
  }

  function updateTimelineFilterNotice() {
    const notice = document.getElementById("alerts-time-filter-notice");
    if (!notice) return;
    const tf = window.activityTimeFilter;
    const active = Boolean(tf?.from || tf?.to);
    notice.classList.toggle("hidden", !active);
    if (!active) {
      notice.textContent = "";
      return;
    }
    const range =
      tf.from && tf.to
        ? tf.from === tf.to
          ? tf.from
          : `${tf.from} → ${tf.to}`
        : tf.from || tf.to;
    notice.innerHTML = `Date filter active (${range}) — showing a subset of alerts. <button type="button" class="btn btn-ghost alerts-clear-date" id="alerts-clear-date">Show all dates</button>`;
    notice.querySelector("#alerts-clear-date")?.addEventListener("click", () => {
      window.clearActivityTimeFilter?.();
    });
  }

  function renderAlertsBody() {
    const body = document.getElementById("alerts-body");
    const meta = document.getElementById("alerts-stream-meta");
    updateTimelineFilterNotice();
    if (!body) return;
    if (!state.items.length) {
      body.innerHTML = `<tr><td colspan="5" class="empty">No alerts at this risk threshold</td></tr>`;
    } else {
      body.innerHTML = state.items.map((r) => alertRowHtml(r)).join("");
    }
    if (meta) {
      meta.textContent = state.items.length
        ? `${state.items.length} loaded${state.hasMore ? " · scroll for more" : ""}`
        : "";
    }
    const sentinel = document.getElementById("alerts-load-sentinel");
    sentinel?.classList.toggle("hidden", !state.hasMore);
  }

  function prependAlerts(rows) {
    if (!rows.length) return;
    const existing = new Set(state.items.map((r) => r.alert_id));
    const fresh = sortNewestFirst(rows.filter((r) => !existing.has(r.alert_id)));
    if (!fresh.length) return;

    const scrollRoot = document.getElementById("alerts-scroll");
    const stickToTop = scrollRoot ? scrollRoot.scrollTop < 120 : true;

    state.items = [...fresh, ...state.items];
    syncMaxId();
    const body = document.getElementById("alerts-body");
    if (!body) return;
    body.querySelector("tr.empty")?.remove();
    if (!body.querySelector("tr[data-alert-id]")) {
      renderAlertsBody();
      return;
    }
    // Insert oldest-of-batch first so newest row ends up at the top of the table.
    fresh
      .slice()
      .reverse()
      .forEach((r) => {
        body.insertAdjacentHTML("afterbegin", alertRowHtml(r, "alert-row-enter"));
      });

    if (stickToTop && scrollRoot) {
      scrollRoot.scrollTo({ top: 0, behavior: "smooth" });
    }

    const meta = document.getElementById("alerts-stream-meta");
    if (meta && state.items.length) {
      const newCount = fresh.length;
      meta.textContent = `${state.items.length} loaded · ${newCount} new at top${
        state.hasMore ? " · scroll for more" : ""
      }`;
    }
  }

  async function resetAndLoadAlerts() {
    state.items = [];
    state.hasMore = true;
    state.loading = true;
    const body = document.getElementById("alerts-body");
    if (body) body.innerHTML = `<tr><td colspan="5" class="empty">Loading…</td></tr>`;
    try {
      const data = await fetchAlertsPage();
      state.items = sortNewestFirst(data.items || []);
      state.hasMore = Boolean(data.has_more);
      syncMaxId();
      if (data.max_alert_id != null) {
        state.maxAlertId = Math.max(state.maxAlertId, data.max_alert_id);
      }
      renderAlertsBody();
    } finally {
      state.loading = false;
      void pollNewAlerts();
    }
  }

  async function loadOlderAlerts() {
    if (state.loading || state.loadingMore || !state.hasMore || !state.items.length) return;
    const oldest = state.items[state.items.length - 1]?.alert_id;
    if (!oldest) return;
    state.loadingMore = true;
    const sentinel = document.getElementById("alerts-load-sentinel");
    sentinel?.classList.add("is-loading");
    try {
      const data = await fetchAlertsPage({ before_id: oldest });
      const batch = data.items || [];
      const existing = new Set(state.items.map((r) => r.alert_id));
      batch.forEach((r) => {
        if (!existing.has(r.alert_id)) state.items.push(r);
      });
      state.hasMore = Boolean(data.has_more);
      renderAlertsBody();
    } finally {
      state.loadingMore = false;
      sentinel?.classList.remove("is-loading");
    }
  }

  async function pollNewAlerts() {
    if (state.loading || state.polling) return;
    if (document.hidden) return;
    state.polling = true;
    try {
      const since = state.maxAlertId || 0;
      const data = await fetchAlertsPage({ since_id: since, limit: 25, live: true });
      const batch = data.items || [];
      if (batch.length) prependAlerts(batch);
      if (data.max_alert_id != null) {
        state.maxAlertId = Math.max(state.maxAlertId, data.max_alert_id);
      }
      if (batch.length && typeof window.loadOverview === "function") {
        await window.loadOverview(true);
      }
    } catch {
      /* ignore transient poll errors */
    } finally {
      state.polling = false;
    }
  }

  function ensureScrollObserver() {
    const root = document.getElementById("alerts-scroll");
    const sentinel = document.getElementById("alerts-load-sentinel");
    if (!root || !sentinel || state.observer) return;
    state.observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) void loadOlderAlerts();
      },
      { root, rootMargin: "120px", threshold: 0.01 }
    );
    state.observer.observe(sentinel);
  }

  function startPolling() {
    stopPolling();
    state.pollTimer = setInterval(() => void pollNewAlerts(), POLL_MS);
  }

  function stopPolling() {
    if (state.pollTimer) clearInterval(state.pollTimer);
    state.pollTimer = null;
  }

  function initAlertsPanel() {
    ensureScrollObserver();
    startPolling();
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) void pollNewAlerts();
    });
    document.addEventListener("activity-time-filter", () => {
      updateTimelineFilterNotice();
      void resetAndLoadAlerts();
    });
  }

  window.alertsPanel = {
    resetAndLoadAlerts,
    pollNewAlerts,
    initAlertsPanel,
    stopPolling,
  };

  window.loadAlertsFromUi = resetAndLoadAlerts;
})();
