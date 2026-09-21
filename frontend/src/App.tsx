import { Link, Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import CustomerDetailPage from "./pages/CustomerDetailPage";

export default function App() {
  return (
    <div className="layout">
      <header className="header">
        <Link to="/" className="brand">
          Insurance Customer 360
        </Link>
        <span className="tag">
          Cloudera AI · SQLite warehouse · cohort filters sync to the URL
        </span>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/customers/:customerId" element={<CustomerDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}
