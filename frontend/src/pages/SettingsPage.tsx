// frontend/src/pages/SettingsPage.tsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

export default function SettingsPage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<{ full_name: string; email: string } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/auth/me")
      .then((res) => setProfile(res.data))
      .catch(() => setError("Could not load your account details."));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login");
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Account & Preferences</h1>
        <p className="text-sm text-slate-500">Your profile information and default currency settings</p>
      </div>

      <div className="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
        <div>
          <h2 className="text-base font-semibold text-slate-800 border-b border-slate-100 pb-2">
            User Profile
          </h2>
          {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}
          {!profile && !error && <p className="mt-3 text-sm text-slate-400">Loading details...</p>}
          {profile && (
            <dl className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <dt className="text-xs font-semibold uppercase text-slate-400">Full Name</dt>
                <dd className="mt-1 font-semibold text-slate-800">{profile.full_name}</dd>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <dt className="text-xs font-semibold uppercase text-slate-400">Email Address</dt>
                <dd className="mt-1 font-semibold text-slate-800">{profile.email}</dd>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <dt className="text-xs font-semibold uppercase text-slate-400">Currency</dt>
                <dd className="mt-1 font-semibold text-emerald-700">INR (₹) &bull; en-IN</dd>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <dt className="text-xs font-semibold uppercase text-slate-400">Timezone</dt>
                <dd className="mt-1 font-semibold text-slate-800">Asia/Kolkata (IST)</dd>
              </div>
            </dl>
          )}
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          <p className="text-xs text-slate-400">
            Bank data is pre-connected automatically via Plaid Sandbox.
          </p>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
