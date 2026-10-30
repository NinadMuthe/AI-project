// frontend/src/types/transaction.d.ts
export interface TransactionBase {
  amount: number;
  transaction_type: "income" | "expense";
  category: string;
  merchant?: string | null;
  description?: string | null;
  transaction_date: string; // ISO string
  source?: string | null;
}

export interface TransactionCreate extends TransactionBase {}

export interface TransactionUpdate {
  amount?: number;
  transaction_type?: "income" | "expense";
  category?: string;
  merchant?: string | null;
  description?: string | null;
  transaction_date?: string;
  source?: string | null;
}

export interface TransactionRead extends TransactionBase {
  id: number;
  user_id: number;
}

