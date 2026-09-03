const API_BASE = "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail ?? response.statusText;
    const message = typeof detail === "string" ? detail : JSON.stringify(detail);
    throw new Error(message);
  }

  return data;
}

export async function fetchHealth() {
  return request("/health");
}

export async function fetchModels() {
  return request("/models");
}

export async function fetchConfig() {
  return request("/config");
}

export async function updateConfig(updates) {
  return request("/config", {
    method: "PUT",
    body: JSON.stringify(updates),
  });
}

export async function sendChat(payload) {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
