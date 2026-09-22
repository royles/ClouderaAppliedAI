import { useAgentCopilot } from "../agentCopilotContext";
import AgentCopilotSidebar from "./AgentCopilotSidebar";
import CopilotPanelIcon from "./CopilotPanelIcon";

export default function CopilotRail() {
  const { enabled, open, toggleOpen } = useAgentCopilot();
  if (!enabled) return null;

  return (
    <div className={`copilot-rail${open ? " is-open" : " is-closed"}`}>
      <button
        type="button"
        className={`header-copilot-btn copilot-toggle${open ? " copilot-toggle-docked" : ""}`}
        onClick={toggleOpen}
        aria-pressed={open}
        aria-label={open ? "Close executive copilot" : "Open executive copilot"}
        title={open ? "Close copilot" : "Open copilot"}
      >
        <CopilotPanelIcon />
      </button>
      {open && <AgentCopilotSidebar />}
    </div>
  );
}
