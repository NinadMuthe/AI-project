// frontend/src/services/dashboard.ts
import api from "./api";
import { DashboardSummary } from "../types/dashboard";

export const fetchDashboardSummary = async (): Promise<DashboardSummary> => {
  const resp = await api.get<DashboardSummary>("/dashboard/summary");
  return resp.data;
};

