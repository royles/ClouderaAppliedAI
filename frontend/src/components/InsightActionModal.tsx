import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActionDraft,
  SimulateSendResult,
  draftInsightAction,
  simulateInsightSend,
} from "../api";
import { maskEmail, maskPhone } from "../pii";

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
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState<SimulateSendResult | null>(null);
  const [copied, setCopied] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const next = await draftInsightAction(customerId, { recommendation, source });
        if (cancelled) return;
        setDraft(next);
        setBody(next.body ?? "");
        setSubject(next.subject ?? "");
        setError(null);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : t("customer.outreach.draftError"));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [customerId, recommendation, source]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    dialogRef.current?.focus();
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function handleSend() {
    if (!draft?.actionable || !body.trim() || !draft.channel) return;
    setSending(true);
    setError(null);
    try {
      setSent(
        await simulateInsightSend(customerId, {
          channel: draft.channel,
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

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        ref={dialogRef}
        className="modal panel"
        role="dialog"
        aria-labelledby="action-draft-title"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-head">
          <h2 id="action-draft-title">{draft?.preview_label ?? t("customer.outreach.title")}</h2>
          <button type="button" className="link-btn" onClick={onClose}>
            {t("customer.outreach.cancel")}
          </button>
        </div>

        <p className="muted small modal-disclaimer">{t("customer.outreach.disclaimer")}</p>

        {loading && (
          <p className="muted">{t("customer.outreach.loadingDraft")}</p>
        )}
        {error && <p className="error">{error}</p>}

        {draft && !draft.actionable && (
          <p className={draft.bedrock_required || draft.generation_error ? "error" : "muted"}>
            {draft.message ?? t("customer.outreach.notActionable")}
          </p>
        )}

        {draft?.actionable && (
          <>
            <p className="muted small">
              {t("customer.outreach.triggeredBy")} <em>{recommendation}</em>
            </p>
            {draft.content_source === "bedrock" && (
              <p className="insights-meta">
                <span className="source-badge source-bedrock">
                  {t("customer.outreach.draftedBedrock")}
                </span>
                {draft.model_id && (
                  <span className="muted small">
                    {t("customer.insights.modelId", { id: draft.model_id })}
                  </span>
                )}
              </p>
            )}
            <div className="draft-meta">
              <div>
                <span className="label">{t("customer.outreach.to")}</span>
                <div>{draft.recipient_name}</div>
              </div>
              {draft.channel === "email" && (
                <div>
                  <span className="label">{t("customer.outreach.email")}</span>
                  <div>{maskEmail(draft.recipient_email)}</div>
                </div>
              )}
              {(draft.channel === "sms" || draft.channel === "call") && (
                <div>
                  <span className="label">{t("customer.outreach.phone")}</span>
                  <div>{maskPhone(draft.recipient_phone)}</div>
                </div>
              )}
              <div>
                <span className="label">{t("customer.outreach.channel")}</span>
                <div>{draft.channel}</div>
              </div>
            </div>

            {draft.channel === "email" && (
              <>
                <label className="label" htmlFor="draft-subject">
                  {t("customer.outreach.subject")}
                </label>
                <input
                  id="draft-subject"
                  className="control control-full"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
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
            />

            {sent ? (
              <p className="send-success">
                Simulated send complete — {sent.message} ({sent.sent_at})
              </p>
            ) : (
              <div className="modal-actions">
                <button type="button" className="control control-btn" onClick={handleCopy}>
                  {copied ? t("customer.outreach.copied") : t("customer.outreach.copy")}
                </button>
                <button
                  type="button"
                  className="btn"
                  disabled={sending || !body.trim()}
                  onClick={handleSend}
                >
                  {sending ? t("copilot.send.thinking") : t("customer.outreach.send")}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
