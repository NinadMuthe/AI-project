# backend/app/services/ocr_service.py
"""
EasyOCR receipt scanning service for Indian receipts.
Lazy-loads the EasyOCR reader once on first use (singleton).
Extracts amount (₹, Rs, INR, Total, Net Payable), merchant, date, category.
Never saves the image — deletes temp file immediately after processing.
"""
import os
import re
import logging
from pathlib import Path
from typing import Optional, List
import tempfile
from datetime import datetime, date

logger = logging.getLogger(__name__)

_ocr_reader = None  # module-level singleton


def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        logger.info("Loading EasyOCR model (first use, CPU mode)...")
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
        logger.info("EasyOCR model loaded successfully.")
    return _ocr_reader


def _parse_indian_amount(lines: List[str]) -> Optional[float]:
    """
    Extract best total amount for Indian receipts.
    Prioritizes labels like: Grand Total, Net Payable, Total Amount, Total, Amount Payable.
    Ignores tax/subtotal lines like GST, CGST, SGST, Sub Total.
    """
    # 1. First pass: look specifically for total labels
    target_keywords = ["grand total", "net payable", "amount payable", "total amount", "total bill", "total", "balance due", "bill amount"]
    avoid_keywords = ["cgst", "sgst", "igst", "gst", "subtotal", "sub total", "taxable", "tax rate", "change", "item", "qty", "cash tender"]

    candidates = []

    for line in lines:
        lower_line = line.lower()
        is_avoid = any(ak in lower_line for ak in avoid_keywords)
        is_target = any(tk in lower_line for tk in target_keywords)

        # Look for numbers with optional ₹, Rs, Rs., INR
        # Matches e.g. ₹ 1,450.00, Rs. 249, INR 580.50, 1299.00
        found_nums = re.findall(r"(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)", line, re.IGNORECASE)
        for num_str in found_nums:
            clean_str = num_str.replace(",", "").strip()
            if not clean_str:
                continue
            try:
                val = float(clean_str)
                if val <= 0:
                    continue
                # Score candidate
                score = 0
                if is_target:
                    score += 10
                if any(curr in lower_line for curr in ["₹", "rs", "inr"]):
                    score += 3
                if is_avoid:
                    score -= 8
                candidates.append((score, val))
            except ValueError:
                pass

    if candidates:
        # Sort by score descending, then by value descending
        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return candidates[0][1]

    # Fallback regex search on joined text
    combined = " ".join(lines)
    matches = re.findall(r"(?:grand\s*total|net\s*payable|amount\s*payable|total)[:\s]*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)", combined, re.IGNORECASE)
    if matches:
        try:
            return float(matches[-1].replace(",", ""))
        except ValueError:
            pass

    return None


def _parse_merchant(lines: List[str]) -> str:
    """First 1-3 lines typically contain the merchant name or store name."""
    candidates = []
    for line in lines[:5]:
        line = line.strip()
        # Skip lines that are purely receipt numbers, dates, or prices
        if line and len(line) > 2 and not re.match(r"^[\d\s\.\,\$\:\-\/\#\₹]+$", line):
            # Also skip "Tax Invoice", "Cash Memo"
            if not any(skip_kw in line.lower() for skip_kw in ["tax invoice", "cash memo", "bill of supply", "gstin"]):
                candidates.append(line)
        if len(candidates) >= 2:
            break
    return " ".join(candidates[:2]) if candidates else "Store / Merchant"


def _parse_indian_date(lines: List[str]) -> str:
    """Extract date in DD/MM/YYYY, DD-MM-YYYY, or YYYY-MM-DD."""
    combined = " ".join(lines)
    patterns = [
        r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b",
        r"\b(\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2})\b",
        r"\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{2,4})\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, combined, re.IGNORECASE)
        if m:
            raw_d = m.group(1).replace(".", "/").replace("-", "/")
            parts = raw_d.split("/")
            if len(parts) == 3:
                try:
                    # If first part is 4 digits, it's YYYY/MM/DD
                    if len(parts[0]) == 4:
                        return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                    # Else it's DD/MM/YYYY
                    year = int(parts[2])
                    if year < 100:
                        year += 2000
                    return f"{year:04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"
                except Exception:
                    pass
    return date.today().isoformat()


def _map_indian_receipt_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["restaurant", "cafe", "coffee", "chai", "bakery", "kitchen", "biryani", "dhaba", "food", "dining", "swiggy", "zomato", "burger", "pizza"]):
        return "Food & Dining"
    if any(k in t for k in ["supermarket", "mart", "bazaar", "kirana", "grocer", "vegetable", "milk", "dairy", "zepto", "blinkit", "bigbasket"]):
        return "Groceries"
    if any(k in t for k in ["fuel", "petrol", "diesel", "hpcl", "bpcl", "ioc", "uber", "ola", "transport", "travel"]):
        return "Transport"
    if any(k in t for k in ["pharmacy", "medical", "chemist", "clinic", "hospital", "apollo", "1mg", "medplus", "netmeds", "dr."]):
        return "Health"
    if any(k in t for k in ["fashion", "retail", "clothing", "apparel", "shoes", "trends", "zara", "pantaloons", "max", "h&m"]):
        return "Shopping"
    if any(k in t for k in ["cinema", "theatre", "pvr", "inox", "entertainment", "game"]):
        return "Entertainment"
    if any(k in t for k in ["books", "stationery", "school", "college", "institute", "course"]):
        return "Education"
    if any(k in t for k in ["bescom", "electric", "power", "water", "gas", "telecom", "broadband"]):
        return "Bills & Utilities"
    return "Food & Dining"


async def scan_receipt(image_bytes: bytes, filename: str) -> dict:
    """Run EasyOCR on image bytes. Returns parsed fields. Does NOT save to DB."""
    suffix = Path(filename).suffix.lower() or ".jpg"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        reader = get_ocr_reader()
        results = reader.readtext(tmp_path, detail=0, paragraph=True)
        lines = [str(r).strip() for r in results if str(r).strip()]
        raw_text = "\n".join(lines)

        amount = _parse_indian_amount(lines)
        merchant = _parse_merchant(lines)
        date_str = _parse_indian_date(lines)
        category = _map_indian_receipt_category(raw_text)

        return {
            "raw_text": raw_text,
            "amount": amount,
            "currency": "INR",
            "merchant": merchant,
            "date": date_str,
            "category": category,
            "payment_mode": "UPI",
            "transaction_type": "expense",
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)  # Always delete temp file immediately
            except Exception:
                pass
