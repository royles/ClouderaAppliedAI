/** Query flag: page opened from a copilot action (mobile focus layout). */
export const COPILOT_FOCUS_PARAM = "from_copilot";

export function isCopilotFocusSearch(params: URLSearchParams): boolean {
  return params.get(COPILOT_FOCUS_PARAM) === "1";
}

export function withCopilotFocus(path: string, enabled: boolean): string {
  if (!enabled) return path;
  const [pathname, search = ""] = path.split("?");
  const params = new URLSearchParams(search);
  params.set(COPILOT_FOCUS_PARAM, "1");
  const qs = params.toString();
  return qs ? `${pathname}?${qs}` : pathname;
}

export function stripCopilotFocus(params: URLSearchParams): URLSearchParams {
  const next = new URLSearchParams(params);
  next.delete(COPILOT_FOCUS_PARAM);
  return next;
}
