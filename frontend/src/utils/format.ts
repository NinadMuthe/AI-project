// frontend/src/utils/format.ts

export const INDIAN_CATEGORIES = [
  "Food & Dining",
  "Groceries",
  "Transport",
  "Bills & Utilities",
  "Rent",
  "Shopping",
  "Entertainment",
  "Subscriptions",
  "Health",
  "Investments",
  "Education",
  "Income",
  "Others",
];

export const PAYMENT_MODES = [
  "UPI",
  "Card",
  "Net Banking",
  "Cash",
  "Auto-debit",
];

export function formatINR(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return "₹0.00";
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDateIN(dateStr: string | Date | null | undefined): string {
  if (!dateStr) return "-";
  try {
    const d = typeof dateStr === "string" ? new Date(dateStr) : dateStr;
    if (isNaN(d.getTime())) return String(dateStr);
    const day = String(d.getDate()).padStart(2, "0");
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  } catch {
    return String(dateStr);
  }
}

