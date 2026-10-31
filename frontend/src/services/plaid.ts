// frontend/src/services/plaid.ts
import api from "./api";

export interface PlaidStatus {
  connected: boolean;
  institution_name: string | null;
  last_synced_at: string | null;
  status: string | null;
}

export const fetchPlaidStatus = async (): Promise<PlaidStatus> => {
  const resp = await api.get<PlaidStatus>("/plaid/status");
  return resp.data;
};

export const connectSandboxBank = async (): Promise<{
  connected: boolean;
  institution_name: string;
  transactions_synced?: number;
  message: string;
}> => {
  const resp = await api.post("/plaid/connect-sandbox");
  return resp.data;
};

export const syncPlaid = async (): Promise<{
  synced: number;
  message: string;
}> => {
  const resp = await api.post("/plaid/sync");
  return resp.data;
};

export const syncPlaidTransactions = syncPlaid;

export const simulatePurchase = async (): Promise<{
  simulated: boolean;
  merchant?: string;
  amount?: number;
  transactions_synced: number;
  message: string;
}> => {
  const resp = await api.post("/plaid/simulate-transaction");
  return resp.data;
};

