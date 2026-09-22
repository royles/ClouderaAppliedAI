import { useAgentCopilot } from "../agentCopilotContext";
import CopilotPanelIcon from "./CopilotPanelIcon";

export default function AgentCopilotToggle() {
  const { enabled, open, toggleOpen } = useAgentCopilot();
  if (!enabled) return null;

  return (
    <button
      type="button"
      className={`header-copilot-btn${open ? " is-active" : ""}`}
      onClick={toggleOpen}
      aria-pressed={open}
      aria-label={open ? "Close executive copilot" : "Open executive copilot"}
      title={open ? "Close copilot" : "Open copilot"}
    >
      <CopilotPanelIcon />
    </button>
  );
}
