// frontend/src/App.tsx
import React from "react";
import { Routes, Route, NavLink, Navigate, Outlet, useNavigate } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import TransactionsPage from "./pages/TransactionsPage";
import ReceiptScannerPage from "./pages/ReceiptScannerPage";
import ForecastPage from "./pages/ForecastPage";
import AnomaliesPage from "./pages/AnomaliesPage";
import AIAssistantPage from "./pages/AIAssistantPage";
import BankConnectionPage from "./pages/BankConnectionPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import PlannedPage from "./pages/PlannedPage";

const ProtectedLayout: React.FC = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem("access_token");

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login");
  };

  const coreLinks = [
    { to: "/dashboard", label: "Dashboard", icon: "📊" },
    { to: "/transactions", label: "Transactions", icon: "💳" },
    { to: "/receipt-scanner", label: "Receipt Scanner", icon: "🧾" },
    { to: "/forecast", label: "Forecast", icon: "📈" },
    { to: "/anomalies", label: "Anomalies", icon: "🛡️" },
    { to: "/ai-assistant", label: "AI Assistant", icon: "✨" },
    { to: "/bank-connection", label: "Bank Connection", icon: "🏦" },
  ];

  const plannedLinks = [
    { to: "/budgets", label: "Budgets", icon: "🎯" },
    { to: "/settings", label: "Settings", icon: "⚙️" },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col md:flex-row font-sans">
      {/* Dark Sidebar */}
      <aside className="w-full md:w-64 bg-slate-900 border-r border-slate-800 flex flex-col md:min-h-screen">
        {/* Brand header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              FP
            </div>
            <div>
              <span className="text-lg font-bold text-white tracking-tight">FinPulse AI</span>
              <span className="block text-[10px] uppercase font-semibold text-indigo-400 tracking-wider">
                Financial Engine
              </span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto px-4 py-5 space-y-6">
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 px-3">
              Active Modules
            </span>
            <nav className="mt-2 space-y-1">
              {coreLinks.map(({ to, label, icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors ${
                      isActive
                        ? "bg-indigo-600 text-white shadow-sm"
                        : "text-slate-300 hover:bg-slate-800 hover:text-white"
                    }`
                  }
                >
                  <span className="mr-3 text-base">{icon}</span>
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>

          <div>
            <div className="flex items-center justify-between px-3">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Next Phase
              </span>
              <span className="text-[10px] font-bold text-indigo-400 bg-indigo-950/70 border border-indigo-800 px-1.5 py-0.2 rounded">
                PLANNED
              </span>
            </div>
            <nav className="mt-2 space-y-1">
              {plannedLinks.map(({ to, label, icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `flex items-center px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                      isActive
                        ? "bg-indigo-900/60 text-indigo-200 border border-indigo-700"
                        : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                    }`
                  }
                >
                  <span className="mr-3 text-sm opacity-80">{icon}</span>
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>

        {/* Footer & Logout */}
        <div className="p-4 border-t border-slate-800">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800/80 hover:bg-rose-900/40 hover:text-rose-200 border border-slate-700 hover:border-rose-700 rounded-lg transition-colors"
          >
            <span className="mr-2">🚪</span>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 bg-slate-50 min-h-screen overflow-y-auto">
        <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          localStorage.getItem("access_token") ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <LoginPage />
          )
        }
      />
      <Route
        path="/register"
        element={
          localStorage.getItem("access_token") ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <RegisterPage />
          )
        }
      />

      <Route element={<ProtectedLayout />}>
        {/* Core Live Pages */}
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/receipt-scanner" element={<ReceiptScannerPage />} />
        <Route path="/forecast" element={<ForecastPage />} />
        <Route path="/anomalies" element={<AnomaliesPage />} />
        <Route path="/ai-assistant" element={<AIAssistantPage />} />
        <Route path="/bank-connection" element={<BankConnectionPage />} />

        {/* Planned Next Phase Pages */}
        <Route
          path="/budgets"
          element={
            <PlannedPage
              featureName="Budgets"
              description="Configurable monthly category spending limits with progress indicators and threshold alert webhooks."
              icon="🎯"
            />
          }
        />
        <Route
          path="/settings"
          element={
            <PlannedPage
              featureName="Settings & Preferences"
              description="User profile management, security key rotation, notification preferences, and currency settings."
              icon="⚙️"
            />
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;
