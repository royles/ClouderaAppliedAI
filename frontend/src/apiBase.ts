/** Resolve API paths relative to the deployed app URL (CAI subpaths and root). */

export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const base = import.meta.env.BASE_URL ?? "/";
  if (base === "./" || base === ".") {
    return `.${p}`;
  }
  const prefix = base.endsWith("/") ? base.slice(0, -1) : base;
  return `${prefix}${p}`;
}
