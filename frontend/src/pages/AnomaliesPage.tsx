// frontend/src/pages/AnomaliesPage.tsx
import React, { useEffect, useState } from "react";
import {
  fetchAnomalies,
  runAnomalyDetection,
  markAnomalyReviewed,
  AnomalyTransaction,
} from "../services/anomaly";
import { fetchModelsStatus, ModelDetail } from "../services/models";
import { format } from "date-fns";

const AnomaliesPage: React.FC = () => {
  const [anomalies, setAnomalies] = useState<AnomalyTransaction[]>([]);
  const [modelStatus, setModelStatus] = useState<ModelDetail | null>(null);
  const [filterUnreviewedOnly, setFilterUnreviewedOnly] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [detecting, setDetecting] = useState<boolean>(false);
  const [banner, setBanner] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [data, statusRes] = await Promise.all([
        fetchAnomalies(!filterUnreviewedOnly),
        fetchModelsStatus().catch(() => null),
      ]);
      setAnomalies(data);
      if (statusRes?.isolation_forest) {
        setModelStatus(statusRes.isolation_forest);
      }
    } catch (e: any) {
      setBanner({
        text: e.response?.data?.detail || e.message || "Failed to load anomaly records",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterUnreviewedOnly]);

  const handleRunDetection = async () => {
    try {
      setDetecting(true);
      setBanner(null);
      const result = await runAnomalyDetection();
      setBanner({
        text: result.message,
        type: "success",
      });
      await loadData();
    } catch (e: any) {
      setBanner({
        text: e.response?.data?.detail || "Failed to execute anomaly detection",
        type: "error",
      });
    } finally {
      setDetecting(false);
    }
  };

  const handleMarkReviewed = async (id: number) => {
    try {
      const updated = await markAnomalyReviewed(id);
      setAnomalies((prev) => prev.map((tx) => (tx.id === id ? updated : tx)));
      setBanner({
        text: `Transaction #${id} marked as reviewed.`,
        type: "success",
      });
    } catch (e: any) {
      setBanner({
        text: e.response?.data?.detail || "Could not mark transaction as reviewed",
        type: "error",
      });
    }
  };

  const displayedAnomalies = filterUnreviewedOnly
    ? anomalies.filter((a) => !a.is_reviewed)
    : anomalies;

  const totalFlagged = anomalies.length;
  const pendingReview = anomalies.filter((a) => !a.is_reviewed).length;
  const clearedCount = anomalies.filter((a) => a.is_reviewed).length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-800">Unusual Spending Activity</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
              Isolation Forest ML
            </span>
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
            Machine learning engine identifies suspicious spending amounts, velocity anomalies, and category outliers.
          </p>
        </div>

        <button
          onClick={handleRunDetection}
          disabled={detecting}
          className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-md shadow-sm disabled:opacity-50"
        >
          {detecting ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
              </svg>
              Running Isolation Forest...
            </>
          ) : (
            "Run Anomaly Check Now"
          )}
        </button>
      </div>

      {/* Banner */}
      {banner && (
        <div
          className={`p-4 rounded-md text-sm flex items-center justify-between ${
            banner.type === "success"
              ? "bg-emerald-50 border border-emerald-200 text-emerald-800"
              : "bg-rose-50 border border-rose-200 text-rose-800"
          }`}
        >
          <span>{banner.text}</span>
          <button onClick={() => setBanner(null)} className="font-bold text-lg leading-none ml-4">
            &times;
          </button>
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Flagged</span>
          <div className="mt-1 text-2xl font-bold text-slate-800">{totalFlagged}</div>
          <span className="text-xs text-slate-400">Total unusual entries detected</span>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Pending Review</span>
          <div className="mt-1 text-2xl font-bold text-amber-600">{pendingReview}</div>
          <span className="text-xs text-slate-400">Transactions requiring attention</span>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Reviewed</span>
          <div className="mt-1 text-2xl font-bold text-emerald-600">{clearedCount}</div>
          <span className="text-xs text-slate-400">Confirmed by account holder</span>
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h2 className="text-base font-semibold text-slate-800">
            Detected Outliers ({displayedAnomalies.length})
          </h2>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="unreviewed-only"
              checked={filterUnreviewedOnly}
              onChange={(e) => setFilterUnreviewedOnly(e.target.checked)}
              className="h-4 w-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
            />
            <label htmlFor="unreviewed-only" className="text-xs font-medium text-slate-600 cursor-pointer">
              Show unreviewed only
            </label>
          </div>
        </div>

        {loading ? (
          <div className="py-12 flex justify-center items-center text-slate-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mr-3"></div>
            Loading anomaly records...
          </div>
        ) : displayedAnomalies.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Date</th>
                  <th className="py-2.5 px-4 font-semibold">Merchant & Details</th>
                  <th className="py-2.5 px-4 font-semibold">Category</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
                  <th className="py-2.5 px-4 font-semibold">Model Finding</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Score</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Status</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {displayedAnomalies.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                      {format(new Date(tx.transaction_date), "MMM d, yyyy")}
                    </td>
                    <td className="py-3 px-4 max-w-xs">
                      <div className="font-semibold text-slate-800">{tx.merchant || "-"}</div>
                      {tx.description && (
                        <div className="text-xs text-slate-400 truncate">{tx.description}</div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-700 whitespace-nowrap">{tx.category}</td>
                    <td className="py-3 px-4 text-right font-bold text-rose-600 whitespace-nowrap">
                      ${tx.amount.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-700 max-w-sm">
                      <span className="font-medium text-amber-900 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        {tx.anomaly_reason || "Unusual pattern flagged by model"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                        {tx.anomaly_score !== null && tx.anomaly_score !== undefined
                          ? (tx.anomaly_score * 100).toFixed(0) + "%"
                          : "-"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      {tx.is_reviewed ? (
                        <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-medium">
                          Reviewed
                        </span>
                      ) : (
                        <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium">
                          Pending
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      {!tx.is_reviewed && (
                        <button
                          onClick={() => handleMarkReviewed(tx.id)}
                          className="text-xs px-2.5 py-1 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium rounded shadow-xs"
                        >
                          Mark Reviewed
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-400 text-sm">
            <p>No unusual transactions found matching criteria.</p>
            <p className="text-xs mt-1">Run an anomaly check or import transactions to analyze.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnomaliesPage;
