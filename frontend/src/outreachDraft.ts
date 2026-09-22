/** Match backend classify_recommendation + channel_for_action_kind (client-side shell). */

import type { TFunction } from "i18next";

export type DraftChannel = "email" | "sms" | "call";

export function inferDraftChannel(recommendation: string): DraftChannel {
  const t = recommendation.toLowerCase();
  if (/\b(call|check-in|outbound|phone)\b/.test(t)) return "call";
  if (/\bsms\b/.test(t) || t.includes("text message")) return "sms";
  return "email";
}

export function draftPreviewTitle(
  channel: DraftChannel,
  brand: string,
  fallback: string,
  t: TFunction,
): string {
  if (channel === "email") {
    return t("customer.outreach.previewEmail", { brand, defaultValue: fallback });
  }
  if (channel === "sms") {
    return t("customer.outreach.previewSms", { brand, defaultValue: fallback });
  }
  if (channel === "call") {
    return t("customer.outreach.previewCall", { brand, defaultValue: fallback });
  }
  return fallback;
}

export function draftChannelLabel(channel: DraftChannel, t: TFunction): string {
  if (channel === "call") return t("engagement.channel.phone");
  if (channel === "sms") return t("engagement.channel.sms");
  return t("engagement.channel.email");
}

export type DraftStreamMeta = {
  channel?: DraftChannel | string | null;
  recipient_name?: string | null;
  recipient_email?: string | null;
  recipient_phone?: string | null;
  preview_label?: string | null;
  actionable?: boolean;
};
