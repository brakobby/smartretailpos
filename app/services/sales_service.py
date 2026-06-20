"""
SmartRetail POS — Sales Service

Handles:
  - create_sale() — the core POS transaction
  - void_sale()
  - get_sale() / list_sales()
  - Automatically deducts stock via InventoryService
  - Creates CreditAccount for credit sales
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.config.settings import ALLOW_NEGATIVE_STOCK
from app.database.database import get_session
from app.database.models import (
    Sale, SaleItem, Product, Customer,
    CreditAccount, CreditStatus, PaymentType,
    InventoryTransactionType, AuditLog,
)
from app.services.inventory_service import InventoryService
from app.utils.helpers import generate_invoice_number
from app.utils.session import current_session

logger = logging.getLogger(__name__)


class CartItem:
    """Represents one line in the POS cart."""
    def __init__(self, product_id: int, product_name: str, barcode: str,
                 price: float, cost_price: float, quantity: float = 1,
                 discount: float = 0):
        self.product_id   = product_id
        self.product_name = product_name
        self.barcode      = barcode
        self.price        = price
        self.cost_price   = cost_price
        self.quantity     = quantity
        self.discount     = discount  # per-item discount in currency

    @property
    def subtotal(self) -> float:
        return (self.price * self.quantity) - self.discount

    @property
    def profit(self) -> float:
        return (self.price - self.cost_price) * self.quantity

    def to_dict(self) -> dict:
        return {
            "product_id":   self.product_id,
            "product_name": self.product_name,
            "barcode":      self.barcode,
            "price":        self.price,
            "cost_price":   self.cost_price,
            "quantity":     self.quantity,
            "discount":     self.discount,
            "subtotal":     self.subtotal,
        }


class SalesService:

    # ── Core Transaction ───────────────────────────────────────────────────

    @staticmethod
    def create_sale(
        cart_items: List[CartItem],
        payment_type: PaymentType,
        amount_paid: float,
        customer_id: Optional[int] = None,
        discount: float = 0.0,
        tax_amount: float = 0.0,
        notes: str = "",
    ) -> Tuple[bool, str, Optional[Sale]]:
        """
        Process a complete POS sale.

        Returns (success, message, sale_object).
        """
        if not cart_items:
            return False, "Cart is empty.", None

        if payment_type == PaymentType.CREDIT and customer_id is None:
            return False, "Credit sales require a registered customer.", None

        with get_session() as session:
            # Validate stock for all items
            for item in cart_items:
                product = session.get(Product, item.product_id)
                if product is None or product.is_deleted:
                    return False, f"Product not found: {item.product_name}", None
                if product.quantity < item.quantity and not ALLOW_NEGATIVE_STOCK:
                    return False, (
                        f"Insufficient stock for '{product.product_name}'. "
                        f"Available: {product.quantity:.0f}"
                    ), None

            # Calculate totals
            subtotal = sum(i.subtotal for i in cart_items)
            net_total = subtotal - discount + tax_amount
            balance   = max(net_total - amount_paid, 0)

            # Create Sale record
            invoice_no = generate_invoice_number()
            sale = Sale(
                customer_id=customer_id,
                user_id=current_session.user_id,
                invoice_number=invoice_no,
                total_amount=net_total,
                discount=discount,
                tax_amount=tax_amount,
                amount_paid=amount_paid,
                balance=balance,
                payment_type=payment_type,
                sale_date=datetime.utcnow(),
                notes=notes,
            )
            session.add(sale)
            session.flush()  # Get sale.id

            # Create SaleItems and deduct stock
            for item in cart_items:
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                    cost_price=item.cost_price,
                    discount=item.discount,
                    subtotal=item.subtotal,
                )
                session.add(sale_item)

                # Deduct stock
                ok, msg = InventoryService.adjust_stock(
                    item.product_id,
                    -item.quantity,
                    InventoryTransactionType.SALE,
                    reference=invoice_no,
                    notes=f"POS Sale",
                    session=session,
                )
                if not ok:
                    session.rollback()
                    return False, msg, None

            # Credit account for credit/partial sales
            if payment_type in (PaymentType.CREDIT, PaymentType.MIXED) and balance > 0:
                credit_account = CreditAccount(
                    customer_id=customer_id,
                    sale_id=sale.id,
                    amount=balance,
                    balance=balance,
                    status=CreditStatus.OPEN,
                )
                session.add(credit_account)

            # Audit log
            session.add(AuditLog(
                user_id=current_session.user_id,
                action="SALE_CREATED",
                details=f"Invoice: {invoice_no} | Total: {net_total:.2f} | Paid: {amount_paid:.2f}",
                module="POS",
            ))

            logger.info("Sale created: %s | Total: %.2f", invoice_no, net_total)
            return True, f"Sale recorded. Invoice: {invoice_no}", sale

    # ── Void Sale ─────────────────────────────────────────────────────────

    @staticmethod
    def void_sale(sale_id: int, reason: str = "") -> Tuple[bool, str]:
        if not current_session.is_manager_or_above():
            return False, "Only managers and admins can void sales."

        with get_session() as session:
            sale = session.get(Sale, sale_id)
            if sale is None:
                return False, "Sale not found."
            if sale.is_void:
                return False, "Sale is already voided."

            sale.is_void = True

            # Reverse stock deductions
            for item in sale.sale_items:
                InventoryService.adjust_stock(
                    item.product_id,
                    item.quantity,  # positive = stock returns
                    InventoryTransactionType.RETURN,
                    reference=sale.invoice_number,
                    notes=f"Void: {reason}",
                    session=session,
                )

            session.add(AuditLog(
                user_id=current_session.user_id,
                action="SALE_VOIDED",
                details=f"Invoice: {sale.invoice_number} | Reason: {reason}",
                module="POS",
            ))
            return True, "Sale voided and stock reversed."

    # ── Queries ───────────────────────────────────────────────────────────

    @staticmethod
    def get_sale(sale_id: int) -> Optional[Sale]:
        with get_session() as session:
            return session.get(Sale, sale_id)

    @staticmethod
    def get_sale_by_invoice(invoice_number: str) -> Optional[Sale]:
        with get_session() as session:
            return session.query(Sale).filter_by(invoice_number=invoice_number).first()

    @staticmethod
    def list_sales(limit: int = 100, include_void: bool = False) -> List[Sale]:
        with get_session() as session:
            q = session.query(Sale)
            if not include_void:
                q = q.filter(Sale.is_void == False)
            return q.order_by(Sale.sale_date.desc()).limit(limit).all()

    @staticmethod
    def find_product_by_barcode(barcode: str) -> Optional[Product]:
        with get_session() as session:
            return (
                session.query(Product)
                .filter_by(barcode=barcode.strip(), is_deleted=False)
                .first()
            )

    @staticmethod
    def search_products(query: str, limit: int = 20) -> List[Product]:
        with get_session() as session:
            q_str = f"%{query}%"
            return (
                session.query(Product)
                .filter(
                    Product.is_deleted == False,
                    (Product.product_name.ilike(q_str) | Product.barcode.ilike(q_str))
                )
                .limit(limit)
                .all()
            )
