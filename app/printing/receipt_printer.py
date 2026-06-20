"""
SmartRetail POS — Receipt Printing Service

Supports:
  - ESC/POS thermal printers via python-escpos
  - Fallback: plain-text receipt for testing / PDF export
  - 58mm and 80mm paper widths
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from app.config.settings import (
    BUSINESS_NAME, BUSINESS_ADDRESS, BUSINESS_PHONE,
    CURRENCY_SYMBOL, PRINTER_TYPE,
    RECEIPT_WIDTH_58MM, RECEIPT_WIDTH_80MM,
)
from app.database.models import Sale
from app.utils.helpers import format_currency, left_right_text, center_text

logger = logging.getLogger(__name__)

# Paper width in characters
WIDTH = RECEIPT_WIDTH_80MM if PRINTER_TYPE == "80mm" else RECEIPT_WIDTH_58MM


# ── Text Receipt Builder ──────────────────────────────────────────────────────

def build_receipt_text(sale: Sale) -> str:
    """
    Build a plain-text receipt string.
    Used for both ESC/POS printing and PDF fallback.
    """
    W = WIDTH
    lines: List[str] = []

    def line(text: str = ""):
        lines.append(text)

    def divider(char: str = "─"):
        lines.append(char * W)

    # Header
    line(center_text(BUSINESS_NAME, W))
    if BUSINESS_ADDRESS:
        line(center_text(BUSINESS_ADDRESS, W))
    if BUSINESS_PHONE:
        line(center_text(BUSINESS_PHONE, W))
    divider("=")

    # Receipt info
    line(left_right_text("Invoice:", sale.invoice_number, W))
    line(left_right_text("Date:", sale.sale_date.strftime("%d %b %Y %H:%M"), W))
    cashier = sale.user.username if sale.user else "—"
    line(left_right_text("Cashier:", cashier, W))
    if sale.customer:
        line(left_right_text("Customer:", sale.customer.name, W))
    divider()

    # Column headers
    lines.append(f"{'Item':<{W-22}}{'Qty':>4}{'Price':>9}{'Total':>9}")
    divider()

    # Line items
    for item in sale.sale_items:
        name = item.product.product_name if item.product else "Unknown"
        # Truncate long names
        max_name = W - 22
        if len(name) > max_name:
            name = name[:max_name - 1] + "…"
        qty_str   = f"{item.quantity:.0f}"
        price_str = f"{item.price:.2f}"
        total_str = f"{item.subtotal:.2f}"
        line(f"{name:<{max_name}}{qty_str:>4}{price_str:>9}{total_str:>9}")
        if item.discount > 0:
            line(f"  {'Discount':>{max_name + 2}}{'-' + f'{item.discount:.2f}':>9}")

    divider()

    # Totals
    gross = sum(i.price * i.quantity for i in sale.sale_items)
    line(left_right_text("Subtotal:", f"{CURRENCY_SYMBOL} {gross:.2f}", W))

    if sale.discount > 0:
        line(left_right_text("Discount:", f"-{CURRENCY_SYMBOL} {sale.discount:.2f}", W))
    if sale.tax_amount > 0:
        line(left_right_text("Tax:", f"{CURRENCY_SYMBOL} {sale.tax_amount:.2f}", W))

    divider("=")
    line(left_right_text("TOTAL:", f"{CURRENCY_SYMBOL} {sale.total_amount:.2f}", W))
    divider("=")

    # Payment
    line(left_right_text("Payment Type:", sale.payment_type.value, W))
    line(left_right_text("Amount Paid:", f"{CURRENCY_SYMBOL} {sale.amount_paid:.2f}", W))
    change = max(sale.amount_paid - sale.total_amount, 0)
    if change > 0:
        line(left_right_text("Change:", f"{CURRENCY_SYMBOL} {change:.2f}", W))
    if sale.balance > 0:
        line(left_right_text("Balance Due:", f"{CURRENCY_SYMBOL} {sale.balance:.2f}", W))

    divider()
    line(center_text("Thank you for your business!", W))
    line(center_text("Please come again 😊", W))
    divider()
    line()  # Feed

    return "\n".join(lines)


# ── ESC/POS Printer ───────────────────────────────────────────────────────────

class ReceiptPrinter:
    """
    Handles ESC/POS printing via python-escpos.
    Falls back to printing the text receipt to the console if no printer found.
    """

    def __init__(self):
        self._printer = None

    def connect_usb(self, vendor_id: int = None, product_id: int = None) -> bool:
        """Connect to USB thermal printer. Auto-detects common vendor IDs."""
        try:
            from escpos.printer import Usb
            # Common thermal printer vendor IDs
            candidates = [(vendor_id, product_id)] if vendor_id else [
                (0x04b8, 0x0202),  # Epson TM-T20
                (0x0416, 0x5011),  # Winpos
                (0x1fc9, 0x2016),  # Custom
                (0x0519, 0x0003),  # Star
            ]
            for vid, pid in candidates:
                if vid is None:
                    continue
                try:
                    self._printer = Usb(vid, pid)
                    logger.info("Connected to printer: VID=%04x PID=%04x", vid, pid)
                    return True
                except Exception:
                    continue
            return False
        except ImportError:
            logger.warning("python-escpos not installed. Using text fallback.")
            return False

    def connect_network(self, host: str, port: int = 9100) -> bool:
        """Connect to network printer."""
        try:
            from escpos.printer import Network
            self._printer = Network(host, port)
            logger.info("Connected to network printer at %s:%d", host, port)
            return True
        except Exception as e:
            logger.error("Network printer connection failed: %s", e)
            return False

    def print_sale(self, sale: Sale) -> bool:
        """Print the receipt for a completed sale."""
        receipt_text = build_receipt_text(sale)

        if self._printer is None:
            # Text fallback — write to console/log for testing
            logger.info("=== RECEIPT (no printer) ===\n%s", receipt_text)
            print(receipt_text)  # noqa: T201
            return True

        try:
            p = self._printer

            # Header — centered bold
            p.set(align="center", bold=True, double_height=True, double_width=True)
            p.text(f"{BUSINESS_NAME}\n")
            p.set(align="center", bold=False, double_height=False, double_width=False)

            if BUSINESS_ADDRESS:
                p.text(f"{BUSINESS_ADDRESS}\n")
            if BUSINESS_PHONE:
                p.text(f"{BUSINESS_PHONE}\n")

            p.text("=" * WIDTH + "\n")
            p.set(align="left")

            # Body
            p.text(f"Invoice: {sale.invoice_number}\n")
            p.text(f"Date:    {sale.sale_date.strftime('%d %b %Y %H:%M')}\n")
            p.text(f"Cashier: {sale.user.username if sale.user else '—'}\n")
            if sale.customer:
                p.text(f"Customer: {sale.customer.name}\n")
            p.text("-" * WIDTH + "\n")

            # Items
            for item in sale.sale_items:
                name = (item.product.product_name if item.product else "Unknown")[:24]
                p.text(f"{name}\n")
                qty_price = f"  {item.quantity:.0f} x {item.price:.2f}"
                subtotal  = f"{item.subtotal:.2f}"
                gap = WIDTH - len(qty_price) - len(subtotal)
                p.text(f"{qty_price}{' ' * max(gap, 1)}{subtotal}\n")

            p.text("=" * WIDTH + "\n")
            p.set(bold=True)
            p.text(f"TOTAL: {CURRENCY_SYMBOL} {sale.total_amount:.2f}\n")
            p.set(bold=False)
            p.text("=" * WIDTH + "\n")
            p.text(f"Paid:  {CURRENCY_SYMBOL} {sale.amount_paid:.2f}\n")
            change = max(sale.amount_paid - sale.total_amount, 0)
            if change > 0:
                p.text(f"Change:{CURRENCY_SYMBOL} {change:.2f}\n")

            p.text("-" * WIDTH + "\n")
            p.set(align="center")
            p.text("Thank you for your business!\n")
            p.cut()
            return True

        except Exception as e:
            logger.error("Print failed: %s", e)
            # Fallback to text
            print(receipt_text)  # noqa: T201
            return False

    def disconnect(self):
        try:
            if self._printer:
                self._printer.close()
        except Exception:
            pass
        self._printer = None


# ── Singleton printer instance ────────────────────────────────────────────────
receipt_printer = ReceiptPrinter()
