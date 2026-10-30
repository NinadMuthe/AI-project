// frontend/src/pages/BankConnectionPage.tsx
import React, { useEffect, useState } from "react";
import {
  fetchPlaidStatus,
  connectSandboxBank,
  syncPlaid,
  simulatePurchase,
  PlaidStatus,
} from "../services/plaid";
import { format } from "date-fns";

const BankConnectionPage: React.FC = () => {
  const [status, setStatus] = useState<PlaidStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [banner, setBanner] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadStatus = async () => {
    try {
      const res = await fetchPlaidStatus();
      setStatus(res);
    } catch (err: any) {
      console.error("Failed to load Plaid status:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    // Auto-refresh bank connection status periodically
    const timer = setInterval(loadStatus, 30000);
    return () => clearInterval(timer);
  }, []);

  const handleConnect = async () => {
    setActionLoading("connect");
    setBanner(null);
    try {
      const res = await connectSandboxBank();
      setBanner({ type: "success", text: res.message });
      await loadStatus();
    } catch (err: any) {
      setBanner({
        type: "error",
        text: err.response?.data?.detail || "Failed to connect sandbox bank account.",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleSync = async () => {
    setActionLoading("sync");
    setBanner(null);
    try {
      const res = await syncPlaid();
      setBanner({ type: "success", text: res.message });
      await loadStatus();
    } catch (err: any) {
      setBanner({
        type: "error",
        text: err.response?.data?.detail || "Manual synchronization failed.",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleSimulate = async () => {
    setActionLoading("simulate");
    setBanner(null);
    try {
      const res = await simulatePurchase();
      setBanner({ type: "success", text: res.message });
      await loadStatus();
    } catch (err: any) {
      setBanner({
        type: "error",
        text: err.response?.data?.detail || "Failed to simulate transaction.",
      });
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-800">Bank Connection</h1>
            <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
              Sandbox test data
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Connect and synchronize financial accounts using the Plaid Sandbox API
          </p>
        </div>
      </div>

      {/* Banner */}
      {banner && (
        <div
          className={`p-4 rounded-lg text-sm flex items-center justify-between ${
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

      {/* Main Connection Status Card */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-6">
        <div className="flex items-center justify-between border-b pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-2xl">
              🏦
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800">
                {status?.institution_name || "Plaid Sandbox Banking"}
              </h2>
              <p className="text-xs text-slate-500">
                Official Plaid Sandbox Environment (ins_109508)
              </p>
            </div>
          </div>

          <div>
            {loading ? (
              <span className="text-xs text-slate-400">Checking status...</span>
            ) : status?.connected ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-200">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-300">
                <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                Not Connected
              </span>
            )}
          </div>
        </div>

        {/* Sync Info Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-xs font-semibold uppercase text-slate-500">Institution</span>
            <p className="text-sm font-semibold text-slate-800 mt-1">
              {status?.institution_name || "None connected"}
            </p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-xs font-semibold uppercase text-slate-500">Last Synced</span>
            <p className="text-sm font-semibold text-slate-800 mt-1">
              {status?.last_synced_at
                ? format(new Date(status.last_synced_at), "MMM d, yyyy HH:mm:ss")
                : "Never"}
            </p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
            <span className="text-xs font-semibold uppercase text-slate-500">Auto-Sync Schedule</span>
            <p className="text-sm font-semibold text-indigo-600 mt-1">Every 2 minutes</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-wrap gap-3">
          {!status?.connected ? (
            <button
              onClick={handleConnect}
              disabled={actionLoading !== null}
              className="inline-flex items-center px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
            >
              {actionLoading === "connect" ? "Connecting Sandbox Bank..." : "Connect Sandbox Bank"}
            </button>
          ) : (
            <>
              <button
                onClick={handleSync}
                disabled={actionLoading !== null}
                className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
              >
                {actionLoading === "sync" ? "Syncing Transactions..." : "Sync Now"}
              </button>
              <button
                onClick={handleSimulate}
                disabled={actionLoading !== null}
                className="inline-flex items-center px-4 py-2 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
              >
                {actionLoading === "simulate" ? "Simulating..." : "Simulate a Purchase"}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Educational notice */}
      <div className="bg-indigo-50/60 border border-indigo-100 rounded-lg p-5 text-xs text-slate-600 space-y-2">
        <div className="font-semibold text-indigo-900 flex items-center gap-1.5">
          <span>ℹ️</span> How Sandbox Integration Works
        </div>
        <p>
          In Sandbox mode, simulated banking records are generated using Plaid's official test credentials. 
          When transactions are synced, expenses and income are automatically ledgered, categorized, and scored by our 
          Isolation Forest anomaly engine.
        </p>
      </div>
    </div>
  );
};

export default BankConnectionPage;
