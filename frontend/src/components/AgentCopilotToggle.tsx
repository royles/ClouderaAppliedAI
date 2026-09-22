import { useAgentCopilot } from "../agentCopilotContext";

export default function AgentCopilotToggle() {
  const { enabled, open, toggleOpen } = useAgentCopilot();
  if (!enabled) return null;

  return (
    <button
      type="button"
      className={`header-copilot-btn${open ? " is-active" : ""}`}
      onClick={toggleOpen}
      aria-pressed={open}
    >
      Copilot
    </button>
  );
}
