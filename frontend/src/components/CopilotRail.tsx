import { useTranslation } from "react-i18next";
import { useAgentCopilot } from "../agentCopilotContext";
import { useMobileUx } from "../mobileUxContext";
import AgentCopilotSidebar from "./AgentCopilotSidebar";
import CopilotPanelIcon from "./CopilotPanelIcon";

export default function CopilotRail() {
  const { t } = useTranslation();
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
          className="header-copilot-btn copilot-toggle"
          onClick={toggleOpen}
          aria-pressed={open}
          aria-label={
            open ? t("assistant.a11y.toggleClose") : t("assistant.a11y.toggleOpen")
          }
          title={open ? t("assistant.toggleTitle.close") : t("assistant.toggleTitle.open")}
        >
          <CopilotPanelIcon />
        </button>
      )}
      {showSidebar && <AgentCopilotSidebar phoneHome={phoneCopilotHome} />}
    </div>
  );
}
