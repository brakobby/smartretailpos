"""
SmartRetail POS — Utility Functions

Contains:
  - generate_invoice_number()
  - format_currency()
  - format_date() / format_datetime()
  - validate_barcode()
  - truncate_text()
  - get_today_range()
"""

from __future__ import annotations

import hashlib
import random
import string
from datetime import datetime, date, timedelta
from typing import Tuple

from app.config.settings import (
    CURRENCY_SYMBOL, DATE_FORMAT, DATETIME_FORMAT,
    DISPLAY_DATE_FORMAT, DISPLAY_DATETIME_FORMAT,
    INVOICE_PREFIX, PURCHASE_PREFIX, RECEIPT_PREFIX,
)


# ── Invoice / Reference Numbers ───────────────────────────────────────────────

def _timestamp_part() -> str:
    """YYMMDDHHmmSS"""
    return datetime.now().strftime("%y%m%d%H%M%S")


def _random_suffix(n: int = 4) -> str:
    return "".join(random.choices(string.digits, k=n))


def generate_invoice_number() -> str:
    """e.g. INV-260618143022-7841"""
    return f"{INVOICE_PREFIX}-{_timestamp_part()}-{_random_suffix()}"


def generate_purchase_number() -> str:
    """e.g. PO-260618143022-3210"""
    return f"{PURCHASE_PREFIX}-{_timestamp_part()}-{_random_suffix()}"


def generate_receipt_number() -> str:
    """e.g. RCP-260618143022-5521"""
    return f"{RECEIPT_PREFIX}-{_timestamp_part()}-{_random_suffix()}"


# ── Currency Formatting ───────────────────────────────────────────────────────

def format_currency(amount: float, symbol: str = CURRENCY_SYMBOL) -> str:
    """Format a float as a currency string: GHS 1,250.00"""
    return f"{symbol} {amount:,.2f}"


def parse_currency(text: str) -> float:
    """Strip symbol and commas, return float."""
    clean = text.replace(CURRENCY_SYMBOL, "").replace(",", "").strip()
    try:
        return float(clean)
    except ValueError:
        return 0.0


# ── Date Helpers ──────────────────────────────────────────────────────────────

def format_date(dt: datetime | date | None) -> str:
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime(DISPLAY_DATE_FORMAT)
    return dt.strftime(DISPLAY_DATE_FORMAT)


def format_datetime(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.strftime(DISPLAY_DATETIME_FORMAT)


def get_today_range() -> Tuple[datetime, datetime]:
    """Return (start_of_day, end_of_day) for today."""
    today = date.today()
    start = datetime(today.year, today.month, today.day, 0, 0, 0)
    end   = datetime(today.year, today.month, today.day, 23, 59, 59)
    return start, end


def get_month_range(year: int = None, month: int = None) -> Tuple[datetime, datetime]:
    """Return (start, end) datetimes for the given month (defaults to current)."""
    today = date.today()
    year  = year or today.year
    month = month or today.month
    start = datetime(year, month, 1, 0, 0, 0)
    if month == 12:
        end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end = datetime(year, month + 1, 1) - timedelta(seconds=1)
    return start, end


# ── Barcode Validation ────────────────────────────────────────────────────────

def validate_barcode(barcode: str) -> bool:
    """
    Accept any non-empty barcode string.
    Barcodes may be EAN-13, UPC-A, Code128, QR, or custom.
    """
    barcode = barcode.strip()
    return len(barcode) >= 3


def generate_internal_barcode(product_id: int) -> str:
    """Generate an internal barcode for products without a manufacturer code."""
    return f"INT{product_id:08d}"


# ── Text Helpers ──────────────────────────────────────────────────────────────

def truncate_text(text: str, max_len: int = 30, ellipsis: str = "…") -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - len(ellipsis)] + ellipsis


def center_text(text: str, width: int) -> str:
    return text.center(width)


def left_right_text(left: str, right: str, width: int) -> str:
    """Format 'left' and 'right' on the same line padded to width."""
    gap = width - len(left) - len(right)
    if gap < 1:
        gap = 1
    return left + " " * gap + right


# ── Number Helpers ────────────────────────────────────────────────────────────

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_profit_margin(cost: float, selling: float) -> float:
    """Return profit margin as a percentage."""
    return safe_divide(selling - cost, cost) * 100


# ── Password Utilities ────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    import bcrypt
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False
