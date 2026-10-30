// frontend/src/pages/RegisterPage.tsx
import React, { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";

const RegisterPage: React.FC = () => {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.post("/auth/register", {
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
      });
      // Automatically log in after registration
      const form = new URLSearchParams();
      form.append("username", email.trim().toLowerCase());
      form.append("password", password);
      const loginResp = await api.post("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      localStorage.setItem("access_token", loginResp.data.access_token);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Unable to create account. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4 font-sans">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-md">
        <div className="flex items-center justify-center space-x-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold text-xl shadow-sm">
            FP
          </div>
          <span className="text-2xl font-bold text-slate-800">FinPulse AI</span>
        </div>

        <h1 className="text-xl font-bold text-slate-800 text-center mb-1">Create an account</h1>
        <p className="text-sm text-slate-500 text-center mb-6">
          Join FinPulse AI for intelligent financial forecasting
        </p>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-md text-sm mb-5">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Full Name
            </label>
            <input
              type="text"
              placeholder="Jane Doe"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Email Address
            </label>
            <input
              type="email"
              placeholder="you@domain.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Password (min. 8 characters)
            </label>
            <input
              type="password"
              placeholder="••••••••"
              minLength={8}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white font-medium py-2.5 px-4 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors shadow-sm"
          >
            {loading ? "Creating account..." : "Register"}
          </button>
        </form>

        <div className="mt-6 pt-5 border-t border-slate-100 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-indigo-600 hover:text-indigo-800">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
