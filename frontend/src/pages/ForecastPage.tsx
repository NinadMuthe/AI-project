// frontend/src/pages/ForecastPage.tsx
import React, { useEffect, useState } from "react";
import { fetchForecast, ForecastResponse } from "../services/forecast";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { format } from "date-fns";

const ForecastPage: React.FC = () => {
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [horizon, setHorizon] = useState<number>(30);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadForecast = async (h: number) => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchForecast(h);
      setData(res);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || "Failed to load forecast");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadForecast(horizon);
  }, [horizon]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
        <span className="ml-3 text-slate-600 font-medium">Training and running PyTorch LSTM forecast...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-md">
        <p className="font-semibold">Forecast Error</p>
        <p className="text-sm">{error}</p>
        <button
          onClick={() => loadForecast(horizon)}
          className="mt-3 px-3 py-1 bg-rose-600 text-white rounded text-sm hover:bg-rose-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-800">Cash Flow & Expense Forecast</h1>
            {data.is_baseline ? (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
                BASELINE PROJECTION
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-300">
                PyTorch LSTM Neural Network
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-1">{data.message || data.model_used}</p>
        </div>

        {/* Horizon selector */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-slate-700">Horizon:</label>
          <select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            className="border border-slate-300 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value={15}>Next 15 Days</option>
            <option value={30}>Next 30 Days</option>
            <option value={45}>Next 45 Days</option>
            <option value={60}>Next 60 Days</option>
          </select>
        </div>
      </div>

      {/* Model explanation banner */}
      {data.is_baseline && (
        <div className="bg-amber-50 border border-amber-200 text-amber-900 px-4 py-3 rounded-lg text-sm">
          <strong>Notice:</strong> This account does not yet have 30+ days of expense history. A 7-day moving average
          baseline forecast is displayed instead of simulated neural model output.
        </div>
      )}

      {/* Shortage Warning Banner */}
      {data.shortage_flag && (
        <div className="bg-rose-50 border-l-4 border-rose-500 p-4 rounded-r-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0 text-rose-500 font-bold text-xl mr-3">⚠</div>
            <div>
              <h3 className="text-sm font-bold text-rose-800">Projected Month-End Cash Shortage Detected</h3>
              <p className="text-sm text-rose-700 mt-1">{data.shortage_warning}</p>
            </div>
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Current Balance</span>
          <div className="mt-1 text-2xl font-bold text-slate-900">${data.current_balance.toFixed(2)}</div>
          <span className="text-xs text-slate-400">Real-time ledger balance</span>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Projected Balance ({horizon}d)
          </span>
          <div
            className={`mt-1 text-2xl font-bold ${
              data.projected_end_balance >= 0 ? "text-emerald-600" : "text-rose-600"
            }`}
          >
            ${data.projected_end_balance.toFixed(2)}
          </div>
          <span className="text-xs text-slate-400">At end of forecast window</span>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Cash Flow Risk</span>
          <div
            className={`mt-1 text-2xl font-bold ${data.shortage_flag ? "text-rose-600" : "text-emerald-600"}`}
          >
            {data.shortage_flag ? "High Shortage Risk" : "Stable Buffer"}
          </div>
          <span className="text-xs text-slate-400">
            {data.shortage_flag ? `Deficit onset: ${data.shortage_date}` : "Positive balance maintained"}
          </span>
        </div>
      </div>

      {/* Recharts Forecast Chart */}
      <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
        <div className="mb-4">
          <h2 className="text-base font-semibold text-slate-800">Historical vs Forecasted Daily Expenses</h2>
          <p className="text-xs text-slate-500">
            Solid line depicts verified historical spend; dashed line represents model projections.
          </p>
        </div>

        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={data.series}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis
              dataKey="date"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              tickFormatter={(d) => {
                try {
                  return format(new Date(d), "MMM d");
                } catch {
                  return d;
                }
              }}
            />
            <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
            <Tooltip
              formatter={(value: any, name: string) => {
                if (value === null || value === undefined) return ["-", name];
                return [`$${Number(value).toFixed(2)}`, name];
              }}
              labelFormatter={(label) => {
                try {
                  return format(new Date(label), "EEE, MMM d, yyyy");
                } catch {
                  return label;
                }
              }}
              contentStyle={{ backgroundColor: "#ffffff", borderRadius: "8px", border: "1px solid #e2e8f0" }}
            />
            <Legend />
            {/* Historical Spend: Solid Blue Line */}
            <Line
              type="monotone"
              dataKey="actual_expense"
              name="Historical Daily Spend"
              stroke="#2563eb"
              strokeWidth={2}
              dot={{ r: 2 }}
              activeDot={{ r: 5 }}
              connectNulls={false}
            />
            {/* Forecast Spend: Visually Distinct Dashed Indigo/Amber Line */}
            <Line
              type="monotone"
              dataKey="predicted_expense"
              name="Forecasted Spend (Model)"
              stroke="#f59e0b"
              strokeWidth={2.5}
              strokeDasharray="5 5"
              dot={{ r: 3, fill: "#f59e0b" }}
              activeDot={{ r: 6 }}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Forecast Data Table Preview */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
        <h2 className="text-base font-semibold text-slate-800 mb-2">Projected Expense Schedule</h2>
        <div className="overflow-x-auto max-h-64">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-slate-500 uppercase text-xs sticky top-0">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Forecast Date</th>
                <th className="py-2.5 px-4 font-semibold">Model</th>
                <th className="py-2.5 px-4 font-semibold text-right">Predicted Expense</th>
                <th className="py-2.5 px-4 font-semibold text-right">Projected Balance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.series
                .filter((p) => p.is_forecast)
                .map((p, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-2.5 px-4 text-slate-700 font-medium">
                      {format(new Date(p.date), "EEE, MMM d, yyyy")}
                    </td>
                    <td className="py-2.5 px-4 text-xs text-slate-500">
                      {data.is_baseline ? "7-Day Moving Avg" : "LSTM Autoregressive"}
                    </td>
                    <td className="py-2.5 px-4 text-right font-semibold text-amber-600">
                      ${p.predicted_expense?.toFixed(2)}
                    </td>
                    <td
                      className={`py-2.5 px-4 text-right font-semibold ${
                        (p.projected_balance || 0) >= 0 ? "text-slate-800" : "text-rose-600"
                      }`}
                    >
                      ${p.projected_balance?.toFixed(2)}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ForecastPage;
