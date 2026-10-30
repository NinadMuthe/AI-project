// frontend/src/services/ocr.ts
import api from "./api";

export interface OcrScanResult {
  raw_text: string;
  amount: number | null;
  merchant: string;
  date: string | null;
  category: string;
  transaction_type: "expense";
}

export const scanReceiptImage = async (file: File): Promise<OcrScanResult> => {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await api.post<OcrScanResult>("/ocr/scan", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return resp.data;
};
