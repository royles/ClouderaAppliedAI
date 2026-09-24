const ASSISTANT_STORAGE_KEY = "banking-control-assistant-open";

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

export async function postAssistantStream(message, handlers) {
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

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

export function initAssistant() {
  const panel = document.getElementById("assistant-panel");
  const toggle = document.getElementById("assistant-toggle");
  const history = document.getElementById("assistant-history");
  const form = document.getElementById("assistant-form");
  const input = document.getElementById("assistant-input");
  const statusEl = document.getElementById("assistant-status");
  const adminToggle = document.getElementById("assistant-admin-toggle");
  const adminPanel = document.getElementById("assistant-admin");
  const adminForm = document.getElementById("admin-llm-form");
  if (!panel || !toggle || !history || !form || !input) return;

  const open = localStorage.getItem(ASSISTANT_STORAGE_KEY) === "1";
  panel.classList.toggle("collapsed", !open);
  panel.setAttribute("aria-hidden", open ? "false" : "true");

  toggle.addEventListener("click", () => {
    const collapsed = panel.classList.toggle("collapsed");
    panel.setAttribute("aria-hidden", collapsed ? "true" : "false");
    localStorage.setItem(ASSISTANT_STORAGE_KEY, collapsed ? "0" : "1");
  });

  adminToggle?.addEventListener("click", () => {
    adminPanel?.classList.toggle("hidden");
  });

  function appendMessage(role, text, meta = "") {
    const wrap = el("div", `assistant-msg assistant-msg-${role}`);
    wrap.appendChild(el("div", "assistant-msg-role", role === "user" ? "You" : "Assistant"));
    wrap.appendChild(el("div", "assistant-msg-text", text));
    if (meta) wrap.appendChild(el("div", "assistant-msg-meta", meta));
    history.appendChild(wrap);
    history.scrollTop = history.scrollHeight;
    return wrap;
  }

  async function refreshAssistantStatus() {
    try {
      const res = await fetch("/api/admin/assistant/status");
      const data = await res.json();
      statusEl.textContent = data.llm_configured
        ? `LLM ready (${data.provider})`
        : "LLM not configured — open Admin";
      statusEl.className = `pill ${data.llm_configured ? "pill-ok" : "pill-warn"}`;
    } catch {
      statusEl.textContent = "Assistant status unknown";
    }
  }

  async function loadAdminConfig() {
    if (!adminForm) return;
    const res = await fetch("/api/admin/llm");
    const cfg = await res.json();
    adminForm.provider_type.value = cfg.provider_type || "bedrock";
    adminForm.bedrock_region.value = cfg.bedrock_region || "";
    adminForm.bedrock_model_id.value = cfg.bedrock_model_id || "";
    adminForm.bedrock_max_tokens.value = cfg.bedrock_max_tokens ?? "";
    adminForm.bedrock_temperature.value = cfg.bedrock_temperature ?? "";
    adminForm.openai_base_url.value = cfg.openai_base_url || "";
    adminForm.openai_model_id.value = cfg.openai_model_id || "";
    adminForm.openai_api_token.placeholder = cfg.openai_api_token_set
      ? "Token saved (leave blank to keep)"
      : "Bearer token";
  }

  adminForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(adminForm);
    const payload = Object.fromEntries(fd.entries());
    payload.bedrock_max_tokens = payload.bedrock_max_tokens
      ? Number(payload.bedrock_max_tokens)
      : null;
    payload.bedrock_temperature = payload.bedrock_temperature
      ? Number(payload.bedrock_temperature)
      : null;
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

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    appendMessage("user", message);
    const assistantNode = appendMessage("assistant", "…");
    const textNode = assistantNode.querySelector(".assistant-msg-text");
    let sending = true;
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
          const meta = assistantNode.querySelector(".assistant-msg-meta");
          if (meta) {
            meta.textContent = [
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
      if (textNode) textNode.textContent = err instanceof Error ? err.message : "Chat failed";
    } finally {
      sending = false;
      form.querySelector("button")?.removeAttribute("disabled");
    }
  });

  void refreshAssistantStatus();
  void loadAdminConfig();
}
