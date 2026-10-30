// frontend/src/services/forecast.ts
import api from "./api";

export interface DailyPoint {
  date: string;
  actual_expense?: number | null;
  predicted_expense?: number | null;
  projected_balance?: number | null;
  is_forecast: boolean;
}

export interface ForecastResponse {
  model_used: string;
  is_baseline: boolean;
  message?: string | null;
  current_balance: number;
  projected_end_balance: number;
  shortage_flag: boolean;
  shortage_date?: string | null;
  shortage_amount?: number | null;
  shortage_warning?: string | null;
  series: DailyPoint[];
}

export const fetchForecast = async (horizon: number = 30): Promise<ForecastResponse> => {
  const resp = await api.get<ForecastResponse>("/forecast", { params: { horizon } });
  return resp.data;
};
