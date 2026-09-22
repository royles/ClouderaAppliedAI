import type { TFunction } from "i18next";
import type { DataQualityCheck, SystemHealthCheck } from "../api";

type AdminCheck = DataQualityCheck | SystemHealthCheck;

export function translateCheckStatus(t: TFunction, status: string): string {
  const key = `admin.status.${status}` as const;
  const translated = t(key);
  return translated === key ? status : translated;
}

export function translateAdminCheck(
  t: TFunction,
  check: AdminCheck,
): { label: string; summary: string; detail: string | null } {
  const base = `admin.checks.${check.id}`;
  const label = t(`${base}.label`, { defaultValue: check.label });
  const metric = "metric_value" in check ? check.metric_value : undefined;
  const summary = t(`${base}.summary`, {
    defaultValue: check.summary,
    pct: metric,
    value: metric,
  });
  const detail = check.detail
    ? t(`${base}.detail`, { defaultValue: check.detail })
    : null;
  return { label, summary, detail };
}
