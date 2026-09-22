import { useTranslation } from "react-i18next";
import { useLocation } from "react-router-dom";
import {
  BUSINESS_BASE,
  CUSTOMER_BASE,
  isAdminArea,
  isBusinessArea,
  isEngagementArea,
  isProductsArea,
} from "../appRoutes";
import { useMobileUx } from "../mobileUxContext";

function focusTitle(pathname: string, t: (key: string) => string): string {
  if (pathname === BUSINESS_BASE || isBusinessArea(pathname)) return t("mobile.focusTitle.business");
  if (pathname === CUSTOMER_BASE) return t("mobile.focusTitle.customers");
  if (pathname.startsWith(`${CUSTOMER_BASE}/`)) return t("mobile.focusTitle.customerProfile");
  if (isProductsArea(pathname)) return t("mobile.focusTitle.products");
  if (isEngagementArea(pathname)) return t("mobile.focusTitle.engagement");
  if (isAdminArea(pathname)) return t("mobile.focusTitle.admin");
  return t("mobile.focusTitle.details");
}

export default function MobileFocusBar() {
  const { t } = useTranslation();
  const { returnToMobileCopilot } = useMobileUx();
  const location = useLocation();
  const title = focusTitle(location.pathname, t);

  return (
    <header className="mobile-focus-bar">
      <button type="button" className="mobile-focus-back" onClick={returnToMobileCopilot}>
        {t("mobile.backToCopilot")}
      </button>
      <span className="mobile-focus-title">{title}</span>
    </header>
  );
}
