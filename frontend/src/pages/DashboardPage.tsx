// frontend/src/pages/DashboardPage.tsx
import React, { useEffect, useState, useRef } from "react";
import SummaryCard from "../components/SummaryCard";
import { fetchDashboardSummary } from "../services/dashboard";
import { syncPlaidTransactions } from "../services/plaid";
import { DashboardSummary } from "../types/dashboard";
import { formatINR, formatDateIN } from "../utils/format";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";

const PIE_COLORS = ["#10b981", "#6366f1", "#f59e0b", "#ec4899", "#06b6d4", "#8b5cf6", "#f97316", "#64748b"];

const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const prevTxCountRef = useRef<number | null>(null);

  const loadData = async (isBackground = false) => {
    try {
      if (!isBackground) setLoading(true);
      setError(null);
      const summary = await fetchDashboardSummary();
      setData(summary);

      // Check for incoming transactions to show toast
      const curCount = summary.recent_transactions.length;
      if (prevTxCountRef.current !== null && curCount > prevTxCountRef.current) {
        const diff = curCount - prevTxCountRef.current;
        setToastMessage(`${diff} new transaction${diff > 1 ? "s" : ""} received!`);
        setTimeout(() => setToastMessage(null), 5000);
      }
      prevTxCountRef.current = curCount;
    } catch (e: any) {
      if (!isBackground) {
        setError(e.response?.data?.detail || e.message || "Failed to load dashboard summary");
      }
    } finally {
      if (!isBackground) setLoading(false);
    }
  };

  const handleManualRefresh = async () => {
    setRefreshing(true);
    try {
      const syncRes = await syncPlaidTransactions();
      if (syncRes && syncRes.synced > 0) {
        setToastMessage(`${syncRes.synced} new transaction(s) synced from bank.`);
        setTimeout(() => setToastMessage(null), 5000);
      }
      await loadData(true);
    } catch {
      await loadData(true);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    // Auto-refresh every 30 seconds for live updates
    const timer = setInterval(() => {
      loadData(true);
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600"></div>
        <span className="ml-3 text-slate-600 font-medium">Loading your Indian financial summary...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 text-rose-700 px-5 py-4 rounded-lg shadow-xs">
        <p className="font-semibold text-base">Unable to load dashboard</p>
        <p className="text-sm mt-1">{error}</p>
        <button
          onClick={() => loadData()}
          className="mt-3 px-4 py-1.5 bg-rose-600 text-white rounded text-sm font-medium hover:bg-rose-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const pieData = (data.expense_by_category || []).map((c) => ({
    name: c.category,
    value: c.total,
  }));

  const cashFlowData = (data.monthly_cash_flow || []).map((cf) => ({
    month: cf.month,
    Income: cf.income,
    Expenses: cf.expenses,
  }));

  const dailyTrendData = data.daily_spending_trend || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-5 right-5 z-50 bg-emerald-700 text-white px-4 py-3 rounded-lg shadow-lg flex items-center space-x-2 animate-fade-in border border-emerald-500">
          <span>✨</span>
          <span className="text-sm font-medium">{toastMessage}</span>
        </div>
      )}

      {/* Header with Bank Badge and Refresh Button */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <span>Daily Expense Dashboard</span>
            <span className="text-xs font-semibold bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full">
              INR (₹)
            </span>
          </h1>
          <p className="text-sm text-slate-500">
            Automated bank sync, UPI payments, and daily spending pulse
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <span className="text-xs text-slate-400 block font-medium">Bank Account</span>
            <span className="text-xs font-semibold text-slate-700">{data.bank_name || "HDFC Bank (Sandbox)"}</span>
          </div>

          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="inline-flex items-center px-3.5 py-2 border border-slate-300 text-sm font-medium rounded-lg text-slate-700 bg-white hover:bg-slate-50 shadow-xs transition-colors disabled:opacity-50"
            title="Refresh transactions and bank feed"
          >
            <svg
              className={`w-4 h-4 mr-2 text-slate-500 ${refreshing ? "animate-spin text-emerald-600" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {/* Anomaly Alert Notice if any unreviewed */}
      {data.unreviewed_anomalies_count > 0 && (
        <div className="bg-amber-50 border border-amber-200 text-amber-900 px-4 py-3 rounded-lg flex items-center justify-between text-sm shadow-xs">
          <div className="flex items-center space-x-2">
            <span className="text-base">⚠️</span>
            <span>
              <strong>{data.unreviewed_anomalies_count} unusual transaction{data.unreviewed_anomalies_count > 1 ? "s" : ""}</strong> flagged by Isolation Forest for review.
            </span>
          </div>
          <a href="/anomalies" className="text-xs font-semibold text-amber-800 underline hover:text-amber-950">
            View Anomalies &rarr;
          </a>
        </div>
      )}

      {/* Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Total Ledger Balance"
          value={formatINR(data.total_balance)}
          color={data.total_balance >= 0 ? "text-slate-900" : "text-rose-600"}
        />
        <SummaryCard
          title="Today's Spend"
          value={formatINR(data.today_spend)}
          color="text-amber-600"
        />
        <SummaryCard
          title="This Month's Spending"
          value={formatINR(data.monthly_expenses)}
          color="text-rose-600"
        />
        <SummaryCard
          title="Monthly Savings (Net)"
          value={formatINR(data.monthly_savings)}
          color={data.monthly_savings >= 0 ? "text-emerald-600" : "text-rose-500"}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Spending Trend for current month */}
        <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-base font-semibold text-slate-800">Daily Spending Trend (Current Month)</h2>
            <span className="text-xs text-slate-400">DD/MM</span>
          </div>
          <p className="text-xs text-slate-500 mb-4">Daily outgoings including UPI, card, and bill payments</p>
          {dailyTrendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={dailyTrendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v) => `₹${Number(v) >= 1000 ? `${(Number(v) / 1000).toFixed(0)}k` : v}`}
                />
                <Tooltip
                  formatter={(val: any) => [formatINR(Number(val)), "Spend"]}
                  contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                />
                <Line
                  type="monotone"
                  dataKey="amount"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "#10b981" }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-slate-400 text-sm">
              No daily expenses recorded for this month yet.
            </div>
          )}
        </section>

        {/* Expenses by Category */}
        <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
          <h2 className="text-base font-semibold text-slate-800 mb-1">Expenses by Category</h2>
          <p className="text-xs text-slate-500 mb-4">Indian spending categories distribution</p>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  innerRadius={45}
                  paddingAngle={3}
                >
                  {pieData.map((_, i) => (
                    <Cell key={`cell-${i}`} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any) => [formatINR(Number(value)), "Total"]}
                  contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                />
                <Legend iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-slate-400 text-sm">
              No expense categories recorded yet.
            </div>
          )}
        </section>
      </div>

      {/* Monthly Cash Flow Inflow vs Outflow */}
      <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
        <h2 className="text-base font-semibold text-slate-800 mb-1">Monthly Cash Inflow vs Outflow</h2>
        <p className="text-xs text-slate-500 mb-4">Salary credits and other incomes against total monthly outgoings</p>
        {cashFlowData.length > 0 ? (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={cashFlowData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                tickFormatter={(v) => `₹${Number(v) >= 1000 ? `${(Number(v) / 1000).toFixed(0)}k` : v}`}
              />
              <Tooltip
                formatter={(value: any) => [formatINR(Number(value)), ""]}
                contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
              />
              <Legend />
              <Bar dataKey="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Expenses" fill="#f43f5e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
            Cash flow data will populate as transactions are synced.
          </div>
        )}
      </section>

      {/* Recent Transactions Table */}
      <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-800">Recent Transactions</h2>
            <p className="text-xs text-slate-500">Live entries across Bank, Receipt OCR, and Manual sources</p>
          </div>
          <a href="/transactions" className="text-xs font-semibold text-emerald-600 hover:text-emerald-700">
            View All &rarr;
          </a>
        </div>
        {data.recent_transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-500 uppercase text-[11px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Date</th>
                  <th className="py-2.5 px-4 font-semibold">Merchant / Description</th>
                  <th className="py-2.5 px-4 font-semibold">Category</th>
                  <th className="py-2.5 px-4 font-semibold">Mode</th>
                  <th className="py-2.5 px-4 font-semibold">Source</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.recent_transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                      {formatDateIN(tx.transaction_date)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-800">{tx.merchant || tx.description || "General Transaction"}</div>
                      {tx.is_anomaly && (
                        <span className="inline-block mt-0.5 text-[10px] bg-amber-100 text-amber-800 font-semibold px-1.5 py-0.2 rounded">
                          Unusual
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-600 text-xs">{tx.category}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700">
                        {tx.payment_mode || "UPI"}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium capitalize ${
                          tx.source === "bank" || tx.source === "bank_demo_feed"
                            ? "bg-blue-100 text-blue-800"
                            : tx.source === "receipt_ocr"
                            ? "bg-purple-100 text-purple-800"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {tx.source === "bank" || tx.source === "bank_demo_feed"
                          ? "Bank"
                          : tx.source === "receipt_ocr"
                          ? "Receipt"
                          : "Manual"}
                      </span>
                    </td>
                    <td
                      className={`py-3 px-4 text-right font-semibold whitespace-nowrap ${
                        tx.transaction_type === "income" ? "text-emerald-600" : "text-slate-800"
                      }`}
                    >
                      {tx.transaction_type === "income" ? "+" : "-"}
                      {formatINR(tx.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-slate-400 text-sm">
            No transactions found.
          </div>
        )}
      </section>

      {/* Subtle Demo Notice Footer */}
      <footer className="text-center pt-2">
        <p className="text-xs text-slate-400">
          {data.bank_demo_notice} &bull; All forecasts are statistical estimates and not guarantees.
        </p>
      </footer>
    </div>
  );
};

export default DashboardPage;
