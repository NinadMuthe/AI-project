// frontend/src/pages/ReceiptScannerPage.tsx
import React, { useState } from "react";
import { scanReceiptImage, OcrScanResult } from "../services/ocr";
import { createTransaction } from "../services/transaction";
import { TransactionCreate } from "../types/transaction";

const ReceiptScannerPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [scanning, setScanning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<OcrScanResult | null>(null);
  const [showRawText, setShowRawText] = useState(false);

  // Editable form state pre-filled after scan
  const [formData, setFormData] = useState<TransactionCreate>({
    amount: 0,
    transaction_type: "expense",
    category: "Shopping",
    merchant: "",
    description: "Scanned Receipt",
    transaction_date: new Date().toISOString().slice(0, 10),
    source: "receipt_ocr",
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setError(null);
    setSuccessMsg(null);
    if (!file) return;

    if (!file.type.match(/^image\/(jpeg|jpg|png|webp)$/i)) {
      setError("Please select a valid image file (JPG, PNG, or WebP).");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("File exceeds the maximum limit of 5 MB.");
      return;
    }

    setSelectedFile(file);
  };

  const handleScan = async () => {
    if (!selectedFile) return;
    setScanning(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await scanReceiptImage(selectedFile);
      setScanResult(res);
      setFormData({
        amount: res.amount || 0,
        transaction_type: "expense",
        category: res.category || "Shopping",
        merchant: res.merchant || "",
        description: `Receipt scan - ${res.merchant || "Store"}`,
        transaction_date: res.date && res.date.length === 10 ? res.date : new Date().toISOString().slice(0, 10),
        source: "receipt_ocr",
      });
      setSuccessMsg("Receipt scanned successfully! Review the extracted fields below and click Save.");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          "Could not read receipt image. Ensure the image is clear and well-lit, then try again."
      );
    } finally {
      setScanning(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.amount <= 0) {
      setError("Please specify a valid amount greater than $0.00.");
      return;
    }
    setSaving(true);
    setError(null);

    try {
      await createTransaction({
        ...formData,
        source: "receipt_ocr",
      });
      setSuccessMsg("Transaction recorded in ledger with source 'receipt_ocr'!");
      setScanResult(null);
      setSelectedFile(null);
      setFormData({
        amount: 0,
        transaction_type: "expense",
        category: "Shopping",
        merchant: "",
        description: "",
        transaction_date: new Date().toISOString().slice(0, 10),
        source: "receipt_ocr",
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to record transaction.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Receipt OCR Scanner</h1>
        <p className="text-sm text-slate-500">
          Upload photo or scan of a paper receipt to automatically extract expense details
        </p>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-bold text-lg leading-none ml-4">
            &times;
          </button>
        </div>
      )}
      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-sm flex items-center justify-between">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="font-bold text-lg leading-none ml-4">
            &times;
          </button>
        </div>
      )}

      {/* Upload Box */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-4">
        <h2 className="text-base font-semibold text-slate-800">1. Upload Receipt Document</h2>
        <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-indigo-400 transition-colors bg-slate-50/50">
          <input
            type="file"
            id="receipt-file-input"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleFileChange}
            className="hidden"
          />
          <label htmlFor="receipt-file-input" className="cursor-pointer block space-y-2">
            <div className="text-4xl">🧾</div>
            <div className="text-sm font-medium text-slate-700">
              {selectedFile ? selectedFile.name : "Click to select or drag and drop a receipt image"}
            </div>
            <div className="text-xs text-slate-400">
              Supports JPG, PNG, and WebP up to 5 MB
            </div>
          </label>
        </div>

        {selectedFile && (
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={() => setSelectedFile(null)}
              className="px-4 py-2 border border-slate-300 rounded-md text-sm text-slate-600 hover:bg-slate-50"
            >
              Clear
            </button>
            <button
              onClick={handleScan}
              disabled={scanning}
              className="inline-flex items-center px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-md shadow-sm disabled:opacity-50"
            >
              {scanning ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                  </svg>
                  Processing OCR...
                </>
              ) : (
                "Scan with EasyOCR"
              )}
            </button>
          </div>
        )}
      </div>

      {/* Editable Form after Scan */}
      {scanResult && (
        <form
          onSubmit={handleSave}
          className="bg-white rounded-lg border border-indigo-200 shadow-sm p-6 space-y-5"
        >
          <div className="flex items-center justify-between border-b pb-3">
            <div>
              <h2 className="text-base font-semibold text-slate-800">
                2. Review & Save Scanned Transaction
              </h2>
              <p className="text-xs text-slate-500">
                Extracted via EasyOCR. Please confirm or edit the fields below before saving.
              </p>
            </div>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-indigo-100 text-indigo-700 uppercase">
              source: receipt_ocr
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                Amount ($)
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={formData.amount || ""}
                onChange={(e) =>
                  setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })
                }
                required
                className="w-full p-2.5 border border-slate-300 rounded-md text-sm font-semibold text-slate-800"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                Merchant / Store
              </label>
              <input
                type="text"
                value={formData.merchant || ""}
                onChange={(e) => setFormData({ ...formData, merchant: e.target.value })}
                required
                className="w-full p-2.5 border border-slate-300 rounded-md text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                Category
              </label>
              <input
                type="text"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                required
                className="w-full p-2.5 border border-slate-300 rounded-md text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                Transaction Date
              </label>
              <input
                type="date"
                value={formData.transaction_date}
                onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
                required
                className="w-full p-2.5 border border-slate-300 rounded-md text-sm"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                Description / Memo
              </label>
              <input
                type="text"
                value={formData.description || ""}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full p-2.5 border border-slate-300 rounded-md text-sm"
              />
            </div>
          </div>

          {/* Raw Text Accordion */}
          <div className="pt-2">
            <button
              type="button"
              onClick={() => setShowRawText(!showRawText)}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1"
            >
              <span>{showRawText ? "▼ Hide" : "▶ Show"} Raw Extracted Text</span>
            </button>
            {showRawText && (
              <pre className="mt-2 p-3 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-600 overflow-x-auto max-h-48 whitespace-pre-wrap">
                {scanResult.raw_text || "(No text recognized)"}
              </pre>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t">
            <button
              type="button"
              onClick={() => setScanResult(null)}
              className="px-4 py-2 border border-slate-300 rounded-md text-sm text-slate-600 hover:bg-slate-50"
            >
              Discard
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 shadow-sm disabled:opacity-50"
            >
              {saving ? "Saving to Ledger..." : "Save Transaction"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default ReceiptScannerPage;
