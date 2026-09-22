import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActionDraft,
  BedrockStatus,
  SimulateSendResult,
  draftInsightActionStream,
  fetchBedrockStatus,
  fetchCustomer,
  simulateInsightSend,
} from "../api";
import { isLlmGeneratedSource, llmBrandName, resolveLlmProvider } from "../llmBrand";
import { partialJsonStringField } from "../jsonStreamPreview";
import {
  DraftChannel,
  draftChannelLabel,
  draftPreviewTitle,
  inferDraftChannel,
  type DraftStreamMeta,
} from "../outreachDraft";
import { maskEmail, maskPhone } from "../pii";
import { useModalDialog } from "../a11y/useModalDialog";
import { apiLocaleCode } from "../i18n/index";

type Props = {
  customerId: number;
  recommendation: string;
  source: "recommendation" | "experience_note";
  onClose: () => void;
};

export default function InsightActionModal({
  customerId,
  recommendation,
  source,
  onClose,
}: Props) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState<ActionDraft | null>(null);
  const [body, setBody] = useState("");
  const [subject, setSubject] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(true);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState<SimulateSendResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [llmStatus, setLlmStatus] = useState<BedrockStatus | null>(null);
  const [channel, setChannel] = useState<DraftChannel>(() => inferDraftChannel(recommendation));
  const [previewLabel, setPreviewLabel] = useState(() => t("customer.outreach.title"));
  const [recipientName, setRecipientName] = useState("");
  const [recipientEmail, setRecipientEmail] = useState<string | null>(null);
  const [recipientPhone, setRecipientPhone] = useState<string | null>(null);
  const [contentSource, setContentSource] = useState<string | null>(null);
  const [modelId, setModelId] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  useModalDialog(dialogRef, onClose);

  const llmProvider = resolveLlmProvider(llmStatus);
  const configuredBrand = llmBrandName(t, llmProvider);

  useEffect(() => {
    let cancelled = false;
    void fetchBedrockStatus()
      .then((status) => {
        if (!cancelled) setLlmStatus(status);
      })
      .catch(() => {
        if (!cancelled) setLlmStatus(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const ch = inferDraftChannel(recommendation);
    setChannel(ch);
    setPreviewLabel(
      draftPreviewTitle(ch, configuredBrand, t("customer.outreach.title"), t),
    );
    void fetchCustomer(customerId)
      .then((detail) => {
        if (cancelled) return;
        setRecipientName(detail.profile.customer_name);
        setRecipientEmail(detail.profile.email ?? null);
        setRecipientPhone(detail.profile.mobile_no ?? null);
      })
      .catch(() => {
        /* meta event or done payload will fill recipients */
      });
    return () => {
      cancelled = true;
    };
  }, [customerId, recommendation, configuredBrand, t]);

  useEffect(() => {
    let cancelled = false;
    setStreaming(true);
    setDraft(null);
    setBody("");
    setSubject("");
    setError(null);

    void (async () => {
      try {
        await draftInsightActionStream(
          customerId,
          { recommendation, source, locale: apiLocaleCode() },
          {
            onMeta: (meta) => {
              if (cancelled) return;
              applyDraftMeta(meta as DraftStreamMeta);
            },
            onDelta: (_piece, buffer) => {
              if (cancelled) return;
              const nextSubject = partialJsonStringField(buffer, "subject");
              const nextBody = partialJsonStringField(buffer, "body");
              if (nextSubject) setSubject(nextSubject);
              if (nextBody) setBody(nextBody);
              const ch = partialJsonStringField(buffer, "channel");
              if (ch === "email" || ch === "sms" || ch === "call") {
                setChannel(ch);
              }
            },
            onDone: (next) => {
              if (cancelled) return;
              setDraft(next);
              if (next.body) setBody(next.body);
              if (next.subject) setSubject(next.subject ?? "");
              if (next.channel === "email" || next.channel === "sms" || next.channel === "call") {
                setChannel(next.channel);
              }
              if (next.preview_label) setPreviewLabel(next.preview_label);
              if (next.recipient_name) setRecipientName(next.recipient_name);
              if (next.recipient_email !== undefined) setRecipientEmail(next.recipient_email);
              if (next.recipient_phone !== undefined) setRecipientPhone(next.recipient_phone);
              setContentSource(next.content_source ?? null);
              setModelId(next.model_id ?? null);
              setError(null);
            },
          },
        );
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : t("customer.outreach.draftError"));
        }
      } finally {
        if (!cancelled) setStreaming(false);
      }
    })();

    function applyDraftMeta(meta: DraftStreamMeta) {
      if (meta.channel === "email" || meta.channel === "sms" || meta.channel === "call") {
        setChannel(meta.channel);
      }
      if (meta.preview_label) setPreviewLabel(meta.preview_label);
      else if (meta.channel) {
        setPreviewLabel(
          draftPreviewTitle(
            meta.channel as DraftChannel,
            configuredBrand,
            t("customer.outreach.title"),
            t,
          ),
        );
      }
      if (meta.recipient_name) setRecipientName(meta.recipient_name);
      if (meta.recipient_email !== undefined) setRecipientEmail(meta.recipient_email);
      if (meta.recipient_phone !== undefined) setRecipientPhone(meta.recipient_phone);
    }

    return () => {
      cancelled = true;
    };
  }, [customerId, recommendation, source, configuredBrand, t]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    dialogRef.current?.focus();
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const showForm = draft?.actionable !== false;
  const notActionable = draft != null && !draft.actionable;
  const canSend = !streaming && draft?.actionable && body.trim().length > 0;

  async function handleSend() {
    if (!canSend) return;
    setSending(true);
    setError(null);
    try {
      setSent(
        await simulateInsightSend(customerId, {
          channel,
          subject: subject.trim() || undefined,
          body: body.trim(),
        }),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : t("customer.outreach.sendFailed"));
    } finally {
      setSending(false);
    }
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(body);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setError(t("customer.outreach.copyFailed"));
    }
  }

  const draftedBySource = contentSource ?? draft?.content_source;
  const displayModelId = modelId ?? draft?.model_id;

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        ref={dialogRef}
        className="modal panel modal-draft-outreach"
        role="dialog"
        aria-modal="true"
        aria-labelledby="action-draft-title"
        aria-describedby="action-draft-disclaimer"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-head">
          <h2 id="action-draft-title">{draft?.preview_label ?? previewLabel}</h2>
          <button
            type="button"
            className="link-btn"
            onClick={onClose}
            aria-label={t("customer.outreach.cancel")}
          >
            {t("customer.outreach.cancel")}
          </button>
        </div>

        <p id="action-draft-disclaimer" className="muted small modal-disclaimer">
          {t("customer.outreach.disclaimer")}
        </p>

        {streaming && (
          <p className="muted small draft-stream-status">
            {t("customer.outreach.streaming")}
          </p>
        )}
        {error && <p className="error">{error}</p>}

        {notActionable && (
          <p className={draft.bedrock_required || draft.generation_error ? "error" : "muted"}>
            {draft.message ?? t("customer.outreach.notActionable")}
          </p>
        )}

        {showForm && (
          <>
            <p className="muted small">
              {t("customer.outreach.triggeredBy")} <em>{recommendation}</em>
            </p>
            {isLlmGeneratedSource(draftedBySource) && (
              <p className="insights-meta">
                <span className="source-badge source-bedrock">
                  {t("customer.outreach.draftedBy", {
                    brand:
                      draftedBySource === "openai_compatible"
                        ? llmBrandName(t, "openai_compatible")
                        : llmBrandName(t, "bedrock"),
                  })}
                </span>
                {displayModelId && (
                  <span className="muted small">
                    {t("customer.insights.modelId", { id: displayModelId })}
                  </span>
                )}
              </p>
            )}
            <div className="draft-meta">
              <div>
                <span className="label">{t("customer.outreach.to")}</span>
                <div>{recipientName || "—"}</div>
              </div>
              {channel === "email" && (
                <div>
                  <span className="label">{t("customer.outreach.email")}</span>
                  <div>{maskEmail(recipientEmail)}</div>
                </div>
              )}
              {(channel === "sms" || channel === "call") && (
                <div>
                  <span className="label">{t("customer.outreach.phone")}</span>
                  <div>{maskPhone(recipientPhone)}</div>
                </div>
              )}
              <div>
                <span className="label">{t("customer.outreach.channel")}</span>
                <div>{draftChannelLabel(channel, t)}</div>
              </div>
            </div>

            {channel === "email" && (
              <>
                <label className="label" htmlFor="draft-subject">
                  {t("customer.outreach.subject")}
                </label>
                <input
                  id="draft-subject"
                  className="control control-full"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  readOnly={streaming}
                  aria-busy={streaming}
                />
              </>
            )}

            <label className="label" htmlFor="draft-body">
              {t("customer.outreach.body")}
            </label>
            <textarea
              id="draft-body"
              className="draft-body draft-body-edit"
              rows={10}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              readOnly={streaming}
              aria-busy={streaming}
              placeholder={streaming ? t("customer.outreach.streaming") : undefined}
            />

            {sent ? (
              <p className="send-success">
                Simulated send complete — {sent.message} ({sent.sent_at})
              </p>
            ) : (
              <div className="modal-actions">
                <button type="button" className="control control-btn" onClick={handleCopy} disabled={!body.trim()}>
                  {copied ? t("customer.outreach.copied") : t("customer.outreach.copy")}
                </button>
                <button
                  type="button"
                  className="btn"
                  disabled={sending || !canSend}
                  onClick={handleSend}
                >
                  {sending ? t("assistant.send.thinking") : t("customer.outreach.send")}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
