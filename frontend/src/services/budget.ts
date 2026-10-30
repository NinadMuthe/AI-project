import api from "./api";
export interface Budget { id: number; category: string; limit_amount: number; month: string; spent: number; remaining: number; utilization: number; exceeded: boolean; }
export const fetchBudgets = (month?: string) => api.get<Budget[]>("/budgets", { params: month ? { month } : {} }).then(r => r.data);
export const saveBudget = (data: Pick<Budget, "category" | "limit_amount" | "month">) => api.post<Budget>("/budgets", data).then(r => r.data);
export const deleteBudget = (id: number) => api.delete(`/budgets/${id}`);
