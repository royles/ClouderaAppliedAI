import type { TFunction } from "i18next";

/** Active LLM backend for user-facing copy (API field: provider_type). */
export type LlmProviderKind = "bedrock" | "openai_compatible" | "none";

export function resolveLlmProvider(
  status?: { provider?: string; configured?: boolean } | null,
): LlmProviderKind {
  const raw = status?.provider?.trim().toLowerCase();
  if (raw === "openai_compatible") return "openai_compatible";
  if (raw === "bedrock") return "bedrock";
  return "none";
}

/** User-facing product name: Amazon Bedrock vs PrivateAI. */
export function llmBrandName(t: TFunction, provider: LlmProviderKind): string {
  if (provider === "openai_compatible") return t("llm.brand.privateAi");
  if (provider === "bedrock") return t("llm.brand.bedrock");
  return t("llm.brand.local");
}

export function isLlmGeneratedSource(source: string | null | undefined): boolean {
  return source === "bedrock" || source === "openai_compatible" || source === "bedrock_tools";
}

/** Badge text under each assistant turn (PrivateAI, Bedrock, rules, streaming). */
export function assistantSourceLabel(
  t: TFunction,
  source: string | null | undefined,
  llmProvider: LlmProviderKind,
  responseProvider?: string | null,
): string | null {
  const providerFromApi = resolveLlmProvider({
    provider: responseProvider ?? undefined,
    configured: responseProvider != null && responseProvider !== "",
  });
  const brand = llmBrandName(
    t,
    providerFromApi !== "none" ? providerFromApi : llmProvider,
  );

  if (source === "streaming") {
    return t("assistant.source.streaming", { brand });
  }
  if (source === "openai_compatible") {
    return t("assistant.source.privateAi");
  }
  if (source === "bedrock_tools") {
    return t("assistant.source.bedrockTools");
  }
  if (source === "bedrock") {
    return t("assistant.source.bedrock");
  }
  if (source === "rules_fallback") {
    return t("assistant.source.rulesFallback", { brand });
  }
  if (source === "rules") {
    return t("assistant.source.rules");
  }
  return null;
}
