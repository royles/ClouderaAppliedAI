import { apiUrl } from "./apiBase";

export type SseHandlers<TDone> = {
  onMeta?: (payload: Record<string, unknown>) => void;
  onDelta?: (text: string, buffer: string) => void;
  onDone: (payload: TDone) => void;
  onError?: (detail: string) => void;
};

function dispatchSseEvent<TDone>(
  event: string,
  payload: Record<string, unknown>,
  handlers: SseHandlers<TDone>,
  rawRef: { value: string },
): void {
  if (event === "meta") {
    handlers.onMeta?.(payload);
  } else if (event === "delta" && typeof payload.text === "string") {
    rawRef.value += payload.text;
    handlers.onDelta?.(payload.text, rawRef.value);
  } else if (event === "done") {
    handlers.onDone(payload as TDone);
  } else if (event === "error") {
    const detail = String(payload.detail ?? "Stream error");
    handlers.onError?.(detail);
    throw new Error(detail);
  }
}

function parseSseBlock(block: string): { event: string; data: string } | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (!dataLines.length) return null;
  return { event, data: dataLines.join("\n") };
}

export async function postSseStream<TDone>(
  path: string,
  body: unknown,
  handlers: SseHandlers<TDone>,
): Promise<void> {
  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    handlers.onError?.(detail || res.statusText);
    throw new Error(detail || res.statusText);
  }
  if (!res.body) {
    throw new Error("Streaming not supported");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const rawRef = { value: "" };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const parsed = parseSseBlock(part.trim());
      if (!parsed) continue;
      let payload: Record<string, unknown>;
      try {
        payload = JSON.parse(parsed.data) as Record<string, unknown>;
      } catch {
        continue;
      }
      dispatchSseEvent(parsed.event, payload, handlers, rawRef);
    }
  }
}

export async function getSseStream<TDone>(
  path: string,
  handlers: SseHandlers<TDone>,
): Promise<void> {
  const res = await fetch(apiUrl(path), {
    headers: { Accept: "text/event-stream" },
  });
  if (!res.ok) {
    const detail = await res.text();
    handlers.onError?.(detail || res.statusText);
    throw new Error(detail || res.statusText);
  }
  if (!res.body) {
    throw new Error("Streaming not supported");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const rawRef = { value: "" };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const parsed = parseSseBlock(part.trim());
      if (!parsed) continue;
      let payload: Record<string, unknown>;
      try {
        payload = JSON.parse(parsed.data) as Record<string, unknown>;
      } catch {
        continue;
      }
      dispatchSseEvent(parsed.event, payload, handlers, rawRef);
    }
  }
}
