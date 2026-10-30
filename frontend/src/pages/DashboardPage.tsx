// frontend/src/pages/DashboardPage.tsx
import React, { useEffect, useState } from "react";
import SummaryCard from "../components/SummaryCard";
import { fetchDashboardSummary } from "../services/dashboard";
import { loadSampleData } from "../services/transaction";
import { DashboardSummary } from "../types/dashboard";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { format } from "date-fns";

const PIE_COLORS = ["#4f46e5", "#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#64748b"];

const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingSample, setLoadingSample] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);

  const loadData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      setError(null);
      const summary = await fetchDashboardSummary();
      setData(summary);
    } catch (e: any) {
      if (!silent) {
        setError(e.response?.data?.detail || e.message || "Failed to load dashboard");
      }
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Auto-refresh dashboard data every 30 seconds for live bank sync updates
    const timer = setInterval(() => {
      loadData(true);
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  const handleLoadSample = async () => {
    try {
      setLoadingSample(true);
      setBanner(null);
      const res = await loadSampleData();
      setBanner(res.message);
      await loadData();
    } catch (e: any) {
      setBanner(e.response?.data?.detail || "Failed to load sample data.");
    } finally {
      setLoadingSample(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
        <span className="ml-3 text-slate-600 font-medium">Loading financial dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-md">
        <p className="font-semibold">Unable to load dashboard</p>
        <p className="text-sm">{error}</p>
        <button
          onClick={() => loadData()}
          className="mt-3 px-3 py-1 bg-rose-600 text-white rounded text-sm hover:bg-rose-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const pieData = data.expense_by_category.map((c) => ({
    name: c.category,
    value: c.total,
  }));

  const cashFlowData = (data.monthly_cash_flow || []).map((cf) => ({
    month: cf.month,
    Income: cf.income,
    Expenses: cf.expenses,
  }));

  return (
    <div className="space-y-6">
      {/* Top Header & Sample Data Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Financial Overview</h1>
          <p className="text-sm text-slate-500">Real-time balances, spending analytics and monthly cash flow</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleLoadSample}
            disabled={loadingSample}
            className="inline-flex items-center px-4 py-2 border border-indigo-600 text-sm font-medium rounded-md shadow-sm text-indigo-600 bg-white hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {loadingSample ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-indigo-600" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                </svg>
                Generating 6 Months Data...
              </>
            ) : (
              "Load Sample Data"
            )}
          </button>
        </div>
      </div>

      {/* Notification Banner */}
      {banner && (
        <div className="bg-indigo-50 border border-indigo-200 text-indigo-800 px-4 py-3 rounded-md flex items-center justify-between">
          <span className="text-sm">{banner}</span>
          <button
            onClick={() => setBanner(null)}
            className="text-indigo-500 hover:text-indigo-800 text-sm font-semibold ml-4"
          >
            &times;
          </button>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Total Balance"
          value={`$${data.total_balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          color={data.total_balance >= 0 ? "text-slate-900" : "text-rose-600"}
        />
        <SummaryCard
          title="Total Income"
          value={`$${data.total_income.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          color="text-emerald-600"
        />
        <SummaryCard
          title="Total Expenses"
          value={`$${data.total_expenses.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          color="text-rose-600"
        />
        <SummaryCard
          title="Monthly Savings (Current)"
          value={`$${data.monthly_savings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          color={data.monthly_savings >= 0 ? "text-indigo-600" : "text-rose-500"}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Income vs Expenses by Month */}
        <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
          <h2 className="text-base font-semibold text-slate-800 mb-1">Income vs Expense by Month</h2>
          <p className="text-xs text-slate-500 mb-4">Comparison of inflow vs outflow per month</p>
          {cashFlowData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={cashFlowData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} />
                <Tooltip
                  formatter={(value: any) => [`$${Number(value).toFixed(2)}`, ""]}
                  contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                />
                <Legend />
                <Bar dataKey="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Expenses" fill="#f43f5e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
              No cash flow data available yet. Click "Load Sample Data" to populate.
            </div>
          )}
        </section>

        {/* Expenses by Category */}
        <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
          <h2 className="text-base font-semibold text-slate-800 mb-1">Expenses by Category</h2>
          <p className="text-xs text-slate-500 mb-4">Breakdown of expense distribution</p>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  innerRadius={45}
                  paddingAngle={3}
                >
                  {pieData.map((_, i) => (
                    <Cell key={`cell-${i}`} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any) => [`$${Number(value).toFixed(2)}`, "Total"]}
                  contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
              No expense categories recorded yet.
            </div>
          )}
        </section>
      </div>

      {/* Recent Transactions Table */}
      <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-800">Recent Transactions</h2>
            <p className="text-xs text-slate-500">Last 5 recorded financial entries across all channels</p>
          </div>
        </div>
        {data.recent_transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Date</th>
                  <th className="py-2.5 px-4 font-semibold">Type</th>
                  <th className="py-2.5 px-4 font-semibold">Category</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.recent_transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 text-slate-600">
                      {format(new Date(tx.transaction_date), "MMM d, yyyy")}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize ${
                          tx.transaction_type === "income"
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-rose-100 text-rose-800"
                        }`}
                      >
                        {tx.transaction_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-700 font-medium">{tx.category}</td>
                    <td
                      className={`py-3 px-4 text-right font-semibold ${
                        tx.transaction_type === "income" ? "text-emerald-600" : "text-slate-800"
                      }`}
                    >
                      {tx.transaction_type === "income" ? "+" : "-"}${tx.amount.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-slate-400 text-sm">
            No transactions found. Click "Load Sample Data" to initialize.
          </div>
        )}
      </section>
    </div>
  );
};

export default DashboardPage;
