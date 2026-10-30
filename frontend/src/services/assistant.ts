// frontend/src/services/assistant.ts
import api from "./api";

export interface AssistantChatResponse {
  response: string;
  context_used: {
    balance: number;
    current_month_income: number;
    current_month_expense: number;
    monthly_savings: number;
    top_categories: Array<{ category: string; total: number }>;
    recent_transactions: Array<any>;
    unreviewed_anomalies: Array<any>;
    anomaly_count: number;
  };
}

export const sendAssistantMessage = async (message: string): Promise<AssistantChatResponse> => {
  const resp = await api.post<AssistantChatResponse>("/assistant/chat", { message });
  return resp.data;
};
