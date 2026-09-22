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
import AgentCopilotSidebar from "./components/AgentCopilotSidebar";
import AgentCopilotToggle from "./components/AgentCopilotToggle";
import DataFreshnessStrip from "./components/DataFreshnessStrip";
import ProductsPage from "./pages/ProductsPage";
import AdminPage from "./pages/AdminPage";
import DashboardPage from "./pages/DashboardPage";
import CustomerDetailPage from "./pages/CustomerDetailPage";
import CustomerHubPage from "./pages/CustomerHubPage";
import EngagementHubPage from "./pages/EngagementHubPage";

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
  const location = useLocation();
  const businessActive = isBusinessArea(location.pathname);
  const customerActive = isCustomerArea(location.pathname);
  const engagementActive = isEngagementArea(location.pathname);
  const productsActive = isProductsArea(location.pathname);
  const adminActive = isAdminArea(location.pathname);

  return (
    <aside className="app-side-nav" aria-label="Application areas">
      <div className="app-side-nav-body">
        <p className="app-side-nav-heading">Workspace</p>
        <nav className="app-side-tabs" aria-label="Workspace">
          <Link
            to={BUSINESS_BASE}
            className={`app-side-tab${businessActive ? " is-active" : ""}`}
            aria-current={businessActive ? "page" : undefined}
          >
            <span className="app-side-tab-title">The business</span>
            <span className="app-side-tab-desc muted small">
              Book, cohorts, and portfolio KPIs
            </span>
          </Link>
          <Link
            to={CUSTOMER_BASE}
            className={`app-side-tab${customerActive ? " is-active" : ""}`}
            aria-current={customerActive ? "page" : undefined}
          >
            <span className="app-side-tab-title">The customer</span>
            <span className="app-side-tab-desc muted small">
              360 profile, insights, and outreach
            </span>
          </Link>
          <Link
            to={ENGAGEMENT_BASE}
            className={`app-side-tab${engagementActive ? " is-active" : ""}`}
            aria-current={engagementActive ? "page" : undefined}
          >
            <span className="app-side-tab-title">Engagement</span>
            <span className="app-side-tab-desc muted small">
              Touchpoints, influence, and next best action
            </span>
          </Link>
          <Link
            to={PRODUCTS_BASE}
            className={`app-side-tab${productsActive ? " is-active" : ""}`}
            aria-current={productsActive ? "page" : undefined}
          >
            <span className="app-side-tab-title">Products</span>
            <span className="app-side-tab-desc muted small">
              Product heatmap and customer drill-down
            </span>
          </Link>
        </nav>
      </div>
      <div className="app-side-nav-footer">
        <p className="app-side-nav-heading">Administration</p>
        <nav className="app-side-tabs" aria-label="Administration">
          <Link
            to={ADMIN_BASE}
            className={`app-side-tab app-side-tab-admin${adminActive ? " is-active" : ""}`}
            aria-current={adminActive ? "page" : undefined}
          >
            <span className="app-side-tab-title">Data &amp; admin</span>
            <span className="app-side-tab-desc muted small">
              Health, warehouse, data source
            </span>
          </Link>
        </nav>
      </div>
    </aside>
  );
}

function AppLayout() {
  const { open } = useAgentCopilot();

  return (
    <div className="layout">
      <AgentCopilotToggle />
      <header className="header header-with-copilot-toggle">
        <Link to={BUSINESS_BASE} className="brand">
          Insurance Customer 360
        </Link>
        <span className="tag">Cloudera AI · Business &amp; customer views</span>
      </header>
      <div className={`app-body${open ? " app-body-copilot-open" : ""}`}>
        <AppSideNav />
        <main className="main app-main">
          <DataFreshnessStrip />
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
        <AgentCopilotSidebar />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AgentCopilotProvider>
      <AppLayout />
    </AgentCopilotProvider>
  );
}
