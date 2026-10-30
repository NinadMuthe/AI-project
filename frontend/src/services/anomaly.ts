// frontend/src/services/anomaly.ts
import api from "./api";

export interface AnomalyTransaction {
  id: number;
  user_id: number;
  amount: number;
  transaction_type: string;
  category: string;
  merchant?: string | null;
  description?: string | null;
  transaction_date: string;
  source: string;
  is_anomaly: boolean;
  anomaly_score?: number | null;
  anomaly_reason?: string | null;
  anomaly_detected_at?: string | null;
  is_reviewed: boolean;
}

export interface AnomalyDetectionResult {
  total_evaluated: number;
  anomalies_flagged: number;
  message: string;
  anomalies: AnomalyTransaction[];
}

export const fetchAnomalies = async (includeReviewed: boolean = true): Promise<AnomalyTransaction[]> => {
  const resp = await api.get<AnomalyTransaction[]>("/anomalies", {
    params: { include_reviewed: includeReviewed },
  });
  return resp.data;
};

export const runAnomalyDetection = async (): Promise<AnomalyDetectionResult> => {
  const resp = await api.post<AnomalyDetectionResult>("/anomalies/detect");
  return resp.data;
};

export const markAnomalyReviewed = async (txId: number): Promise<AnomalyTransaction> => {
  const resp = await api.post<AnomalyTransaction>(`/anomalies/${txId}/review`);
  return resp.data;
};
