import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useLocation } from "react-router-dom";
import { AgentAction, CustomerSegment, fetchAgentStatus } from "./api";
import { isBusinessArea } from "./appRoutes";
import { parseBusinessSegment } from "./cohortQuery";
import { LlmProviderKind, resolveLlmProvider } from "./llmBrand";

export type CopilotPanel = "ask" | "retention_playbook";

export type CopilotTurn = {
  id: string;
  role: "user" | "assistant";
  text: string;
  actions?: AgentAction[];
  source?: string | null;
  modelId?: string | null;
};

type AgentCopilotContextValue = {
  enabled: boolean;
  agentMode: string;
  bedrockConfigured: boolean;
  llmProvider: LlmProviderKind;
  open: boolean;
  setOpen: (open: boolean) => void;
  toggleOpen: () => void;
  panel: CopilotPanel;
  setPanel: (panel: CopilotPanel) => void;
  turns: CopilotTurn[];
  appendTurn: (turn: CopilotTurn) => void;
  askSegment: CustomerSegment;
  playbookSegment: CustomerSegment;
  setPlaybookSegment: (segment: CustomerSegment) => void;
  playbookCohortLabel: string | null;
  openRetentionPlaybook: (segment: CustomerSegment, cohortLabel?: string | null) => void;
};

const AgentCopilotContext = createContext<AgentCopilotContextValue | null>(null);

function newTurnId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function AgentCopilotProvider({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [enabled, setEnabled] = useState(false);
  const [agentMode, setAgentMode] = useState("rules");
  const [bedrockConfigured, setBedrockConfigured] = useState(false);
  const [llmProvider, setLlmProvider] = useState<LlmProviderKind>("none");
  const [open, setOpen] = useState(true);
  const [panel, setPanel] = useState<CopilotPanel>("ask");
  const [turns, setTurns] = useState<CopilotTurn[]>([]);
  const [playbookSegment, setPlaybookSegment] = useState<CustomerSegment>("customers_all");
  const [playbookCohortLabel, setPlaybookCohortLabel] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void fetchAgentStatus()
      .then((s) => {
        if (!cancelled) {
          setEnabled(s.enabled);
          setAgentMode(s.mode);
          setBedrockConfigured(s.bedrock_configured);
          setLlmProvider(
            resolveLlmProvider({
              provider: s.llm_provider,
              configured: s.llm_configured ?? s.bedrock_configured,
            }),
          );
        }
      })
      .catch(() => {
        if (!cancelled) setEnabled(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const askSegment = useMemo((): CustomerSegment => {
    if (isBusinessArea(location.pathname)) {
      return parseBusinessSegment(new URLSearchParams(location.search));
    }
    return "customers_all";
  }, [location.pathname, location.search]);

  const openRetentionPlaybook = useCallback(
    (segment: CustomerSegment, cohortLabel?: string | null) => {
      setPlaybookSegment(segment);
      setPlaybookCohortLabel(cohortLabel ?? null);
      setPanel("retention_playbook");
      setOpen(true);
    },
    [],
  );

  const appendTurn = useCallback((turn: CopilotTurn) => {
    setTurns((prev) => [...prev, turn]);
  }, []);

  const toggleOpen = useCallback(() => setOpen((v) => !v), []);

  const value = useMemo(
    (): AgentCopilotContextValue => ({
      enabled,
      agentMode,
      bedrockConfigured,
      llmProvider,
      open,
      setOpen,
      toggleOpen,
      panel,
      setPanel,
      turns,
      appendTurn,
      askSegment,
      playbookSegment,
      setPlaybookSegment,
      playbookCohortLabel,
      openRetentionPlaybook,
    }),
    [
      enabled,
      agentMode,
      bedrockConfigured,
      llmProvider,
      open,
      toggleOpen,
      panel,
      turns,
      appendTurn,
      askSegment,
      playbookSegment,
      playbookCohortLabel,
      openRetentionPlaybook,
    ],
  );

  return (
    <AgentCopilotContext.Provider value={value}>{children}</AgentCopilotContext.Provider>
  );
}

export function useAgentCopilot() {
  const ctx = useContext(AgentCopilotContext);
  if (!ctx) {
    throw new Error("useAgentCopilot must be used within AgentCopilotProvider");
  }
  return ctx;
}

export function useAgentCopilotOptional() {
  return useContext(AgentCopilotContext);
}

export { newTurnId };
