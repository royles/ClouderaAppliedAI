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

  function setPanelOpen(panel, toggle, open) {
    panel.classList.toggle("is-open", open);
    document.body.classList.toggle("assistant-open", open);
    panel.setAttribute("aria-hidden", open ? "false" : "true");
    if (toggle) toggle.setAttribute("aria-expanded", open ? "true" : "false");
    localStorage.setItem(STORAGE_KEY, open ? "1" : "0");
  }

  function initBankingAssistant() {
    if (window.__bankingAssistantInit) return;
    window.__bankingAssistantInit = true;

    const panel = document.getElementById("assistant-panel");
    const toggle = document.getElementById("assistant-toggle");
    const backdrop = document.getElementById("assistant-backdrop");
    const history = document.getElementById("assistant-history");
    const form = document.getElementById("assistant-form");
    const input = document.getElementById("assistant-input");
    const statusEl = document.getElementById("assistant-status");
    const adminToggle = document.getElementById("assistant-admin-toggle");
    const adminPanel = document.getElementById("assistant-admin");
    const adminForm = document.getElementById("admin-llm-form");

    if (!panel || !toggle) return;

    const shouldOpen = localStorage.getItem(STORAGE_KEY) === "1";
    setPanelOpen(panel, toggle, shouldOpen);

    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      const open = !panel.classList.contains("is-open");
      setPanelOpen(panel, toggle, open);
    });

    backdrop?.addEventListener("click", () => setPanelOpen(panel, toggle, false));

    adminToggle?.addEventListener("click", () => {
      adminPanel?.classList.toggle("hidden");
    });

    function appendMessage(role, text) {
      const wrap = document.createElement("div");
      wrap.className = `assistant-msg assistant-msg-${role}`;
      const roleEl = document.createElement("div");
      roleEl.className = "assistant-msg-role";
      roleEl.textContent = role === "user" ? "You" : "Assistant";
      const textEl = document.createElement("div");
      textEl.className = "assistant-msg-text";
      textEl.textContent = text;
      wrap.appendChild(roleEl);
      wrap.appendChild(textEl);
      const metaEl = document.createElement("div");
      metaEl.className = "assistant-msg-meta";
      wrap.appendChild(metaEl);
      history?.appendChild(wrap);
      if (history) history.scrollTop = history.scrollHeight;
      return wrap;
    }

    async function refreshAssistantStatus() {
      if (!statusEl) return;
      try {
        const res = await fetch("/api/admin/assistant/status");
        const data = await res.json();
        statusEl.textContent = data.llm_configured
          ? `LLM ready (${data.provider})`
          : "LLM not configured — open Admin";
        statusEl.className = `pill ${data.llm_configured ? "pill-ok" : "pill-warn"}`;
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
        /* admin optional */
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

    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!input) return;
      const message = input.value.trim();
      if (!message) return;
      input.value = "";
      appendMessage("user", message);
      const assistantNode = appendMessage("assistant", "…");
      const textNode = assistantNode.querySelector(".assistant-msg-text");
      const metaNode = assistantNode.querySelector(".assistant-msg-meta");
      form.querySelector("button")?.setAttribute("disabled", "true");
      try {
        await postAssistantStream(message, {
          onMeta: (m) => {
            if (textNode) textNode.textContent = m.status || "Working…";
          },
          onDelta: (_piece, buffer) => {
            if (textNode) textNode.textContent = buffer;
          },
          onDone: (done) => {
            if (textNode) textNode.textContent = done.answer || "";
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
        form.querySelector("button")?.removeAttribute("disabled");
      }
    });

    void refreshAssistantStatus();
    void loadAdminConfig();
  }

  window.initBankingAssistant = initBankingAssistant;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBankingAssistant);
  } else {
    initBankingAssistant();
  }
})();
