// frontend/src/types/dashboard.d.ts
export interface CategoryExpense {
  category: string;
  total: number;
}

export interface RecentTransaction {
  id: number;
  amount: number;
  transaction_type: string;
  category: string;
  transaction_date: string; // ISO
}

export interface MonthlyCashFlow {
  month: string;
  income: number;
  expenses: number;
}

export interface DashboardSummary {
  total_balance: number;
  total_income: number;
  total_expenses: number;
  monthly_savings: number;
  recent_transactions: RecentTransaction[];
  expense_by_category: CategoryExpense[];
  monthly_cash_flow: MonthlyCashFlow[];
}


