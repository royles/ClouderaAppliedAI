import { useEffect, useState } from "react";
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
  const [draft, setDraft] = useState<ActionDraft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState<SimulateSendResult | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setDraft(await draftInsightAction(customerId, { recommendation, source }));
        setError(null);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Could not build draft");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [customerId, recommendation, source]);

  async function handleSend() {
    if (!draft?.actionable || !draft.body || !draft.channel) return;
    setSending(true);
    setError(null);
    try {
      setSent(
        await simulateInsightSend(customerId, {
          channel: draft.channel,
          subject: draft.subject ?? undefined,
          body: draft.body,
        }),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulated send failed");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal panel"
        role="dialog"
        aria-labelledby="action-draft-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-head">
          <h2 id="action-draft-title">{draft?.preview_label ?? "Prepare outreach"}</h2>
          <button type="button" className="link-btn" onClick={onClose}>
            Close
          </button>
        </div>

        {loading && (
          <p className="muted">Generating draft with Amazon Bedrock from account data…</p>
        )}
        {error && <p className="error">{error}</p>}

        {draft && !draft.actionable && (
          <p className={draft.bedrock_required || draft.generation_error ? "error" : "muted"}>
            {draft.message ?? "Not actionable."}
          </p>
        )}

        {draft?.actionable && (
          <>
            <p className="muted small">
              Triggered by: <em>{recommendation}</em>
            </p>
            {draft.content_source === "bedrock" && (
              <p className="insights-meta">
                <span className="source-badge source-bedrock">Drafted by Amazon Bedrock</span>
                {draft.model_id && (
                  <span className="muted small">Model: {draft.model_id}</span>
                )}
              </p>
            )}
            <div className="draft-meta">
              <div>
                <span className="label">To</span>
                <div>{draft.recipient_name}</div>
              </div>
              {draft.channel === "email" && (
                <div>
                  <span className="label">Email</span>
                  <div>{maskEmail(draft.recipient_email)}</div>
                </div>
              )}
              {(draft.channel === "sms" || draft.channel === "call") && (
                <div>
                  <span className="label">Phone</span>
                  <div>{maskPhone(draft.recipient_phone)}</div>
                </div>
              )}
              <div>
                <span className="label">Channel</span>
                <div>{draft.channel}</div>
              </div>
            </div>

            {draft.subject && (
              <>
                <span className="label">Subject</span>
                <div className="draft-subject">{draft.subject}</div>
              </>
            )}

            <span className="label">Body</span>
            <pre className="draft-body">{draft.body}</pre>

            {sent ? (
              <p className="send-success">
                Simulated send complete — {sent.message} ({sent.sent_at})
              </p>
            ) : (
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn"
                  disabled={sending}
                  onClick={handleSend}
                >
                  {sending
                    ? "Sending…"
                    : draft.channel === "call"
                      ? "Log script (simulate)"
                      : `Simulate send ${draft.channel}`}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
