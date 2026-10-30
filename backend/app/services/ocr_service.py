# backend/app/services/ocr_service.py
"""
EasyOCR receipt scanning service.
Lazy-loads the EasyOCR reader once on first use (singleton).
Never saves the image — deletes temp file immediately after processing.
"""
import os
import re
import logging
from pathlib import Path
from typing import Optional
import tempfile

logger = logging.getLogger(__name__)

_ocr_reader = None  # module-level singleton


def _get_reader():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        logger.info("Loading EasyOCR model (first use, CPU mode)...")
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
        logger.info("EasyOCR model loaded.")
    return _ocr_reader


def _parse_amount(lines: list[str]) -> Optional[float]:
    """Extract the best total amount from OCR text lines."""
    # Priority: lines containing TOTAL, GRAND, AMOUNT, BALANCE
    total_patterns = [
        r"(?:grand\s*total|total\s*amount|total|amount\s*due|balance\s*due|amount)[:\s]*\$?\s*([\d,]+\.\d{2})",
        r"\$\s*([\d,]+\.\d{2})\b",
        r"\b([\d,]+\.\d{2})\b",
    ]
    combined = " ".join(lines).lower()
    for pattern in total_patterns:
        matches = re.findall(pattern, combined, re.IGNORECASE)
        if matches:
            # Return largest number found (most likely to be total)
            amounts = []
            for m in matches:
                try:
                    amounts.append(float(m.replace(",", "")))
                except ValueError:
                    pass
            if amounts:
                return max(amounts)
    return None


def _parse_merchant(lines: list[str]) -> str:
    """First 1-2 non-empty, non-numeric lines are likely the merchant name."""
    candidates = []
    for line in lines[:6]:
        line = line.strip()
        if line and len(line) > 2 and not re.match(r"^[\d\s\.\,\$\:\-\/]+$", line):
            candidates.append(line)
        if len(candidates) >= 2:
            break
    return " ".join(candidates[:2]) if candidates else "Unknown Merchant"


def _parse_date(lines: list[str]) -> Optional[str]:
    """Extract a date string."""
    combined = " ".join(lines)
    patterns = [
        r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b",
        r"\b(\d{4}[\/\-]\d{2}[\/\-]\d{2})\b",
        r"\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4})\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, combined, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _guess_category(text: str) -> str:
    text = text.lower()
    if any(k in text for k in ["restaurant", "cafe", "coffee", "food", "pizza", "burger", "diner", "eat", "bar "]):
        return "Food"
    if any(k in text for k in ["pharmacy", "drug", "medical", "clinic", "health", "hospital"]):
        return "Health"
    if any(k in text for k in ["uber", "lyft", "taxi", "gas", "fuel", "transit", "metro", "parking"]):
        return "Transport"
    if any(k in text for k in ["amazon", "walmart", "target", "store", "shop", "market", "buy", "mall"]):
        return "Shopping"
    if any(k in text for k in ["electric", "water", "internet", "phone", "utility", "bill"]):
        return "Bills"
    if any(k in text for k in ["netflix", "spotify", "subscription", "stream"]):
        return "Subscriptions"
    if any(k in text for k in ["movie", "theater", "cinema", "concert", "entertainment"]):
        return "Entertainment"
    return "Shopping"


async def scan_receipt(image_bytes: bytes, filename: str) -> dict:
    """Run EasyOCR on image bytes. Returns parsed fields. Does NOT save to DB."""
    suffix = Path(filename).suffix.lower() or ".jpg"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        reader = _get_reader()
        results = reader.readtext(tmp_path, detail=0, paragraph=True)
        lines = [str(r).strip() for r in results if str(r).strip()]
        raw_text = "\n".join(lines)

        amount = _parse_amount(lines)
        merchant = _parse_merchant(lines)
        date_str = _parse_date(lines)
        category = _guess_category(raw_text)

        return {
            "raw_text": raw_text,
            "amount": amount,
            "merchant": merchant,
            "date": date_str,
            "category": category,
            "transaction_type": "expense",
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)  # Always delete temp file

