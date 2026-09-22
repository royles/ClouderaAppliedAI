import { Link, Navigate, Route, Routes, useLocation, useParams } from "react-router-dom";
import {
  ADMIN_BASE,
  BUSINESS_BASE,
  CUSTOMER_BASE,
  isAdminArea,
  isBusinessArea,
  isCustomerArea,
  isEngagementArea,
  ENGAGEMENT_BASE,
  isProductsArea,
  PRODUCTS_BASE,
} from "./appRoutes";
import { AgentCopilotProvider, useAgentCopilot } from "./agentCopilotContext";
import CopilotRail from "./components/CopilotRail";
import DataFreshnessStrip from "./components/DataFreshnessStrip";
import MobileCopilotDock from "./components/MobileCopilotDock";
import MobileFocusBar from "./components/MobileFocusBar";
import { MobileUxProvider, useMobileUx } from "./mobileUxContext";
import ProductsPage from "./pages/ProductsPage";
import AdminPage from "./pages/AdminPage";
import DashboardPage from "./pages/DashboardPage";
import CustomerDetailPage from "./pages/CustomerDetailPage";
import CustomerHubPage from "./pages/CustomerHubPage";
import EngagementHubPage from "./pages/EngagementHubPage";
import LanguageSwitcher from "./components/LanguageSwitcher";
import { ThemeProvider } from "./theme/ThemeContext";
import { useTranslation } from "react-i18next";

function LegacyRootRedirect() {
  const location = useLocation();
  const target = `${BUSINESS_BASE}${location.search}`;
  return <Navigate to={target} replace />;
}

function LegacyCustomerRedirect() {
  const location = useLocation();
  const { customerId } = useParams();
  if (!customerId) return <Navigate to={CUSTOMER_BASE} replace />;
  return (
    <Navigate to={`${CUSTOMER_BASE}/${customerId}`} replace state={location.state} />
  );
}

function AppSideNav() {
  const { t } = useTranslation();
  const location = useLocation();
  const businessActive = isBusinessArea(location.pathname);
  const customerActive = isCustomerArea(location.pathname);
  const engagementActive = isEngagementArea(location.pathname);
  const productsActive = isProductsArea(location.pathname);
  const adminActive = isAdminArea(location.pathname);

  return (
    <aside className="app-side-nav" aria-label={t("app.a11y.applicationAreas")}>
      <div className="app-side-nav-body">
        <p className="app-side-nav-heading">{t("nav.workspace")}</p>
        <nav className="app-side-tabs" aria-label={t("nav.workspace")}>
          <Link
            to={BUSINESS_BASE}
            className={`app-side-tab${businessActive ? " is-active" : ""}`}
            aria-current={businessActive ? "page" : undefined}
          >
            <span className="app-side-tab-title">{t("nav.business.title")}</span>
            <span className="app-side-tab-desc muted small">
              {t("nav.business.desc")}
            </span>
          </Link>
          <Link
            to={CUSTOMER_BASE}
            className={`app-side-tab${customerActive ? " is-active" : ""}`}
            aria-current={customerActive ? "page" : undefined}
          >
            <span className="app-side-tab-title">{t("nav.customer.title")}</span>
            <span className="app-side-tab-desc muted small">
              {t("nav.customer.desc")}
            </span>
          </Link>
          <Link
            to={ENGAGEMENT_BASE}
            className={`app-side-tab${engagementActive ? " is-active" : ""}`}
            aria-current={engagementActive ? "page" : undefined}
          >
            <span className="app-side-tab-title">{t("nav.engagement.title")}</span>
            <span className="app-side-tab-desc muted small">
              {t("nav.engagement.desc")}
            </span>
          </Link>
          <Link
            to={PRODUCTS_BASE}
            className={`app-side-tab${productsActive ? " is-active" : ""}`}
            aria-current={productsActive ? "page" : undefined}
          >
            <span className="app-side-tab-title">{t("nav.products.title")}</span>
            <span className="app-side-tab-desc muted small">
              {t("nav.products.desc")}
            </span>
          </Link>
        </nav>
      </div>
      <div className="app-side-nav-footer">
        <p className="app-side-nav-heading">{t("nav.admin.section")}</p>
        <nav className="app-side-tabs" aria-label={t("app.a11y.administrationNav")}>
          <Link
            to={ADMIN_BASE}
            className={`app-side-tab app-side-tab-admin${adminActive ? " is-active" : ""}`}
            aria-current={adminActive ? "page" : undefined}
          >
            <span className="app-side-tab-title">{t("nav.admin.title")}</span>
            <span className="app-side-tab-desc muted small">
              {t("nav.admin.desc")}
            </span>
          </Link>
        </nav>
      </div>
    </aside>
  );
}

function AppLayout() {
  const { t } = useTranslation();
  const { enabled, open } = useAgentCopilot();
  const { isPhone, mobilePane, mobileFocus } = useMobileUx();
  const showMain = !isPhone || mobilePane === "content";
  const phoneCopilotHome = isPhone && mobilePane === "copilot";

  return (
    <div
      className={`layout${isPhone ? " layout-phone" : ""}${
        phoneCopilotHome ? " layout-phone-copilot" : ""
      }${mobileFocus ? " layout-phone-content" : ""}`}
    >
      {!phoneCopilotHome && (
        <header className={`header${isPhone ? " header-phone" : ""}`}>
          <Link to={BUSINESS_BASE} className="brand">
            {t("app.brand.title")}
          </Link>
          {!isPhone && (
            <span className="tag">{t("app.brand.tagline")}</span>
          )}
          <LanguageSwitcher />
        </header>
      )}
      <div
        className={`app-body${open && !phoneCopilotHome ? " app-body-copilot-open" : ""}${
          phoneCopilotHome ? " app-body-phone-copilot" : ""
        }`}
      >
        {!isPhone && <AppSideNav />}
        {showMain && (
          <main className="main app-main">
            {!isPhone && <DataFreshnessStrip />}
            {mobileFocus && <MobileFocusBar />}
            <Routes>
            <Route path="/" element={<LegacyRootRedirect />} />
            <Route path={BUSINESS_BASE} element={<DashboardPage />} />
            <Route path={CUSTOMER_BASE} element={<CustomerHubPage />} />
            <Route path={`${CUSTOMER_BASE}/:customerId`} element={<CustomerDetailPage />} />
            <Route path={ENGAGEMENT_BASE} element={<EngagementHubPage />} />
            <Route path={PRODUCTS_BASE} element={<ProductsPage />} />
            <Route path={ADMIN_BASE} element={<AdminPage />} />
            <Route path="/customers/:customerId" element={<LegacyCustomerRedirect />} />
            <Route path="*" element={<Navigate to={BUSINESS_BASE} replace />} />
            </Routes>
          </main>
        )}
        <CopilotRail />
        {mobileFocus && <MobileCopilotDock />}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AgentCopilotProvider>
        <MobileUxProvider>
          <AppLayout />
        </MobileUxProvider>
      </AgentCopilotProvider>
    </ThemeProvider>
  );
}
