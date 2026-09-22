import { useAgentCopilot } from "../agentCopilotContext";
import { useMobileUx } from "../mobileUxContext";
import AgentCopilotSidebar from "./AgentCopilotSidebar";
import CopilotPanelIcon from "./CopilotPanelIcon";

export default function CopilotRail() {
  const { enabled, open, toggleOpen } = useAgentCopilot();
  const { isPhone, mobilePane } = useMobileUx();
  if (!enabled) return null;

  const phoneCopilotHome = isPhone && mobilePane === "copilot";
  const showSidebar = open && (!isPhone || phoneCopilotHome);
  const showDesktopToggle = !isPhone;

  return (
    <div
      className={`copilot-rail${showSidebar ? " is-open" : " is-closed"}${
        phoneCopilotHome ? " copilot-rail-phone-full" : ""
      }`}
    >
      {showDesktopToggle && (
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
      )}
      {showSidebar && <AgentCopilotSidebar phoneHome={phoneCopilotHome} />}
    </div>
  );
}
