import CopilotPanelIcon from "./CopilotPanelIcon";
import { useMobileUx } from "../mobileUxContext";

export default function MobileCopilotDock() {
  const { returnToMobileCopilot } = useMobileUx();

  return (
    <div className="mobile-copilot-dock" role="navigation" aria-label="Copilot">
      <button type="button" className="mobile-copilot-dock-btn" onClick={returnToMobileCopilot}>
        <CopilotPanelIcon />
        <span>Copilot</span>
      </button>
    </div>
  );
}
