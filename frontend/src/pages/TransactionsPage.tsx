// frontend/src/pages/TransactionsPage.tsx
import React, { useEffect, useState, useRef } from "react";
import EditTransactionModal from "../components/EditTransactionModal";
import {
  fetchTransactions,
  createTransaction,
  deleteTransaction,
} from "../services/transaction";
import { TransactionRead, TransactionCreate } from "../types/transaction";
import { formatINR, formatDateIN, INDIAN_CATEGORIES, PAYMENT_MODES } from "../utils/format";

const TransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<TransactionRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const prevCountRef = useRef<number | null>(null);

  // New transaction form state
  const [newTx, setNewTx] = useState<TransactionCreate>({
    amount: 0,
    currency: "INR",
    transaction_type: "expense",
    category: "Food & Dining",
    merchant: "",
    description: "",
    transaction_date: new Date().toISOString().slice(0, 10),
    payment_mode: "UPI",
    source: "manual",
  });

  const [editingTx, setEditingTx] = useState<TransactionRead | null>(null);
  const [isAdding, setIsAdding] = useState(false);

  // Filters & Search
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const loadData = async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const data = await fetchTransactions({
        ...(search ? { search } : {}),
        ...(typeFilter ? { transaction_type: typeFilter } : {}),
        ...(categoryFilter ? { category: categoryFilter } : {}),
      });
      setTransactions(data);

      if (prevCountRef.current !== null && data.length > prevCountRef.current) {
        const diff = data.length - prevCountRef.current;
        setToastMessage(`${diff} new transaction${diff > 1 ? "s" : ""} added!`);
        setTimeout(() => setToastMessage(null), 5000);
      }
      prevCountRef.current = data.length;
    } catch (e: any) {
      if (!silent) {
        setError(e.response?.data?.detail || e.message || "Failed to load transactions");
      }
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadData(true);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newTx.amount <= 0) {
      setError("Amount must be greater than zero.");
      return;
    }
    const today = new Date().toISOString().slice(0, 10);
    if (newTx.transaction_date > today) {
      setError("Transaction date cannot be in the future.");
      return;
    }
    try {
      const created = await createTransaction({
        ...newTx,
        source: "manual",
      });
      setTransactions((prev) => [created, ...prev]);
      setNewTx({
        amount: 0,
        currency: "INR",
        transaction_type: "expense",
        category: "Food & Dining",
        merchant: "",
        description: "",
        transaction_date: today,
        payment_mode: "UPI",
        source: "manual",
      });
      setIsAdding(false);
      setBanner("Transaction added successfully.");
      setTimeout(() => setBanner(null), 4000);
    } catch (e: any) {
      setError(e.response?.data?.detail || e.message || "Failed to add transaction");
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this transaction?")) return;
    try {
      await deleteTransaction(id);
      setTransactions((prev) => prev.filter((t) => t.id !== id));
      setBanner(`Transaction #${id} deleted.`);
      setTimeout(() => setBanner(null), 4000);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Delete failed");
    }
  };

  const getSourceBadge = (source?: string | null) => {
    const s = (source || "manual").toLowerCase();
    if (s.includes("bank") || s.includes("plaid")) {
      return (
        <span className="text-[11px] px-2 py-0.5 rounded font-medium bg-blue-50 text-blue-700 border border-blue-200">
          Bank
        </span>
      );
    }
    if (s.includes("ocr") || s.includes("receipt")) {
      return (
        <span className="text-[11px] px-2 py-0.5 rounded font-medium bg-purple-50 text-purple-700 border border-purple-200">
          Receipt
        </span>
      );
    }
    return (
      <span className="text-[11px] px-2 py-0.5 rounded font-medium bg-amber-50 text-amber-700 border border-amber-200">
        Manual
      </span>
    );
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed top-5 right-5 z-50 bg-emerald-700 text-white px-4 py-3 rounded-lg shadow-lg flex items-center space-x-2 border border-emerald-500">
          <span>🔔</span>
          <span className="text-sm font-medium">{toastMessage}</span>
        </div>
      )}

      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <span>Daily Transactions Ledger</span>
            <span className="text-xs font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
              INR (₹)
            </span>
          </h1>
          <p className="text-sm text-slate-500">
            Recorded daily expenses across Bank, Receipt OCR, and Manual entries
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsAdding(!isAdding)}
            className="inline-flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-xs transition-colors"
          >
            {isAdding ? "Cancel" : "+ Add Transaction"}
          </button>
        </div>
      </div>

      {/* Banners */}
      {banner && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-md text-sm flex items-center justify-between">
          <span>{banner}</span>
          <button onClick={() => setBanner(null)} className="ml-4 font-bold text-lg leading-none">
            &times;
          </button>
        </div>
      )}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-md text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-4 font-bold text-lg leading-none">
            &times;
          </button>
        </div>
      )}

      {/* Manual Entry Form */}
      {isAdding && (
        <form
          onSubmit={handleAdd}
          className="p-5 bg-white rounded-lg shadow-sm border border-emerald-200 space-y-4 animate-fade-in"
        >
          <h3 className="text-base font-semibold text-slate-800 border-b border-slate-100 pb-2">
            Record Manual Transaction
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                placeholder="250.00"
                value={newTx.amount || ""}
                onChange={(e) => setNewTx({ ...newTx, amount: parseFloat(e.target.value) || 0 })}
                required
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Type</label>
              <select
                value={newTx.transaction_type}
                onChange={(e) => setNewTx({ ...newTx, transaction_type: e.target.value as any })}
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm bg-white"
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Category</label>
              <select
                value={newTx.category}
                onChange={(e) => setNewTx({ ...newTx, category: e.target.value })}
                required
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm bg-white"
              >
                {INDIAN_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Payment Mode</label>
              <select
                value={newTx.payment_mode || "UPI"}
                onChange={(e) => setNewTx({ ...newTx, payment_mode: e.target.value })}
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm bg-white"
              >
                {PAYMENT_MODES.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Merchant / Store</label>
              <input
                type="text"
                placeholder="e.g. Swiggy, DMart, Tea Stall"
                value={newTx.merchant ?? ""}
                onChange={(e) => setNewTx({ ...newTx, merchant: e.target.value })}
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Date</label>
              <input
                type="date"
                value={newTx.transaction_date}
                onChange={(e) => setNewTx({ ...newTx, transaction_date: e.target.value })}
                required
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"
              />
            </div>

            <div className="sm:col-span-2 md:col-span-3">
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Description</label>
              <input
                type="text"
                placeholder="e.g. Lunch with team / weekly grocery refill"
                value={newTx.description ?? ""}
                onChange={(e) => setNewTx({ ...newTx, description: e.target.value })}
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="px-4 py-2 border rounded-lg text-sm text-slate-600 hover:bg-slate-50 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
            >
              Save Transaction
            </button>
          </div>
        </form>
      )}

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2 flex-1">
          <input
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm w-full sm:w-56"
            placeholder="Search merchant, ref..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm bg-white"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">All Types</option>
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
          <select
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm bg-white"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">All Categories</option>
            {INDIAN_CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => loadData()}
            className="px-4 py-1.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
          >
            Filter
          </button>
          {(search || typeFilter || categoryFilter) && (
            <button
              type="button"
              onClick={() => {
                setSearch("");
                setTypeFilter("");
                setCategoryFilter("");
                fetchTransactions({}).then(setTransactions);
              }}
              className="px-2 py-1.5 text-slate-500 hover:text-slate-800 text-xs"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-slate-800">
            Ledger Entries ({transactions.length})
          </h2>
        </div>

        {loading ? (
          <div className="py-16 flex justify-center items-center text-slate-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mr-3"></div>
            Loading transactions...
          </div>
        ) : transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-500 uppercase text-[11px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Date</th>
                  <th className="py-2.5 px-4 font-semibold">Type</th>
                  <th className="py-2.5 px-4 font-semibold">Category</th>
                  <th className="py-2.5 px-4 font-semibold">Merchant & Details</th>
                  <th className="py-2.5 px-4 font-semibold">Mode</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Source</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                      {formatDateIN(tx.transaction_date)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium capitalize ${
                          tx.transaction_type === "income"
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-rose-100 text-rose-800"
                        }`}
                      >
                        {tx.transaction_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-700 font-medium whitespace-nowrap">
                      {tx.category}
                    </td>
                    <td className="py-3 px-4 max-w-xs">
                      <div className="font-medium text-slate-800">{tx.merchant || "-"}</div>
                      {tx.description && <div className="text-xs text-slate-400 truncate">{tx.description}</div>}
                      {tx.is_anomaly && (
                        <span className="inline-block mt-0.5 text-[10px] bg-amber-100 text-amber-800 font-semibold px-1.5 py-0.2 rounded">
                          Unusual
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700">
                        {tx.payment_mode || "UPI"}
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
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      {getSourceBadge(tx.source)}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap space-x-2">
                      <button
                        onClick={() => setEditingTx(tx)}
                        className="text-xs text-emerald-600 hover:text-emerald-800 font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(tx.id)}
                        className="text-xs text-rose-600 hover:text-rose-800 font-medium ml-2"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-400 text-sm">
            <p>No transactions found matching your criteria.</p>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editingTx && (
        <EditTransactionModal
          transaction={editingTx}
          onClose={() => setEditingTx(null)}
          onUpdated={(updated) => {
            setTransactions((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
            setEditingTx(null);
            setBanner(`Transaction #${updated.id} updated.`);
            setTimeout(() => setBanner(null), 4000);
          }}
        />
      )}
    </div>
  );
};

export default TransactionsPage;
