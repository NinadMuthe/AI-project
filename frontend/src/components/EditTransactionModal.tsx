// frontend/src/components/EditTransactionModal.tsx
import React, { useState, useEffect } from "react";
import { TransactionRead, TransactionUpdate } from "../types/transaction";
import { updateTransaction } from "../services/transaction";

interface Props {
  transaction: TransactionRead | null;
  onClose: () => void;
  onUpdated: (tx: TransactionRead) => void;
}

const EditTransactionModal: React.FC<Props> = ({ transaction, onClose, onUpdated }) => {
  const [form, setForm] = useState<TransactionUpdate>({});

  useEffect(() => {
    if (transaction) {
      setForm({
        amount: transaction.amount,
        transaction_type: transaction.transaction_type as any,
        category: transaction.category,
        merchant: transaction.merchant ?? undefined,
        description: transaction.description ?? undefined,
        transaction_date: transaction.transaction_date.slice(0, 10),
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
    try {
      const updated = await updateTransaction(transaction.id, form);
      onUpdated(updated);
      onClose();
    } catch (err: any) {
      alert(err.message || "Update failed");
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center">
      <div className="bg-white rounded shadow p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4 text-primary">Edit Transaction</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="number"
            step="0.01"
            name="amount"
            placeholder="Amount"
            value={form.amount ?? ""}
            onChange={handleChange}
            required
            className="w-full p-2 border rounded"
          />
          <select
            name="transaction_type"
            value={form.transaction_type ?? ""}
            onChange={handleChange}
            className="w-full p-2 border rounded"
          >
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
          <input
            type="text"
            name="category"
            placeholder="Category"
            value={form.category ?? ""}
            onChange={handleChange}
            required
            className="w-full p-2 border rounded"
          />
          <input
            type="date"
            name="transaction_date"
            value={form.transaction_date ?? ""}
            onChange={handleChange}
            required
            className="w-full p-2 border rounded"
          />
          <div className="flex justify-end space-x-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 rounded bg-primary text-white hover:bg-indigo-600">
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditTransactionModal;

