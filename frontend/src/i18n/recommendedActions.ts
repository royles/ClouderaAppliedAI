import type { TFunction } from "i18next";

export type RecommendedActionFields = {
  action_code: string;
  title: string;
  detail: string;
};

/** Engagement hub next-best-action copy (keyed by action_code). */
export function engagementRecommendedAction(
  t: TFunction,
  action: RecommendedActionFields,
  ctx?: { unresolvedCount?: number },
): { title: string; detail: string } {
  const code = action.action_code;
  return {
    title: t(`engagement.actions.${code}.title`, { defaultValue: action.title }),
    detail: t(`engagement.actions.${code}.detail`, {
      count: ctx?.unresolvedCount ?? 0,
      defaultValue: action.detail,
    }),
  };
}

/** Retention playbook queue actions (same codes as engagement may differ in copy). */
export function retentionRecommendedAction(
  t: TFunction,
  action: RecommendedActionFields,
): { title: string; detail: string } {
  const code = action.action_code;
  return {
    title: t(`assistant.retention.actions.${code}.title`, { defaultValue: action.title }),
    detail: t(`assistant.retention.actions.${code}.detail`, { defaultValue: action.detail }),
  };
}
