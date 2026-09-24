(function () {
  /** @type {{ from: string|null, to: string|null }} */
  const activityTimeFilter = { from: null, to: null };

  let buckets = [];
  let granularity = "auto";
  let viewStart = 0;
  let dragging = null;
  let brushStartIdx = null;
  let brushEndIdx = null;

  const VISIBLE_BUCKETS = 18;
  const CHART_HEIGHT = 120;

  function api(path) {
    return fetch(path).then(async (res) => {
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    });
  }

  function dispatchFilterChange() {
    window.activityTimeFilter = { ...activityTimeFilter };
    document.dispatchEvent(
      new CustomEvent("activity-time-filter", { detail: { ...activityTimeFilter } })
    );
    updateFilterSummary();
    highlightPanels();
  }

  function updateFilterSummary() {
    const el = document.getElementById("timeline-range-label");
    if (!el) return;
    if (!activityTimeFilter.from && !activityTimeFilter.to) {
      el.textContent = "All dates · drag chart or handles to filter alerts & audit";
      return;
    }
    if (activityTimeFilter.from && activityTimeFilter.to) {
      if (activityTimeFilter.from === activityTimeFilter.to) {
        el.textContent = `Selected ${activityTimeFilter.from} · filtering transactions & audit`;
      } else {
        el.textContent = `${activityTimeFilter.from} → ${activityTimeFilter.to} · filtering transactions & audit`;
      }
      return;
    }
    el.textContent = `${activityTimeFilter.from || "…"} → ${activityTimeFilter.to || "…"}`;
  }

  function highlightPanels() {
    const active = Boolean(activityTimeFilter.from || activityTimeFilter.to);
    document.getElementById("panel-alerts")?.classList.toggle("panel-time-filter", active);
    document.getElementById("panel-audit")?.classList.toggle("panel-time-filter", active);
  }

  function applyBucketRange(fromIdx, toIdx) {
    const a = Math.min(fromIdx, toIdx);
    const b = Math.max(fromIdx, toIdx);
    const start = buckets[a];
    const end = buckets[b];
    if (!start || !end) return;
    activityTimeFilter.from = start.period_start;
    activityTimeFilter.to = end.period_end;
    brushStartIdx = a;
    brushEndIdx = b;
    dispatchFilterChange();
    drawChart();
  }

  function clearFilter() {
    activityTimeFilter.from = null;
    activityTimeFilter.to = null;
    brushStartIdx = null;
    brushEndIdx = null;
    dispatchFilterChange();
    drawChart();
  }

  function indexFromX(canvas, clientX, visible) {
    const rect = canvas.getBoundingClientRect();
    const x = clientX - rect.left;
    const barW = rect.width / visible.length;
    const idx = viewStart + Math.floor(x / barW);
    return Math.max(viewStart, Math.min(viewStart + visible.length - 1, idx));
  }

  function drawChart() {
    const canvas = document.getElementById("activity-timeline-canvas");
    const scroll = document.getElementById("timeline-scroll");
    if (!canvas || !scroll) return;

    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(CHART_HEIGHT * dpr);
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, CHART_HEIGHT);

    if (!buckets.length) {
      ctx.fillStyle = "#93a4bc";
      ctx.font = "13px DM Sans, system-ui, sans-serif";
      ctx.fillText("No activity in warehouse yet", 12, 48);
      scroll.innerHTML = "";
      return;
    }

    const maxView = Math.max(1, buckets.length - VISIBLE_BUCKETS + 1);
    viewStart = Math.max(0, Math.min(viewStart, maxView - 1));
    const visible = buckets.slice(viewStart, viewStart + VISIBLE_BUCKETS);
    const maxTotal = Math.max(1, ...visible.map((b) => b.total));

    const padL = 8;
    const padR = 8;
    const padT = 12;
    const padB = 28;
    const chartW = width - padL - padR;
    const chartH = CHART_HEIGHT - padT - padB;
    const gap = 4;
    const barW = chartW / visible.length - gap;

    visible.forEach((b, i) => {
      const x = padL + i * (barW + gap);
      const alertH = (b.alerts / maxTotal) * chartH;
      const auditH = (b.audit_events / maxTotal) * chartH;
      const baseY = padT + chartH;

      ctx.fillStyle = "rgba(61, 214, 195, 0.85)";
      ctx.fillRect(x, baseY - alertH, barW / 2 - 1, alertH);
      ctx.fillStyle = "rgba(245, 185, 66, 0.9)";
      ctx.fillRect(x + barW / 2 + 1, baseY - auditH, barW / 2 - 1, auditH);

      const globalIdx = viewStart + i;
      const selected =
        brushStartIdx != null &&
        brushEndIdx != null &&
        globalIdx >= Math.min(brushStartIdx, brushEndIdx) &&
        globalIdx <= Math.max(brushStartIdx, brushEndIdx);
      if (selected) {
        ctx.fillStyle = "rgba(61, 214, 195, 0.18)";
        ctx.fillRect(x - 1, padT, barW + 2, chartH);
        ctx.strokeStyle = "#3dd6c3";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(x - 1, padT, barW + 2, chartH);
      }

      ctx.fillStyle = "#93a4bc";
      ctx.font = "10px DM Sans, system-ui, sans-serif";
      ctx.textAlign = "center";
      const label = b.label.length > 8 ? b.label.slice(0, 7) + "…" : b.label;
      ctx.fillText(label, x + barW / 2, CHART_HEIGHT - 6);
    });

    renderScrollTrack(maxView);
  }

  function renderScrollTrack(maxView) {
    const scroll = document.getElementById("timeline-scroll");
    if (!scroll) return;
    if (buckets.length <= VISIBLE_BUCKETS) {
      scroll.innerHTML = `<div class="timeline-scroll-hint">Showing all ${buckets.length} periods</div>`;
      return;
    }
    const pct = maxView > 1 ? (viewStart / (maxView - 1)) * 100 : 0;
    const thumbW = Math.max(12, (VISIBLE_BUCKETS / buckets.length) * 100);
    scroll.innerHTML = `
      <div class="timeline-scroll-track" id="timeline-scroll-track">
        <div class="timeline-scroll-mini">
          ${buckets
            .map((b) => {
              const h = Math.min(100, 8 + b.total * 3);
              return `<span style="height:${h}%" title="${b.label}: ${b.total}"></span>`;
            })
            .join("")}
        </div>
        <div class="timeline-scroll-thumb" id="timeline-scroll-thumb" style="left:${pct}%;width:${thumbW}%"></div>
      </div>
      <p class="timeline-scroll-hint">Scroll chart or drag track · ${buckets.length} periods aggregated server-side</p>`;

    const track = document.getElementById("timeline-scroll-track");
    const thumb = document.getElementById("timeline-scroll-thumb");
    if (!track || !thumb) return;

    track.addEventListener("click", (e) => {
      if (e.target === thumb) return;
      const rect = track.getBoundingClientRect();
      const ratio = (e.clientX - rect.left) / rect.width;
      const maxViewLocal = Math.max(1, buckets.length - VISIBLE_BUCKETS + 1);
      viewStart = Math.round(ratio * (maxViewLocal - 1));
      drawChart();
    });
  }

  async function loadTimelineData() {
    const params = new URLSearchParams();
    params.set("granularity", granularity);
    const data = await api(`/api/activity-timeline?${params}`);
    buckets = data.buckets || [];
    const granEl = document.getElementById("timeline-granularity");
    if (granEl && granularity === "auto") {
      granEl.value = "auto";
    }
    const meta = document.getElementById("timeline-meta");
    if (meta) {
      meta.textContent = `${data.totals?.combined ?? 0} events · ${data.granularity} buckets · scales via SQL aggregates`;
    }
    viewStart = Math.max(0, buckets.length - VISIBLE_BUCKETS);
    drawChart();
  }

  function setupCanvasInteractions() {
    const canvas = document.getElementById("activity-timeline-canvas");
    if (!canvas) return;

    canvas.addEventListener("wheel", (e) => {
      if (buckets.length <= VISIBLE_BUCKETS) return;
      e.preventDefault();
      const maxView = Math.max(1, buckets.length - VISIBLE_BUCKETS + 1);
      viewStart = Math.max(0, Math.min(maxView - 1, viewStart + (e.deltaY > 0 ? 1 : -1)));
      drawChart();
    }, { passive: false });

    canvas.addEventListener("mousedown", (e) => {
      if (!buckets.length) return;
      const visible = buckets.slice(viewStart, viewStart + VISIBLE_BUCKETS);
      const idx = indexFromX(canvas, e.clientX, visible);
      dragging = { startIdx: idx, currentIdx: idx, moved: false };
    });

    window.addEventListener("mousemove", (e) => {
      if (!dragging) return;
      const canvas = document.getElementById("activity-timeline-canvas");
      if (!canvas) return;
      const visible = buckets.slice(viewStart, viewStart + VISIBLE_BUCKETS);
      const idx = indexFromX(canvas, e.clientX, visible);
      if (idx !== dragging.currentIdx) dragging.moved = true;
      dragging.currentIdx = idx;
      brushStartIdx = dragging.startIdx;
      brushEndIdx = dragging.currentIdx;
      drawChart();
    });

    window.addEventListener("mouseup", () => {
      if (!dragging) return;
      applyBucketRange(dragging.startIdx, dragging.currentIdx);
      dragging = null;
    });
  }

  function setupBrushHandles() {
    const left = document.getElementById("timeline-brush-left");
    const right = document.getElementById("timeline-brush-right");
    if (!left || !right) return;

    const onHandle = (side) => (e) => {
      e.preventDefault();
      if (!buckets.length) return;
      if (brushStartIdx == null || brushEndIdx == null) {
        brushStartIdx = 0;
        brushEndIdx = buckets.length - 1;
      }
      const move = (ev) => {
        const canvas = document.getElementById("activity-timeline-canvas");
        if (!canvas) return;
        const visible = buckets.slice(viewStart, viewStart + VISIBLE_BUCKETS);
        const idx = indexFromX(canvas, ev.clientX, visible);
        if (side === "left") {
          brushStartIdx = Math.min(idx, brushEndIdx);
        } else {
          brushEndIdx = Math.max(idx, brushStartIdx);
        }
        applyBucketRange(brushStartIdx, brushEndIdx);
      };
      const up = () => {
        window.removeEventListener("mousemove", move);
        window.removeEventListener("mouseup", up);
      };
      window.addEventListener("mousemove", move);
      window.addEventListener("mouseup", up);
    };

    left.addEventListener("mousedown", onHandle("left"));
    right.addEventListener("mousedown", onHandle("right"));
  }

  function initActivityTimeline() {
    window.activityTimeFilter = activityTimeFilter;

    document.getElementById("timeline-clear")?.addEventListener("click", clearFilter);
    document.getElementById("timeline-granularity")?.addEventListener("change", (e) => {
      granularity = e.target.value;
      void loadTimelineData();
    });

    setupCanvasInteractions();
    setupBrushHandles();
    updateFilterSummary();

    window.addEventListener("resize", () => drawChart());

    void loadTimelineData();
  }

  window.initActivityTimeline = initActivityTimeline;
  window.reloadActivityTimeline = loadTimelineData;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initActivityTimeline);
  } else {
    initActivityTimeline();
  }
})();
