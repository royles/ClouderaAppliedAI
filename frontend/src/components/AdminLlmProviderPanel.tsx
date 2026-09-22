import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  fetchLlmProviderConfig,
  LlmProviderConfig,
  testLlmProvider,
  updateLlmProviderConfig,
} from "../api";

type ProviderChoice = "bedrock" | "openai_compatible";

type FormState = {
  provider_type: ProviderChoice;
  bedrock_region: string;
  bedrock_model_id: string;
  bedrock_max_tokens: string;
  bedrock_temperature: string;
  openai_base_url: string;
  openai_model_id: string;
  openai_api_token: string;
  clear_openai_api_token: boolean;
};

function configToForm(cfg: LlmProviderConfig): FormState {
  return {
    provider_type: (cfg.provider_type as ProviderChoice) || "bedrock",
    bedrock_region: cfg.bedrock_region ?? "",
    bedrock_model_id: cfg.bedrock_model_id ?? "",
    bedrock_max_tokens:
      cfg.bedrock_max_tokens != null ? String(cfg.bedrock_max_tokens) : "",
    bedrock_temperature:
      cfg.bedrock_temperature != null ? String(cfg.bedrock_temperature) : "",
    openai_base_url: cfg.openai_base_url ?? "",
    openai_model_id: cfg.openai_model_id ?? "",
    openai_api_token: "",
    clear_openai_api_token: false,
  };
}

function buildUpdatePayload(form: FormState): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    provider_type: form.provider_type,
    bedrock_region: form.bedrock_region.trim() || null,
    bedrock_model_id: form.bedrock_model_id.trim() || null,
    openai_base_url: form.openai_base_url.trim() || null,
    openai_model_id: form.openai_model_id.trim() || null,
  };
  const maxTok = parseInt(form.bedrock_max_tokens, 10);
  if (Number.isFinite(maxTok) && maxTok > 0) {
    payload.bedrock_max_tokens = maxTok;
  } else if (form.bedrock_max_tokens.trim() === "") {
    payload.bedrock_max_tokens = null;
  }
  const temp = parseFloat(form.bedrock_temperature);
  if (Number.isFinite(temp)) {
    payload.bedrock_temperature = temp;
  } else if (form.bedrock_temperature.trim() === "") {
    payload.bedrock_temperature = null;
  }
  if (form.openai_api_token.trim()) {
    payload.openai_api_token = form.openai_api_token;
  }
  if (form.clear_openai_api_token) {
    payload.clear_openai_api_token = true;
  }
  return payload;
}

