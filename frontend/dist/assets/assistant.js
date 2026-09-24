/* global window, document, localStorage, fetch, alert, FormData */
(function () {
  const STORAGE_KEY = "banking-control-assistant-open";

  function parseSseBlock(block) {
    let event = "message";
    const dataLines = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }
    if (!dataLines.length) return null;
    return { event, data: dataLines.join("\n") };
  }

  async function postAssistantStream(message, handlers) {
    const res = await fetch("/api/assistant/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(detail || res.statusText);
    }
    if (!res.body) throw new Error("Streaming not supported");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let raw = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        const parsed = parseSseBlock(part.trim());
        if (!parsed) continue;
        let payload;
        try {
          payload = JSON.parse(parsed.data);
        } catch {
          continue;
        }
        if (parsed.event === "meta") handlers.onMeta?.(payload);
        else if (parsed.event === "delta" && payload.text) {
          raw += payload.text;
          handlers.onDelta?.(payload.text, raw);
        } else if (parsed.event === "done") handlers.onDone?.(payload);
        else if (parsed.event === "error") throw new Error(payload.detail || "Stream error");
      }
    }
  }

  function setCopilotOpen(rail, panel, toggle, open) {
    if (!rail || !panel) return;
    rail.classList.toggle("is-open", open);
    rail.classList.toggle("is-closed", !open);
    document.body.classList.toggle("copilot-open", open);
    panel.setAttribute("aria-hidden", open ? "false" : "true");
    if (toggle) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Close control assistant" : "Open control assistant");
      toggle.title = open ? "Close assistant" : "Open assistant";
    }
    localStorage.setItem(STORAGE_KEY, open ? "1" : "0");
  }

  function setAdminMenuOpen(menuPanel, menuToggle, open) {
    if (!menuPanel || !menuToggle) return;
    menuPanel.classList.toggle("hidden", !open);
    menuToggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function initBankingAssistant() {
    if (window.__bankingAssistantInit) return;
    window.__bankingAssistantInit = true;

    const rail = document.getElementById("copilot-rail");
    const panel = document.getElementById("assistant-panel");
    const toggle = document.getElementById("assistant-toggle");
    const history = document.getElementById("assistant-history");
    const form = document.getElementById("assistant-form");
    const input = document.getElementById("assistant-input");
    const statusEl = document.getElementById("assistant-status");
    const adminMenuToggle = document.getElementById("admin-menu-toggle");
    const adminMenuPanel = document.getElementById("admin-menu-panel");
    const adminForm = document.getElementById("admin-llm-form");

    if (!panel || !toggle || !rail) return;

    const shouldOpen = localStorage.getItem(STORAGE_KEY) === "1";
    setCopilotOpen(rail, panel, toggle, shouldOpen);

    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      const open = !rail.classList.contains("is-open");
      setCopilotOpen(rail, panel, toggle, open);
    });

    adminMenuToggle?.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = adminMenuPanel?.classList.contains("hidden");
      setAdminMenuOpen(adminMenuPanel, adminMenuToggle, Boolean(open));
    });

    document.addEventListener("click", (e) => {
      if (!adminMenuPanel || adminMenuPanel.classList.contains("hidden")) return;
      if (e.target.closest("#admin-icon-menu")) return;
      setAdminMenuOpen(adminMenuPanel, adminMenuToggle, false);
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && adminMenuPanel && !adminMenuPanel.classList.contains("hidden")) {
        setAdminMenuOpen(adminMenuPanel, adminMenuToggle, false);
        adminMenuToggle?.focus();
      }
    });

    function renderActionChips(container, actions) {
      if (!container || !actions?.length) return;
      const row = document.createElement("div");
      row.className = "assistant-actions";
      actions.forEach((action) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "assistant-action-chip";
        btn.textContent = action.label || "Open";
        btn.addEventListener("click", () => void executeAssistantAction(action));
        row.appendChild(btn);
      });
      container.appendChild(row);
    }

    async function executeAssistantAction(action) {
      const dash = window.dashboardAssistant;
      if (!dash || !action?.action_type) return;
      const payload = action.payload || {};
      switch (action.action_type) {
        case "metric_filter":
          await dash.applyMetricFilter?.(payload.filter_id);
          break;
        case "focus_panel":
          dash.focusPanel?.(payload.panel_id);
          break;
        case "filter_controls":
          await dash.filterControls?.(payload);
          break;
        case "filter_alerts":
          await dash.filterAlerts?.(payload);
          break;
        case "open_detail":
          dash.openDetail?.(payload.kind, payload.id);
          break;
        default:
          break;
      }
    }

    function appendMessage(role, text, actions) {
      const wrap = document.createElement("div");
      wrap.className = `assistant-msg assistant-msg-${role}`;
      const roleEl = document.createElement("div");
      roleEl.className = "assistant-msg-role";
      roleEl.textContent = role === "user" ? "You" : "Assistant";
      const textEl = document.createElement("div");
      textEl.className = "assistant-msg-text";
      if (typeof window.setAssistantMessageBody === "function") {
        window.setAssistantMessageBody(textEl, role, text);
      } else {
        textEl.textContent = text;
      }
      wrap.appendChild(roleEl);
      wrap.appendChild(textEl);
      renderActionChips(wrap, actions);
      const metaEl = document.createElement("div");
      metaEl.className = "assistant-msg-meta";
      wrap.appendChild(metaEl);
      history?.appendChild(wrap);
      if (history) {
        history.scrollTop = history.scrollHeight;
      }
      return wrap;
    }

    async function showStarterPrompt() {
      if (!history || history.querySelector(".assistant-starter-wrap")) return;
      try {
        const res = await fetch("/api/assistant/starters");
        if (!res.ok) return;
        const data = await res.json();
        const wrap = document.createElement("div");
        wrap.className = "assistant-starter-wrap assistant-msg assistant-msg-assistant";
        const roleEl = document.createElement("div");
        roleEl.className = "assistant-msg-role";
        roleEl.textContent = "Assistant";
        const textEl = document.createElement("div");
        textEl.className = "assistant-msg-text";
        if (typeof window.setAssistantMessageBody === "function") {
          window.setAssistantMessageBody(textEl, "assistant", data.answer || "");
        } else {
          textEl.textContent = data.answer || "";
        }
        wrap.appendChild(roleEl);
        wrap.appendChild(textEl);
        renderActionChips(wrap, data.actions);
        history.appendChild(wrap);
      } catch {
        /* optional */
      }
    }

    async function refreshAssistantStatus() {
      if (!statusEl) return;
      try {
        const res = await fetch("/api/admin/assistant/status");
        const data = await res.json();
        statusEl.textContent = data.llm_configured
          ? `LLM ready (${data.provider})`
          : "LLM not configured — use ⚙ in header";
        statusEl.className = `pill ${data.llm_configured ? "pill-ok" : "pill-warn"}`;
        window.loadStatusChips?.();
      } catch {
        statusEl.textContent = "Assistant status unknown";
        statusEl.className = "pill pill-muted";
      }
    }

    function setField(name, value) {
      const el = adminForm?.querySelector(`[name="${name}"]`);
      if (el) el.value = value ?? "";
    }

    async function loadAdminConfig() {
      if (!adminForm) return;
      try {
        const res = await fetch("/api/admin/llm");
        if (!res.ok) return;
        const cfg = await res.json();
        setField("provider_type", cfg.provider_type || "bedrock");
        setField("bedrock_region", cfg.bedrock_region);
        setField("bedrock_model_id", cfg.bedrock_model_id);
        setField("bedrock_max_tokens", cfg.bedrock_max_tokens ?? "");
        setField("bedrock_temperature", cfg.bedrock_temperature ?? "");
        setField("openai_base_url", cfg.openai_base_url);
        setField("openai_model_id", cfg.openai_model_id);
        const tokenInput = adminForm.querySelector('[name="openai_api_token"]');
        if (tokenInput) {
          tokenInput.placeholder = cfg.openai_api_token_set
            ? "Token saved (leave blank to keep)"
            : "Bearer token";
        }
      } catch {
        /* optional */
      }
    }

    adminForm?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(adminForm);
      const payload = Object.fromEntries(fd.entries());
      if (payload.bedrock_max_tokens) payload.bedrock_max_tokens = Number(payload.bedrock_max_tokens);
      else delete payload.bedrock_max_tokens;
      if (payload.bedrock_temperature) payload.bedrock_temperature = Number(payload.bedrock_temperature);
      else delete payload.bedrock_temperature;
      if (!payload.openai_api_token) delete payload.openai_api_token;
      const res = await fetch("/api/admin/llm", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        alert(await res.text());
        return;
      }
      await loadAdminConfig();
      await refreshAssistantStatus();
      window.loadStatusChips?.();
    });

    document.getElementById("admin-llm-test")?.addEventListener("click", async () => {
      if (!adminForm) return;
      const fd = new FormData(adminForm);
      const payload = Object.fromEntries(fd.entries());
      const res = await fetch("/api/admin/llm/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      alert(data.ok ? `OK: ${data.detail || data.message}` : data.message);
    });

    let sending = false;

    async function submitChat() {
      if (!input || sending) return;
      const message = input.value.trim();
      if (!message) return;
      input.value = "";
      history?.querySelector(".assistant-starter-wrap")?.remove();
      appendMessage("user", message);
      const assistantNode = appendMessage("assistant", "…");
      const textNode = assistantNode.querySelector(".assistant-msg-text");
      const metaNode = assistantNode.querySelector(".assistant-msg-meta");
      sending = true;
      form?.querySelector('button[type="submit"]')?.setAttribute("disabled", "true");
      try {
        await postAssistantStream(message, {
          onMeta: (m) => {
            if (textNode) {
              textNode.classList.remove("assistant-markdown");
              textNode.textContent = m.status || "Working…";
            }
          },
          onDelta: (_piece, buffer) => {
            if (textNode && typeof window.setAssistantMessageBody === "function") {
              window.setAssistantMessageBody(textNode, "assistant", buffer);
            } else if (textNode) {
              textNode.textContent = buffer;
            }
            if (history) history.scrollTop = history.scrollHeight;
          },
          onDone: (done) => {
            if (textNode && typeof window.setAssistantMessageBody === "function") {
              window.setAssistantMessageBody(textNode, "assistant", done.answer || "");
            } else if (textNode) {
              textNode.textContent = done.answer || "";
            }
            renderActionChips(assistantNode, done.actions);
            if (metaNode) {
              metaNode.textContent = [
                done.provider,
                done.model_id,
                done.tools_called?.length ? `tools: ${done.tools_called.join(", ")}` : "",
              ]
                .filter(Boolean)
                .join(" · ");
            }
          },
        });
      } catch (err) {
        if (textNode) {
          textNode.textContent = err instanceof Error ? err.message : "Chat failed";
        }
      } finally {
        sending = false;
        form?.querySelector('button[type="submit"]')?.removeAttribute("disabled");
      }
    }

    form?.addEventListener("submit", (e) => {
      e.preventDefault();
      void submitChat();
    });

    input?.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" || e.shiftKey || e.isComposing) return;
      e.preventDefault();
      void submitChat();
    });

    void refreshAssistantStatus();
    void loadAdminConfig();
    void showStarterPrompt();
  }

  window.initBankingAssistant = initBankingAssistant;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBankingAssistant);
  } else {
    initBankingAssistant();
  }
})();
