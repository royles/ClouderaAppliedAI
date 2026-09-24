(function () {
  const PAGE_SIZE = 35;
  const POLL_MS = 5000;

  const state = {
    items: [],
    hasMore: true,
    loading: false,
    loadingMore: false,
    polling: false,
    /** Highest alert_id the server reported (live poll cursor). */
    lastGlobalAlertId: 0,
    observer: null,
    pollTimer: null,
  };

  function alertId(r) {
    return Number(r.alert_id);
  }

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
    const live = Boolean(extra.live);
    const statusFilter = window.getAlertStatusFilter?.();
    if (statusFilter && !live) params.set("status", statusFilter);
    if (!live && typeof window.appendActivityTimeParams === "function") {
      window.appendActivityTimeParams(params);
    }
    if (live) params.set("live", "true");
    Object.entries(extra).forEach(([k, v]) => {
      if (k === "live" || k === "limit") return;
      if (v != null) params.set(k, String(v));
    });
    return params;
  }

  function sortNewestFirst(rows) {
    return rows.slice().sort((a, b) => alertId(b) - alertId(a));
  }

  function alertPassesUiFilters(r) {
    const minRisk = Number(document.getElementById("risk-slider")?.value || 0) / 100;
    if (Number(r.risk_score) < minRisk) return false;
    const statusFilter = window.getAlertStatusFilter?.();
    if (statusFilter && r.status !== statusFilter) return false;
    const tf = window.activityTimeFilter;
    if (tf?.from || tf?.to) {
      const day = String(r.alert_at || "").slice(0, 10);
      if (tf.from && day < tf.from) return false;
      if (tf.to && day > tf.to) return false;
    }
    return true;
  }

  async function fetchAlertsPage(extra = {}) {
    const params = buildAlertParams(extra);
    const res = await fetch(`/api/alerts?${params}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  function applyServerMax(data) {
    if (data?.max_alert_id != null) {
      state.lastGlobalAlertId = Math.max(state.lastGlobalAlertId, Number(data.max_alert_id));
    }
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

  function updateMeta(extra = "") {
    const meta = document.getElementById("alerts-stream-meta");
    if (!meta) return;
    if (!state.items.length) {
      meta.textContent = extra || "";
      return;
    }
    meta.textContent = `${state.items.length} loaded${state.hasMore ? " · scroll for more" : ""}${extra ? ` · ${extra}` : ""}`;
  }

  function renderAlertsBody() {
    const body = document.getElementById("alerts-body");
    updateTimelineFilterNotice();
    if (!body) return;
    if (!state.items.length) {
      body.innerHTML = `<tr><td colspan="5" class="empty">No alerts at this risk threshold</td></tr>`;
    } else {
      body.innerHTML = state.items.map((r) => alertRowHtml(r)).join("");
    }
    updateMeta();
    const sentinel = document.getElementById("alerts-load-sentinel");
    sentinel?.classList.toggle("hidden", !state.hasMore);
  }

  function prependAlerts(rows) {
    if (!rows.length) return 0;
    const existing = new Set(state.items.map((r) => alertId(r)));
    const fresh = sortNewestFirst(rows.filter((r) => !existing.has(alertId(r)) && alertPassesUiFilters(r)));
    if (!fresh.length) return 0;

    const scrollRoot = document.getElementById("alerts-scroll");
    const stickToTop = scrollRoot ? scrollRoot.scrollTop < 120 : true;

    state.items = [...fresh, ...state.items];
    const body = document.getElementById("alerts-body");
    if (!body) return fresh.length;
    body.querySelector("tr.empty")?.remove();
    if (!body.querySelector("tr[data-alert-id]")) {
      renderAlertsBody();
      return fresh.length;
    }
    fresh
      .slice()
      .reverse()
      .forEach((r) => {
        body.insertAdjacentHTML("afterbegin", alertRowHtml(r, "alert-row-enter"));
      });

    if (stickToTop && scrollRoot) {
      scrollRoot.scrollTo({ top: 0, behavior: "smooth" });
    }
    updateMeta(`${fresh.length} new at top`);
    return fresh.length;
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
      applyServerMax(data);
      renderAlertsBody();
    } finally {
      state.loading = false;
      void pollNewAlerts();
    }
  }

  async function loadOlderAlerts() {
    if (state.loading || state.loadingMore || !state.hasMore || !state.items.length) return;
    const oldest = alertId(state.items[state.items.length - 1]);
    if (!oldest) return;
    state.loadingMore = true;
    const sentinel = document.getElementById("alerts-load-sentinel");
    sentinel?.classList.add("is-loading");
    try {
      const data = await fetchAlertsPage({ before_id: oldest });
      const batch = data.items || [];
      const existing = new Set(state.items.map((r) => alertId(r)));
      batch.forEach((r) => {
        if (!existing.has(alertId(r))) state.items.push(r);
      });
      state.hasMore = Boolean(data.has_more);
      applyServerMax(data);
      renderAlertsBody();
    } finally {
      state.loadingMore = false;
      sentinel?.classList.remove("is-loading");
    }
  }

  async function pollNewAlerts() {
    if (state.loading || state.polling) return;
    state.polling = true;
    try {
      const since = state.lastGlobalAlertId || 0;
      const data = await fetchAlertsPage({ since_id: since, limit: 30, live: true });
      applyServerMax(data);
      const batch = data.items || [];
      const added = prependAlerts(batch);
      if (added > 0 && typeof window.loadOverview === "function") {
        await window.loadOverview(true);
      }
    } catch (err) {
      console.warn("alerts live poll failed", err);
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
    void pollNewAlerts();
  }

  function stopPolling() {
    if (state.pollTimer) clearInterval(state.pollTimer);
    state.pollTimer = null;
  }

  function initAlertsPanel() {
    if (!document.getElementById("alerts-body")) return;
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      initAlertsPanel();
    });
  } else {
    initAlertsPanel();
  }
})();