export default function AdminLlmProviderPanel() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedNote, setSavedNote] = useState<string | null>(null);
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [meta, setMeta] = useState<LlmProviderConfig | null>(null);
  const [form, setForm] = useState<FormState | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const cfg = await fetchLlmProviderConfig();
      setMeta(cfg);
      setForm(configToForm(cfg));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("admin.llm.loadError"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void load();
  }, [load]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    setSavedNote(null);
    setTestMessage(null);
    try {
      const updated = await updateLlmProviderConfig(buildUpdatePayload(form));
      setMeta(updated);
      setForm(configToForm(updated));
      setSavedNote(t("admin.llm.saved"));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("admin.llm.saveError"));
    } finally {
      setSaving(false);
    }
  };

  const onTest = async () => {
    if (!form) return;
    setTesting(true);
    setTestMessage(null);
    try {
      const result = await testLlmProvider(buildUpdatePayload(form));
      setTestMessage(
        result.ok
          ? result.message + (result.detail ? ` — ${result.detail}` : "")
          : result.message,
      );
    } catch (err) {
      setTestMessage(err instanceof Error ? err.message : t("admin.llm.testFailed"));
    } finally {
      setTesting(false);
    }
  };

  if (loading || !form) {
    return <p className="muted small">{t("admin.llm.loading")}</p>;
  }

  return (
    <form className="admin-llm-form" onSubmit={(e) => void onSubmit(e)}>
      <p className="muted small">{t("admin.llm.lede")}</p>
      {meta?.env_note && <p className="muted small admin-llm-env-note">{meta.env_note}</p>}

      <fieldset className="admin-fieldset">
        <legend>{t("admin.llm.providerLegend")}</legend>
        <label className="admin-radio">
          <input
            type="radio"
            name="provider_type"
            checked={form.provider_type === "bedrock"}
            onChange={() => setForm({ ...form, provider_type: "bedrock" })}
          />
          {t("admin.llm.providers.bedrock")}
        </label>
        <label className="admin-radio">
          <input
            type="radio"
            name="provider_type"
            checked={form.provider_type === "openai_compatible"}
            onChange={() => setForm({ ...form, provider_type: "openai_compatible" })}
          />
          {t("admin.llm.providers.openaiCompatible")}
        </label>
      </fieldset>

      {form.provider_type === "bedrock" && (
        <div className="admin-llm-section">
          <h3 className="subsection-title">{t("admin.llm.bedrockSection")}</h3>
          <p className="muted small">{t("admin.llm.bedrockHint")}</p>
          <label className="admin-field">
            <span>{t("admin.llm.bedrockRegion")}</span>
            <input
              type="text"
              value={form.bedrock_region}
              onChange={(e) => setForm({ ...form, bedrock_region: e.target.value })}
              placeholder="us-east-1"
              autoComplete="off"
            />
          </label>
          <label className="admin-field">
            <span>{t("admin.llm.bedrockModelId")}</span>
            <input
              type="text"
              value={form.bedrock_model_id}
              onChange={(e) => setForm({ ...form, bedrock_model_id: e.target.value })}
              placeholder="anthropic.claude-haiku-4-5-20251001-v1:0"
              autoComplete="off"
            />
          </label>
        </div>
      )}

      {form.provider_type === "openai_compatible" && (
        <div className="admin-llm-section">
          <h3 className="subsection-title">{t("admin.llm.openaiSection")}</h3>
          <label className="admin-field">
            <span>{t("admin.llm.openaiBaseUrl")}</span>
            <input
              type="url"
              value={form.openai_base_url}
              onChange={(e) => setForm({ ...form, openai_base_url: e.target.value })}
              placeholder="https://api.openai.com/v1"
              autoComplete="off"
            />
          </label>
          <label className="admin-field">
            <span>{t("admin.llm.openaiModelId")}</span>
            <input
              type="text"
              value={form.openai_model_id}
              onChange={(e) => setForm({ ...form, openai_model_id: e.target.value })}
              placeholder="gpt-4o-mini"
              autoComplete="off"
            />
          </label>
          <label className="admin-field">
            <span>{t("admin.llm.openaiToken")}</span>
            <input
              type="password"
              value={form.openai_api_token}
              onChange={(e) => setForm({ ...form, openai_api_token: e.target.value })}
              placeholder={
                meta.openai_api_token_set
                  ? t("admin.llm.tokenPlaceholderSet")
                  : t("admin.llm.tokenPlaceholderEmpty")
              }
              autoComplete="new-password"
            />
          </label>
          {meta.openai_api_token_set && (
            <label className="admin-checkbox">
              <input
                type="checkbox"
                checked={form.clear_openai_api_token}
                onChange={(e) =>
                  setForm({ ...form, clear_openai_api_token: e.target.checked })
                }
              />
              {t("admin.llm.clearToken")}
            </label>
          )}
        </div>
      )}

      <div className="admin-llm-section">
        <h3 className="subsection-title">{t("admin.llm.samplingSection")}</h3>
        <label className="admin-field">
          <span>{t("admin.llm.maxTokens")}</span>
          <input
            type="number"
            min={64}
            max={8192}
            value={form.bedrock_max_tokens}
            onChange={(e) => setForm({ ...form, bedrock_max_tokens: e.target.value })}
            placeholder="900"
          />
        </label>
        <label className="admin-field">
          <span>{t("admin.llm.temperature")}</span>
          <input
            type="number"
            step="0.05"
            min={0}
            max={2}
            value={form.bedrock_temperature}
            onChange={(e) => setForm({ ...form, bedrock_temperature: e.target.value })}
            placeholder="0.35"
          />
        </label>
      </div>

      {error && <p className="error">{error}</p>}
      {savedNote && <p className="muted small">{savedNote}</p>}
      {testMessage && <p className="muted small admin-test-result">{testMessage}</p>}

      <div className="admin-form-actions">
        <button type="submit" className="btn primary" disabled={saving}>
          {saving ? t("admin.llm.saving") : t("admin.llm.save")}
        </button>
        <button
          type="button"
          className="btn secondary"
          disabled={testing}
          onClick={() => void onTest()}
        >
          {testing ? t("admin.llm.testing") : t("admin.llm.test")}
        </button>
      </div>
      {meta.updated_at && (
        <p className="muted small">
          {t("admin.datasource.lastUpdated", {
            date: new Date(meta.updated_at).toLocaleString(),
          })}
        </p>
      )}
    </form>
  );
}
