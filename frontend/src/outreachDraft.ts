/** Match backend classify_recommendation + channel_for_action_kind (client-side shell). */

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
): string {
  if (channel === "email") return `Draft email (${brand})`;
  if (channel === "sms") return `Draft SMS (${brand})`;
  if (channel === "call") return `Call script (${brand})`;
  return fallback;
}

export type DraftStreamMeta = {
  channel?: DraftChannel | string | null;
  recipient_name?: string | null;
  recipient_email?: string | null;
  recipient_phone?: string | null;
  preview_label?: string | null;
  actionable?: boolean;
};
