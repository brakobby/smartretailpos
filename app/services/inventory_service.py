"""
SmartRetail POS — Inventory Service

Handles all stock movements. Every change creates an InventoryTransaction.
Business rule: stock cannot go below 0 unless ALLOW_NEGATIVE_STOCK is True.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from sqlalchemy import func

from app.config.settings import ALLOW_NEGATIVE_STOCK
from app.database.database import get_session
from app.database.models import (
    Product, InventoryTransaction, InventoryTransactionType, AuditLog,
)
from app.utils.helpers import generate_invoice_number
from app.utils.session import current_session

logger = logging.getLogger(__name__)


class InventoryService:

    # ── Core Stock Adjustment ─────────────────────────────────────────────

    @staticmethod
    def adjust_stock(
        product_id: int,
        quantity_change: float,
        transaction_type: InventoryTransactionType,
        reference: str = "",
        notes: str = "",
        session=None,
    ) -> Tuple[bool, str]:
        """
        Add or remove stock. quantity_change:
          - positive = stock in
          - negative = stock out

        Returns (success, message).
        Can accept an external session for use inside larger transactions.
        """
        def _do(s):
            product = s.get(Product, product_id)
            if product is None or product.is_deleted:
                return False, "Product not found."

            new_qty = product.quantity + quantity_change

            if new_qty < 0 and not ALLOW_NEGATIVE_STOCK:
                return False, (
                    f"Insufficient stock. Available: {product.quantity:.0f}, "
                    f"Requested: {abs(quantity_change):.0f}"
                )

            product.quantity = max(new_qty, 0) if not ALLOW_NEGATIVE_STOCK else new_qty

            txn = InventoryTransaction(
                product_id=product_id,
                transaction_type=transaction_type,
                quantity=quantity_change,
                balance_after=product.quantity,
                reference=reference or generate_invoice_number(),
                notes=notes,
                created_by=current_session.user_id,
            )
            s.add(txn)

            log = AuditLog(
                user_id=current_session.user_id,
                action=f"STOCK_{transaction_type.value}",
                details=(
                    f"Product ID {product_id} | qty change: {quantity_change:+.2f} "
                    f"| new balance: {product.quantity:.2f}"
                ),
                module="INVENTORY",
            )
            s.add(log)
            return True, "Stock updated successfully."

        if session is not None:
            return _do(session)
        else:
            with get_session() as s:
                result = _do(s)
            return result

    # ── Stock In (from supplier / manual) ─────────────────────────────────

    @staticmethod
    def stock_in(product_id: int, quantity: float,
                 reference: str = "", notes: str = "") -> Tuple[bool, str]:
        if quantity <= 0:
            return False, "Quantity must be positive."
        return InventoryService.adjust_stock(
            product_id, quantity, InventoryTransactionType.STOCK_IN,
            reference, notes,
        )

    # ── Stock Out (manual removal) ─────────────────────────────────────────

    @staticmethod
    def stock_out(product_id: int, quantity: float,
                  reference: str = "", notes: str = "") -> Tuple[bool, str]:
        if quantity <= 0:
            return False, "Quantity must be positive."
        return InventoryService.adjust_stock(
            product_id, -quantity, InventoryTransactionType.STOCK_OUT,
            reference, notes,
        )

    # ── Adjustment (correction) ────────────────────────────────────────────

    @staticmethod
    def set_stock_level(product_id: int, new_quantity: float,
                        notes: str = "") -> Tuple[bool, str]:
        """Force the stock to a specific level (e.g. after physical count)."""
        with get_session() as session:
            product = session.get(Product, product_id)
            if product is None:
                return False, "Product not found."
            diff = new_quantity - product.quantity
            return InventoryService.adjust_stock(
                product_id, diff, InventoryTransactionType.ADJUSTMENT,
                "PHYSICAL-COUNT", notes, session=session,
            )

    # ── History ────────────────────────────────────────────────────────────

    @staticmethod
    def get_product_history(product_id: int, limit: int = 100) -> List[InventoryTransaction]:
        with get_session() as session:
            return (
                session.query(InventoryTransaction)
                .filter_by(product_id=product_id)
                .order_by(InventoryTransaction.created_at.desc())
                .limit(limit)
                .all()
            )

    @staticmethod
    def get_all_transactions(
        limit: int = 500,
        transaction_type: Optional[InventoryTransactionType] = None,
    ) -> List[InventoryTransaction]:
        with get_session() as session:
            q = session.query(InventoryTransaction)
            if transaction_type:
                q = q.filter_by(transaction_type=transaction_type)
            return q.order_by(InventoryTransaction.created_at.desc()).limit(limit).all()

    # ── Low Stock ──────────────────────────────────────────────────────────

    @staticmethod
    def get_low_stock_products() -> List[Product]:
        with get_session() as session:
            return (
                session.query(Product)
                .filter(
                    Product.is_deleted == False,
                    Product.quantity <= Product.minimum_quantity,
                )
                .order_by(Product.quantity.asc())
                .all()
            )
