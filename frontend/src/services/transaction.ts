// frontend/src/services/transaction.ts
import api from "./api";
import { TransactionCreate, TransactionRead, TransactionUpdate } from "../types/transaction";

export const fetchTransactions = async (params: Record<string, string> = {}) => {
  const resp = await api.get<TransactionRead[]>("/transactions", { params });
  return resp.data;
};

export const createTransaction = async (data: TransactionCreate) => {
  const resp = await api.post<TransactionRead>("/transactions/", data);
  return resp.data;
};

export const updateTransaction = async (id: number, data: TransactionUpdate) => {
  const resp = await api.put<TransactionRead>(`/transactions/${id}`, data);
  return resp.data;
};

export const deleteTransaction = async (id: number) => {
  await api.delete(`/transactions/${id}`);
};
