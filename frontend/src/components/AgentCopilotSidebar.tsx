import { FormEvent, KeyboardEvent, useCallback, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { isCustomerArea } from "../appRoutes";
import { parseCohortSearch } from "../cohortQuery";
import { AgentAction, askAgent } from "../api";
import {
  CopilotPanel,
  newTurnId,
  useAgentCopilot,
} from "../agentCopilotContext";
import { withCopilotFocus } from "../copilotNavigation";
import { useMobileUx } from "../mobileUxContext";
import RetentionPlaybookPanel from "./RetentionPlaybookPanel";
import { llmBrandName } from "../llmBrand";

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
  isPhone,
  onNavigateContent,
}: {
  action: AgentAction;
  onOpenPanel: (action: AgentAction) => void;
  isPhone: boolean;
  onNavigateContent: () => void;
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

  const href = withCopilotFocus(actionHref(action), isPhone);
  return (
    <Link
      to={href}
      className="agent-copilot-action"
      onClick={() => {
        if (isPhone) onNavigateContent();
      }}
    >
      {action.label}
    </Link>
  );
}

type Props = {
  phoneHome?: boolean;
};

export default function AgentCopilotSidebar({ phoneHome = false }: Props) {
  const { t, i18n } = useTranslation();
  const apiLocale = i18n.language?.startsWith("he") ? "he" : "en";
  const navigate = useNavigate();
  const { isPhone, enterMobileContent } = useMobileUx();
  const location = useLocation();
  const listContext = useMemo(() => {
    if (!isCustomerArea(location.pathname)) return null;
    const state = parseCohortSearch(new URLSearchParams(location.search));
    return {
      segment: state.segment,
      sort_by: state.sortBy,
      sort_order: state.sortOrder,
      page_size: state.pageSize,
      page: state.page,
      view: state.view,
      city: state.city,
      q: state.q || null,
      policy_type_code: state.policyTypeCode,
      churn_risk_tier: state.churnTier,
    };
  }, [location.pathname, location.search]);

  const {
    bedrockConfigured,
    llmProvider,
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
        navigate(withCopilotFocus(actionHref(action), isPhone));
        if (isPhone) enterMobileContent();
      }
      if (action.panel === "retention_playbook") {
        openRetentionPlaybook(seg, playbookCohortLabel);
        setPanel("retention_playbook");
        if (isPhone) enterMobileContent();
      }
    },
    [
      askSegment,
      enterMobileContent,
      isPhone,
      navigate,
      openRetentionPlaybook,
      playbookCohortLabel,
      setPanel,
    ],
  );

  const runAsk = useCallback(
    async (message: string) => {
      const trimmed = message.trim();
      if (!trimmed || sending) return;
      setDraft("");
      appendTurn({ id: newTurnId(), role: "user", text: trimmed });
      setSending(true);
      try {
        const res = await askAgent({
          message: trimmed,
          segment: askSegment,
          list_context: listContext,
          locale: apiLocale,
        });
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
              : t("errors.assistantUnreachable"),
        });
      } finally {
        setSending(false);
      }
    },
    [appendTurn, askSegment, listContext, sending, apiLocale, t],
  );

  const submit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      void runAsk(draft);
    },
    [draft, runAsk],
  );

  const onInputKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key !== "Enter" || e.shiftKey || e.nativeEvent.isComposing) return;
      e.preventDefault();
      void runAsk(draft);
    },
    [draft, runAsk],
  );

  const setTab = (next: CopilotPanel) => setPanel(next);
  const activeBrand = llmBrandName(t, llmProvider);

  return (
    <aside
      className={`agent-copilot-sidebar${phoneHome ? " agent-copilot-sidebar-phone-home" : ""}`}
      aria-label={t("assistant.title")}
    >
      <header className="agent-copilot-head">
        <div>
          <h2 className="agent-copilot-title">{t("assistant.title")}</h2>
          <p className="muted small">
            {phoneHome ? t("assistant.lede.phone") : t("assistant.lede.desktop")}{" "}
            {!phoneHome &&
              (bedrockConfigured
                ? t("assistant.poweredBy.configured", { brand: activeBrand })
                : t("assistant.poweredBy.rules"))}
          </p>
        </div>
      </header>

      <div className="agent-copilot-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={panel === "ask"}
          className={`agent-copilot-tab${panel === "ask" ? " is-active" : ""}`}
          onClick={() => setTab("ask")}
        >
          {t("assistant.tabs.conversation")}
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
          {t("assistant.tabs.retention")}
        </button>
      </div>

      {panel === "ask" && (
        <>
          <div ref={historyRef} className="agent-copilot-history">
            {turns.length === 0 && (
              <p className="muted small agent-copilot-empty">
                {t("assistant.empty.hint")}
              </p>
            )}
            {turns.map((turn) => (
              <div
                key={turn.id}
                className={`agent-copilot-turn agent-copilot-turn-${turn.role}`}
              >
                <span className="agent-copilot-turn-label">
                  {turn.role === "user" ? t("assistant.turn.user") : t("assistant.turn.assistant")}
                  {turn.role === "assistant" && turn.source && (
                    <span className="agent-copilot-source">
                      {turn.source === "bedrock_tools"
                        ? t("assistant.source.bedrockTools", { brand: activeBrand })
                        : turn.source === "bedrock" || turn.source === "openai_compatible"
                          ? t("assistant.source.bedrock", { brand: activeBrand })
                          : t("assistant.source.rules")}
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
                        isPhone={isPhone}
                        onNavigateContent={enterMobileContent}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          <form className="agent-copilot-form" onSubmit={submit}>
            <label className="visually-hidden" htmlFor="agent-copilot-input">
              {t("assistant.input.label")}
            </label>
            <textarea
              id="agent-copilot-input"
              className="agent-copilot-input"
              rows={3}
              placeholder={t("assistant.input.placeholder")}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onInputKeyDown}
              disabled={sending}
            />
            <button type="submit" className="agent-copilot-send" disabled={sending || !draft.trim()}>
              {sending ? t("assistant.send.thinking") : t("assistant.send.submit")}
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
