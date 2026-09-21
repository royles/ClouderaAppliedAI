import { Link, Navigate, Route, Routes, useLocation, useParams } from "react-router-dom";
import {
  ADMIN_BASE,
  BUSINESS_BASE,
  CUSTOMER_BASE,
  isAdminArea,
  isBusinessArea,
  isCustomerArea,
} from "./appRoutes";
import AdminPage from "./pages/AdminPage";
import DashboardPage from "./pages/DashboardPage";
import CustomerDetailPage from "./pages/CustomerDetailPage";
import CustomerHubPage from "./pages/CustomerHubPage";

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
  const adminActive = isAdminArea(location.pathname);

  return (
    <aside className="app-side-nav" aria-label="Application areas">
      <p className="app-side-nav-heading">Workspace</p>
      <nav className="app-side-tabs">
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
          to={ADMIN_BASE}
          className={`app-side-tab${adminActive ? " is-active" : ""}`}
          aria-current={adminActive ? "page" : undefined}
        >
          <span className="app-side-tab-title">Data &amp; admin</span>
          <span className="app-side-tab-desc muted small">
            Tables, lineage, load times, quality
          </span>
        </Link>
      </nav>
    </aside>
  );
}

export default function App() {
  return (
    <div className="layout">
      <header className="header">
        <Link to={BUSINESS_BASE} className="brand">
          Insurance Customer 360
        </Link>
        <span className="tag">Cloudera AI · Business &amp; customer views</span>
      </header>
      <div className="app-body">
        <AppSideNav />
        <main className="main app-main">
          <Routes>
            <Route path="/" element={<LegacyRootRedirect />} />
            <Route path={BUSINESS_BASE} element={<DashboardPage />} />
            <Route path={CUSTOMER_BASE} element={<CustomerHubPage />} />
            <Route path={`${CUSTOMER_BASE}/:customerId`} element={<CustomerDetailPage />} />
            <Route path={ADMIN_BASE} element={<AdminPage />} />
            <Route path="/customers/:customerId" element={<LegacyCustomerRedirect />} />
            <Route path="*" element={<Navigate to={BUSINESS_BASE} replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
