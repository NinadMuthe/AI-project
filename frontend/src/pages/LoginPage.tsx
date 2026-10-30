// frontend/src/pages/LoginPage.tsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const form = new URLSearchParams();
      form.append("username", email.trim().toLowerCase());
      form.append("password", password);
      const resp = await api.post("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      localStorage.setItem("access_token", resp.data.access_token);
      navigate("/dashboard");
    } catch (e: any) {
      setError(e.response?.data?.detail || "Authentication failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-100 p-4 font-sans">
      <div className="bg-white rounded-xl shadow-md border border-slate-200 p-8 w-full max-w-md">
        {/* Brand header */}
        <div className="flex items-center justify-center space-x-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold text-xl shadow-sm">
            FP
          </div>
          <span className="text-2xl font-bold text-slate-800">FinPulse AI</span>
        </div>

        <h2 className="text-xl font-bold text-slate-800 text-center mb-1">Welcome back</h2>
        <p className="text-sm text-slate-500 text-center mb-6">
          Sign in to access your financial overview & ML forecasts
        </p>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-md text-sm mb-5">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Email Address
            </label>
            <input
              type="email"
              placeholder="you@domain.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Password
            </label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white font-medium py-2.5 px-4 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors shadow-sm"
          >
            {loading ? "Authenticating..." : "Sign In"}
          </button>
        </form>

        <div className="mt-6 pt-5 border-t border-slate-100 text-center text-sm text-slate-500">
          Don't have an account?{" "}
          <Link to="/register" className="font-semibold text-indigo-600 hover:text-indigo-800">
            Create account
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
