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

/** Session or per-response provider; never infer Bedrock from a generic “configured” flag. */
export function resolveConfiguredProvider(
  sessionProvider: LlmProviderKind,
  responseProvider?: string | null,
): LlmProviderKind {
  const fromResponse = resolveLlmProvider({ provider: responseProvider ?? undefined });
  if (fromResponse !== "none") return fromResponse;
  return sessionProvider;
}

/**
 * When PrivateAI is the configured backend, API fields may still say “bedrock”.
 * Never surface Amazon Bedrock in that case.
 */
export function effectiveLlmSource(
  source: string | null | undefined,
  configured: LlmProviderKind,
): string | null {
  if (!source) return null;
  if (source === "streaming" || source === "pending") return source;
  if (configured === "openai_compatible") {
    if (source === "bedrock" || source === "bedrock_tools") return "openai_compatible";
  }
  if (configured !== "bedrock") {
    if (source === "bedrock" || source === "bedrock_tools") {
      return configured === "openai_compatible" ? "openai_compatible" : "rules";
    }
  }
  return source;
}

/** User-facing product name: Amazon Bedrock vs PrivateAI. */
export function llmBrandName(t: TFunction, provider: LlmProviderKind): string {
  if (provider === "openai_compatible") return t("llm.brand.privateAi");
  if (provider === "bedrock") return t("llm.brand.bedrock");
  return t("llm.brand.local");
}

export function isLlmGeneratedSource(source: string | null | undefined): boolean {
  const s = source ?? "";
  return s === "bedrock" || s === "openai_compatible" || s === "bedrock_tools";
}

export function isAssistantSourcePending(source: string | null | undefined): boolean {
  return source === "streaming" || source === "pending";
}

/** Badge text under each assistant turn — only after the answer is complete. */
export function assistantSourceLabel(
  t: TFunction,
  source: string | null | undefined,
  llmProvider: LlmProviderKind,
  responseProvider?: string | null,
): string | null {
  if (!source || isAssistantSourcePending(source)) return null;

  const configured = resolveConfiguredProvider(llmProvider, responseProvider);
  const effective = effectiveLlmSource(source, configured);
  if (!effective) return null;

  if (effective === "openai_compatible") {
    return t("assistant.source.privateAi");
  }
  if (effective === "bedrock_tools") {
    return t("assistant.source.bedrockTools");
  }
  if (effective === "bedrock") {
    return t("assistant.source.bedrock");
  }
  if (effective === "rules_fallback") {
    if (configured === "openai_compatible") {
      return t("assistant.source.rulesFallback", {
        brand: llmBrandName(t, "openai_compatible"),
      });
    }
    if (configured === "bedrock") {
      return t("assistant.source.rulesFallback", {
        brand: llmBrandName(t, "bedrock"),
      });
    }
    return t("assistant.source.rules");
  }
  if (effective === "rules") {
    return t("assistant.source.rules");
  }
  return null;
}

/** Insights / drafts: brand line for a completed LLM response. */
export function brandForLlmSource(
  t: TFunction,
  source: string | null | undefined,
  configured: LlmProviderKind,
): string {
  const effective = effectiveLlmSource(source, configured);
  if (effective === "openai_compatible") return llmBrandName(t, "openai_compatible");
  if (effective === "bedrock" || effective === "bedrock_tools") {
    return llmBrandName(t, "bedrock");
  }
  return llmBrandName(t, configured);
}
