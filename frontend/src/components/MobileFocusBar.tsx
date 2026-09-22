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

function focusTitle(pathname: string): string {
  if (pathname === BUSINESS_BASE || isBusinessArea(pathname)) return "Business KPIs";
  if (pathname === CUSTOMER_BASE) return "Customers";
  if (pathname.startsWith(`${CUSTOMER_BASE}/`)) return "Customer profile";
  if (isProductsArea(pathname)) return "Products";
  if (isEngagementArea(pathname)) return "Engagement";
  if (isAdminArea(pathname)) return "Admin";
  return "Details";
}

export default function MobileFocusBar() {
  const { returnToMobileCopilot } = useMobileUx();
  const location = useLocation();
  const title = focusTitle(location.pathname);

  return (
    <header className="mobile-focus-bar">
      <button type="button" className="mobile-focus-back" onClick={returnToMobileCopilot}>
        ← Copilot
      </button>
      <span className="mobile-focus-title">{title}</span>
    </header>
  );
}
