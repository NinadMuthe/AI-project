// frontend/src/pages/TransactionsPage.tsx
import React, { useEffect, useState } from "react";
import EditTransactionModal from "../components/EditTransactionModal";
import {
  fetchTransactions,
  createTransaction,
  deleteTransaction,
  loadSampleData,
} from "../services/transaction";
import { TransactionRead, TransactionCreate } from "../types/transaction";
import { format } from "date-fns";

const TransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<TransactionRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const [loadingSample, setLoadingSample] = useState(false);

  // New transaction form state
  const [newTx, setNewTx] = useState<TransactionCreate>({
    amount: 0,
    transaction_type: "expense",
    category: "",
    merchant: "",
    description: "",
    transaction_date: new Date().toISOString().slice(0, 10),
    source: "manual",
  });

  const [editingTx, setEditingTx] = useState<TransactionRead | null>(null);

  // Filters & Search
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [isAdding, setIsAdding] = useState(false);

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
    // Auto-refresh transaction list every 30 seconds for live bank sync updates
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
    try {
      const created = await createTransaction({
        ...newTx,
        source: "manual",
      });
      setTransactions((prev) => [created, ...prev]);
      setNewTx({
        amount: 0,
        transaction_type: "expense",
        category: "",
        merchant: "",
        description: "",
        transaction_date: new Date().toISOString().slice(0, 10),
        source: "manual",
      });
      setIsAdding(false);
      setBanner("Transaction added successfully.");
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
    } catch (e: any) {
      setError(e.response?.data?.detail || "Delete failed");
    }
  };

  const handleLoadSample = async () => {
    setLoadingSample(true);
    setError(null);
    setBanner(null);
    try {
      const result = await loadSampleData();
      setBanner(result.message);
      await loadData();
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to load sample data.");
    } finally {
      setLoadingSample(false);
    }
  };

  const getSourceBadge = (source?: string | null) => {
    switch (source) {
      case "plaid_sandbox":
        return (
          <span className="text-[11px] px-2 py-0.5 rounded font-medium bg-amber-50 text-amber-700 border border-amber-200">
            Plaid sandbox
          </span>
        );
      case "receipt_ocr":
        return (
          <span className="text-[11px] px-2 py-0.5 rounded font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
            Receipt OCR
          </span>
        );
      case "sample_data":
        return (
          <span className="text-[11px] px-2 py-0.5 rounded font-medium bg-sky-50 text-sky-700 border border-sky-200">
            Sample data
          </span>
        );
      default:
        return (
          <span className="text-[11px] px-2 py-0.5 rounded font-medium bg-slate-100 text-slate-600 border border-slate-200">
            Manual
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Transactions Ledger</h1>
          <p className="text-sm text-slate-500">
            Real-time financial activity with automated categorization and ML audit
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsAdding(!isAdding)}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-md shadow-sm transition-colors"
          >
            {isAdding ? "Cancel" : "+ Add Transaction"}
          </button>
          <button
            onClick={handleLoadSample}
            disabled={loadingSample}
            className="inline-flex items-center px-4 py-2 border border-slate-300 text-slate-700 bg-white hover:bg-slate-50 text-sm font-medium rounded-md shadow-sm disabled:opacity-50"
          >
            {loadingSample ? "Generating 6-Month Data..." : "Load Sample Data"}
          </button>
        </div>
      </div>

      {/* Banner / Alerts */}
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

      {/* Add Transaction Accordion Form */}
      {isAdding && (
        <form
          onSubmit={handleAdd}
          className="p-5 bg-white rounded-lg shadow-sm border border-indigo-100 space-y-4"
        >
          <h3 className="text-base font-semibold text-slate-800 border-b pb-2">Record New Transaction</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Amount ($)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                placeholder="45.00"
                value={newTx.amount || ""}
                onChange={(e) => setNewTx({ ...newTx, amount: parseFloat(e.target.value) || 0 })}
                required
                className="w-full p-2 border border-slate-300 rounded-md text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Type</label>
              <select
                value={newTx.transaction_type}
                onChange={(e) => setNewTx({ ...newTx, transaction_type: e.target.value as any })}
                className="w-full p-2 border border-slate-300 rounded-md text-sm bg-white"
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Category</label>
              <input
                type="text"
                placeholder="e.g. Food, Salary, Transport"
                value={newTx.category}
                onChange={(e) => setNewTx({ ...newTx, category: e.target.value })}
                required
                className="w-full p-2 border border-slate-300 rounded-md text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Merchant</label>
              <input
                type="text"
                placeholder="e.g. Whole Foods"
                value={newTx.merchant ?? ""}
                onChange={(e) => setNewTx({ ...newTx, merchant: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded-md text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Description</label>
              <input
                type="text"
                placeholder="e.g. Weekly family groceries"
                value={newTx.description ?? ""}
                onChange={(e) => setNewTx({ ...newTx, description: e.target.value })}
                className="w-full p-2 border border-slate-300 rounded-md text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Date</label>
              <input
                type="date"
                value={newTx.transaction_date}
                onChange={(e) => setNewTx({ ...newTx, transaction_date: e.target.value })}
                required
                className="w-full p-2 border border-slate-300 rounded-md text-sm"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="px-4 py-2 border rounded-md text-sm text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700"
            >
              Save Transaction
            </button>
          </div>
        </form>
      )}

      {/* Filter Controls */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2 flex-1">
          <input
            className="border border-slate-300 rounded-md px-3 py-1.5 text-sm w-full sm:w-56"
            placeholder="Search merchant or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            className="border border-slate-300 rounded-md px-3 py-1.5 text-sm bg-white"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">All Types</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
          <input
            className="border border-slate-300 rounded-md px-3 py-1.5 text-sm w-full sm:w-36"
            placeholder="Category..."
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          />
          <button
            type="button"
            onClick={() => loadData()}
            className="px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700"
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
            Recorded Transactions ({transactions.length})
          </h2>
        </div>

        {loading ? (
          <div className="py-12 flex justify-center items-center text-slate-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mr-3"></div>
            Loading ledger...
          </div>
        ) : transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Date</th>
                  <th className="py-2.5 px-4 font-semibold">Type</th>
                  <th className="py-2.5 px-4 font-semibold">Category</th>
                  <th className="py-2.5 px-4 font-semibold">Merchant & Details</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Source</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                      {format(new Date(tx.transaction_date), "MMM d, yyyy")}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
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
                    <td className="py-3 px-4 text-slate-700 font-medium whitespace-nowrap">
                      {tx.category}
                    </td>
                    <td className="py-3 px-4 max-w-xs">
                      <div className="font-medium text-slate-800">{tx.merchant || "-"}</div>
                      {tx.description && <div className="text-xs text-slate-400 truncate">{tx.description}</div>}
                    </td>
                    <td
                      className={`py-3 px-4 text-right font-semibold whitespace-nowrap ${
                        tx.transaction_type === "income" ? "text-emerald-600" : "text-slate-800"
                      }`}
                    >
                      {tx.transaction_type === "income" ? "+" : "-"}${tx.amount.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      {getSourceBadge(tx.source)}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap space-x-2">
                      <button
                        onClick={() => setEditingTx(tx)}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
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
            <p>No transactions found matching criteria.</p>
            <p className="text-xs mt-1">Try resetting filters or click "Load Sample Data".</p>
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
          }}
        />
      )}
    </div>
  );
};

export default TransactionsPage;
