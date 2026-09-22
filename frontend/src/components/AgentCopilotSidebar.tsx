import { FormEvent, useCallback, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AgentAction, askAgent } from "../api";
import {
  CopilotPanel,
  newTurnId,
  useAgentCopilot,
} from "../agentCopilotContext";
import RetentionPlaybookPanel from "./RetentionPlaybookPanel";

function actionHref(action: AgentAction): string {
  const path = action.path ?? "/business";
  if (action.search?.trim()) {
    return `${path}?${action.search.replace(/^\?/, "")}`;
  }
  return path;
}

function ActionButton({
  action,
  onOpenPanel,
}: {
  action: AgentAction;
  onOpenPanel: (action: AgentAction) => void;
}) {
  if (action.action_type === "open_panel" && action.panel === "retention_playbook") {
    return (
      <button
        type="button"
        className="agent-copilot-action"
        onClick={() => onOpenPanel(action)}
      >
        {action.label}
      </button>
    );
  }

  const href = actionHref(action);
  return (
    <Link to={href} className="agent-copilot-action">
      {action.label}
    </Link>
  );
}

export default function AgentCopilotSidebar() {
  const navigate = useNavigate();
  const {
    open,
    setOpen,
    panel,
    setPanel,
    turns,
    appendTurn,
    askSegment,
    playbookSegment,
    setPlaybookSegment,
    playbookCohortLabel,
    openRetentionPlaybook,
  } = useAgentCopilot();

  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const historyRef = useRef<HTMLDivElement>(null);

  const handleOpenPanelAction = useCallback(
    (action: AgentAction) => {
      const seg = (action.segment as typeof askSegment) || askSegment;
      if (action.path) {
        navigate(actionHref(action));
      }
      if (action.panel === "retention_playbook") {
        openRetentionPlaybook(seg, playbookCohortLabel);
        setPanel("retention_playbook");
      }
    },
    [askSegment, navigate, openRetentionPlaybook, playbookCohortLabel, setPanel],
  );

  const submit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      const message = draft.trim();
      if (!message || sending) return;
      setDraft("");
      appendTurn({ id: newTurnId(), role: "user", text: message });
      setSending(true);
      try {
        const res = await askAgent({ message, segment: askSegment });
        appendTurn({
          id: newTurnId(),
          role: "assistant",
          text: res.answer,
          actions: res.actions,
          source: res.source,
          modelId: res.model_id ?? null,
        });
        requestAnimationFrame(() => {
          historyRef.current?.scrollTo({ top: historyRef.current.scrollHeight, behavior: "smooth" });
        });
      } catch (err) {
        appendTurn({
          id: newTurnId(),
          role: "assistant",
          text:
            err instanceof Error
              ? err.message
              : "Could not reach the copilot. Check that the API is running.",
        });
      } finally {
        setSending(false);
      }
    },
    [appendTurn, askSegment, draft, sending],
  );

  if (!open) return null;

  const setTab = (next: CopilotPanel) => setPanel(next);

  return (
    <aside className="agent-copilot-sidebar" aria-label="Executive copilot">
      <header className="agent-copilot-head">
        <div>
          <h2 className="agent-copilot-title">Executive copilot</h2>
          <p className="muted small">
            Ask about the book; links change the main view. Answers use Amazon Bedrock when
            configured.
          </p>
        </div>
        <button
          type="button"
          className="playbook-close"
          onClick={() => setOpen(false)}
          aria-label="Close copilot"
        >
          ×
        </button>
      </header>

      <div className="agent-copilot-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={panel === "ask"}
          className={`agent-copilot-tab${panel === "ask" ? " is-active" : ""}`}
          onClick={() => setTab("ask")}
        >
          Conversation
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={panel === "retention_playbook"}
          className={`agent-copilot-tab${panel === "retention_playbook" ? " is-active" : ""}`}
          onClick={() => {
            setPlaybookSegment(askSegment);
            setTab("retention_playbook");
          }}
        >
          Retention queue
        </button>
      </div>

      {panel === "ask" && (
        <>
          <div ref={historyRef} className="agent-copilot-history">
            {turns.length === 0 && (
              <p className="muted small agent-copilot-empty">
                Try: “Show the product heatmap”, “How many customers?”, or “Open retention
                playbook”.
              </p>
            )}
            {turns.map((turn) => (
              <div
                key={turn.id}
                className={`agent-copilot-turn agent-copilot-turn-${turn.role}`}
              >
                <span className="agent-copilot-turn-label">
                  {turn.role === "user" ? "You" : "Copilot"}
                  {turn.role === "assistant" && turn.source && (
                    <span className="agent-copilot-source">
                      {turn.source === "bedrock" ? " · Bedrock" : " · Rules"}
                    </span>
                  )}
                </span>
                <p className="agent-copilot-turn-text">{turn.text}</p>
                {turn.actions && turn.actions.length > 0 && (
                  <div className="agent-copilot-actions">
                    {turn.actions.map((action) => (
                      <ActionButton
                        key={action.action_id}
                        action={action}
                        onOpenPanel={handleOpenPanelAction}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          <form className="agent-copilot-form" onSubmit={submit}>
            <label className="visually-hidden" htmlFor="agent-copilot-input">
              Ask Customer 360
            </label>
            <textarea
              id="agent-copilot-input"
              className="agent-copilot-input"
              rows={3}
              placeholder="Ask about KPIs, customers, products…"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              disabled={sending}
            />
            <button type="submit" className="agent-copilot-send" disabled={sending || !draft.trim()}>
              {sending ? "Thinking…" : "Ask"}
            </button>
          </form>
        </>
      )}

      {panel === "retention_playbook" && (
        <div className="agent-copilot-playbook-wrap">
          <RetentionPlaybookPanel
            segment={playbookSegment}
            cohortLabel={playbookCohortLabel}
            compact
          />
        </div>
      )}
    </aside>
  );
}
