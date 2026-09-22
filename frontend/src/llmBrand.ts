import type { TFunction } from "i18next";

/** Active LLM backend for user-facing copy (API field: provider_type). */
export type LlmProviderKind = "bedrock" | "openai_compatible" | "none";

export function resolveLlmProvider(
  status?: { provider?: string; configured?: boolean } | null,
): LlmProviderKind {
  const raw = status?.provider?.trim().toLowerCase();
  if (raw === "openai_compatible") return "openai_compatible";
  if (raw === "bedrock") return "bedrock";
  if (status?.configured) return "bedrock";
  return "none";
}

/** User-facing product name: Amazon Bedrock vs PrivateAI. */
export function llmBrandName(t: TFunction, provider: LlmProviderKind): string {
  if (provider === "openai_compatible") return t("llm.brand.privateAi");
  if (provider === "bedrock") return t("llm.brand.bedrock");
  return t("llm.brand.local");
}

export function isLlmGeneratedSource(source: string | null | undefined): boolean {
  return source === "bedrock" || source === "openai_compatible";
}
