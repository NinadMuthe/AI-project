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
  merchant?: string | null;
  description?: string | null;
  transaction_date: string;
  source: string;
  payment_mode: string;
  is_anomaly: boolean;
  anomaly_reason?: string | null;
}

export interface MonthlyCashFlow {
  month: string;
  income: number;
  expenses: number;
}

export interface DailySpend {
  date: string;
  amount: number;
}

export interface DashboardSummary {
  total_balance: number;
  total_income: number;
  total_expenses: number;
  monthly_income: number;
  monthly_expenses: number;
  monthly_savings: number;
  today_spend: number;
  recent_transactions: RecentTransaction[];
  expense_by_category: CategoryExpense[];
  monthly_cash_flow: MonthlyCashFlow[];
  daily_spending_trend: DailySpend[];
  unreviewed_anomalies_count: number;
  bank_name?: string;
  bank_account_number?: string;
  bank_demo_notice: string;
}
