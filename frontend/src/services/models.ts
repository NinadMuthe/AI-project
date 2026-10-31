// frontend/src/services/models.ts
import api from "./api";

export interface ModelDetail {
  state: "not_enough_data" | "training" | "ready" | "failed";
  last_trained_at: string | null;
  records_used: number;
  message?: string;
}

export interface ModelsStatusResponse {
  lstm: ModelDetail;
  isolation_forest: ModelDetail;
}

export const fetchModelsStatus = async (): Promise<ModelsStatusResponse> => {
  const resp = await api.get<ModelsStatusResponse>("/models/status");
  return resp.data;
};

