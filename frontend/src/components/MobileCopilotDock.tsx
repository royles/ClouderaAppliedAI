import { useTranslation } from "react-i18next";
import CopilotPanelIcon from "./CopilotPanelIcon";
import { useMobileUx } from "../mobileUxContext";

export default function MobileCopilotDock() {
  const { t } = useTranslation();
  const { returnToMobileCopilot } = useMobileUx();

  return (
    <div className="mobile-copilot-dock" role="navigation" aria-label={t("copilot.shortTitle")}>
      <button type="button" className="mobile-copilot-dock-btn" onClick={returnToMobileCopilot}>
        <CopilotPanelIcon />
        <span>{t("copilot.shortTitle")}</span>
      </button>
    </div>
  );
}
