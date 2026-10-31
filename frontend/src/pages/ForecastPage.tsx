// frontend/src/pages/ForecastPage.tsx
import React, { useEffect, useState } from "react";
import { fetchForecast, ForecastResponse } from "../services/forecast";
import { fetchModelsStatus, ModelDetail } from "../services/models";
import { formatINR, formatDateIN } from "../utils/format";
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

const ForecastPage: React.FC = () => {
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [modelStatus, setModelStatus] = useState<ModelDetail | null>(null);
  const [horizon, setHorizon] = useState<number>(30);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadForecast = async (h: number) => {
    try {
      setLoading(true);
      setError(null);
      const [res, statusRes] = await Promise.all([
        fetchForecast(h),
        fetchModelsStatus().catch(() => null),
      ]);
      setData(res);
      if (statusRes?.lstm) {
        setModelStatus(statusRes.lstm);
      }
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
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600"></div>
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
    <div className="space-y-6 pb-12">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <span>Expense & Cash Flow Forecast</span>
              <span className="text-xs font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
                INR (₹)
              </span>
            </h1>
            {data.is_baseline ? (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
                BASELINE PROJECTION
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                PyTorch LSTM Neural Network
              </span>
            )}
            {modelStatus && (
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                  modelStatus.state === "ready"
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : modelStatus.state === "training"
                    ? "bg-blue-50 text-blue-700 border-blue-200"
                    : "bg-slate-100 text-slate-600 border-slate-300"
                }`}
              >
                Model: {modelStatus.state} ({modelStatus.records_used} records)
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {data.message || data.model_used} &bull; Projections are statistical estimates, not guarantees.
          </p>
        </div>

        {/* Horizon selector */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-slate-700">Horizon:</label>
          <select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value={15}>Next 15 Days</option>
            <option value={30}>Next 30 Days</option>
            <option value={45}>Next 45 Days</option>
          </select>
        </div>
      </div>

      {/* Baseline notice if under threshold */}
      {data.is_baseline && (
        <div className="bg-amber-50 border border-amber-200 text-amber-900 px-4 py-3 rounded-lg text-sm">
          <strong>Notice:</strong> Account requires 60+ days of history to activate the neural PyTorch LSTM model.
          Displaying moving-average baseline projection (estimate only, not guaranteed).
        </div>
      )}

      {/* Shortage Warning Banner */}
      {data.shortage_flag && (
        <div className="bg-rose-50 border-l-4 border-rose-500 p-4 rounded-r-lg shadow-xs">
          <div className="flex items-start">
            <div className="flex-shrink-0 text-rose-500 font-bold text-xl mr-3">⚠️</div>
            <div>
              <h3 className="text-sm font-bold text-rose-800">Potential Month-End Shortage Warning</h3>
              <p className="text-sm text-rose-700 mt-1">{data.shortage_warning}</p>
            </div>
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Current Balance</span>
          <div className="mt-1 text-2xl font-bold text-slate-900">{formatINR(data.current_balance)}</div>
          <span className="text-xs text-slate-400">Verified live ledger balance</span>
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
            {formatINR(data.projected_end_balance)}
          </div>
          <span className="text-xs text-slate-400">Estimated end-of-window balance</span>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Cash Flow Risk</span>
          <div
            className={`mt-1 text-2xl font-bold ${data.shortage_flag ? "text-rose-600" : "text-emerald-600"}`}
          >
            {data.shortage_flag ? "Shortage Risk" : "Stable Buffer"}
          </div>
          <span className="text-xs text-slate-400">
            {data.shortage_flag ? `Onset: ${formatDateIN(data.shortage_date)}` : "No deficit projected"}
          </span>
        </div>
      </div>

      {/* Recharts Forecast Chart */}
      <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
        <div className="mb-4">
          <h2 className="text-base font-semibold text-slate-800">Historical Actuals vs Forecasted Daily Expenses</h2>
          <p className="text-xs text-slate-500">
            Solid line shows actual past expenses; dashed line shows future model estimates.
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
              tickFormatter={(d) => formatDateIN(d)}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => `₹${Number(v) >= 1000 ? `${(Number(v) / 1000).toFixed(0)}k` : v}`}
            />
            <Tooltip
              formatter={(value: any, name: string) => {
                if (value === null || value === undefined) return ["-", name];
                return [formatINR(Number(value)), name];
              }}
              labelFormatter={(label) => formatDateIN(label)}
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
            {/* Forecast Spend: Visually Distinct Dashed Amber Line */}
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
                      {formatDateIN(p.date)}
                    </td>
                    <td className="py-2.5 px-4 text-xs text-slate-500">
                      {data.is_baseline ? "7-Day Moving Avg" : "LSTM Neural Network"}
                    </td>
                    <td className="py-2.5 px-4 text-right font-semibold text-amber-600">
                      {formatINR(p.predicted_expense)}
                    </td>
                    <td
                      className={`py-2.5 px-4 text-right font-semibold ${
                        (p.projected_balance || 0) >= 0 ? "text-slate-800" : "text-rose-600"
                      }`}
                    >
                      {formatINR(p.projected_balance)}
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
