/**
 * API paths must be absolute from the host root.
 *
 * Relative `./api/...` breaks on client routes like `/customers/123` (resolves to
 * `/customers/api/...` → FastAPI 404).
 */

export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const base = import.meta.env.BASE_URL ?? "/";
  if (base === "/" || base === "./" || base === ".") {
    return p;
  }
  const prefix = base.endsWith("/") ? base.slice(0, -1) : base;
  return `${prefix}${p}`;
}
