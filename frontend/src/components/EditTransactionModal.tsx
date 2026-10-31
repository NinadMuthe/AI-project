// frontend/src/components/EditTransactionModal.tsx
import React, { useState, useEffect } from "react";
import { TransactionRead, TransactionUpdate } from "../types/transaction";
import { updateTransaction } from "../services/transaction";
import { INDIAN_CATEGORIES, PAYMENT_MODES } from "../utils/format";

interface Props {
  transaction: TransactionRead | null;
  onClose: () => void;
  onUpdated: (tx: TransactionRead) => void;
}

const EditTransactionModal: React.FC<Props> = ({ transaction, onClose, onUpdated }) => {
  const [form, setForm] = useState<TransactionUpdate>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (transaction) {
      setForm({
        amount: transaction.amount,
        transaction_type: transaction.transaction_type,
        category: transaction.category,
        merchant: transaction.merchant ?? undefined,
        description: transaction.description ?? undefined,
        transaction_date: transaction.transaction_date.slice(0, 10),
        payment_mode: transaction.payment_mode || "UPI",
        source: transaction.source ?? undefined,
      });
    }
  }, [transaction]);

  if (!transaction) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: name === "amount" ? Number(value) : value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.amount || form.amount <= 0) {
      setError("Amount must be greater than zero.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const updated = await updateTransaction(transaction.id, form);
      onUpdated(updated);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Update failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 p-6 w-full max-w-lg animate-fade-in">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
          <h2 className="text-lg font-bold text-slate-800">Edit Transaction #{transaction.id}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 font-bold text-lg">
            &times;
          </button>
        </div>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 px-3 py-2 rounded text-xs mb-3">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-sm">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                name="amount"
                value={form.amount ?? ""}
                onChange={handleChange}
                required
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Type</label>
              <select
                name="transaction_type"
                value={form.transaction_type ?? "expense"}
                onChange={handleChange}
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm bg-white"
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Category</label>
              <select
                name="category"
                value={form.category ?? ""}
                onChange={handleChange}
                required
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm bg-white"
              >
                {INDIAN_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Payment Mode</label>
              <select
                name="payment_mode"
                value={form.payment_mode ?? "UPI"}
                onChange={handleChange}
                className="w-full p-2.5 border border-slate-300 rounded-lg text-sm bg-white"
              >
                {PAYMENT_MODES.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Merchant / Store</label>
            <input
              type="text"
              name="merchant"
              value={form.merchant ?? ""}
              onChange={handleChange}
              className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"
              placeholder="e.g. Swiggy, DMart, Uber"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Description</label>
            <input
              type="text"
              name="description"
              value={form.description ?? ""}
              onChange={handleChange}
              className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"
              placeholder="Details or reference"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Date</label>
            <input
              type="date"
              name="transaction_date"
              value={form.transaction_date ?? ""}
              onChange={handleChange}
              required
              className="w-full p-2.5 border border-slate-300 rounded-lg text-sm"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 font-medium disabled:opacity-50"
            >
              {saving ? "Saving..." : "Update Transaction"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditTransactionModal;
