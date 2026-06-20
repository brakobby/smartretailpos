"""
SmartRetail POS — SQLAlchemy ORM Models
All database tables are defined here using declarative base.
Relationships are fully defined for easy ORM navigation.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint, event,
)
from sqlalchemy.orm import DeclarativeBase, relationship


# ── Declarative Base ──────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """All models inherit from this base."""
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class InventoryTransactionType(str, enum.Enum):
    STOCK_IN    = "STOCK_IN"
    STOCK_OUT   = "STOCK_OUT"
    SALE        = "SALE"
    RETURN      = "RETURN"
    ADJUSTMENT  = "ADJUSTMENT"


class PaymentType(str, enum.Enum):
    CASH         = "CASH"
    CREDIT       = "CREDIT"
    MOBILE_MONEY = "MOBILE_MONEY"
    MIXED        = "MIXED"


class CreditStatus(str, enum.Enum):
    OPEN     = "OPEN"
    PARTIAL  = "PARTIAL"
    PAID     = "PAID"
    OVERDUE  = "OVERDUE"


class UserStatus(str, enum.Enum):
    ACTIVE   = "ACTIVE"
    INACTIVE = "INACTIVE"


# ── Users & Roles ─────────────────────────────────────────────────────────────

class Role(Base):
    """System roles: Administrator, Manager, Cashier, Storekeeper."""
    __tablename__ = "roles"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role {self.role_name}>"


class User(Base):
    """System users with role-based access control."""
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(100), nullable=False, default="")
    role_id       = Column(Integer, ForeignKey("roles.id"), nullable=False)
    status        = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login    = Column(DateTime, nullable=True)

    role       = relationship("Role", back_populates="users")
    sales      = relationship("Sale", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"


# ── Categories ────────────────────────────────────────────────────────────────

class Category(Base):
    """Product categories."""
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(100), unique=True, nullable=False)
    description = Column(Text, default="")
    is_deleted  = Column(Boolean, default=False, nullable=False)

    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


# ── Suppliers ─────────────────────────────────────────────────────────────────

class Supplier(Base):
    """Supplier / vendor records with running balance (debt to supplier)."""
    __tablename__ = "suppliers"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    supplier_name = Column(String(150), nullable=False)
    phone         = Column(String(30), default="")
    email         = Column(String(100), default="")
    address       = Column(Text, default="")
    balance       = Column(Float, default=0.0, nullable=False)  # amount owed
    is_deleted    = Column(Boolean, default=False, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    products          = relationship("Product", back_populates="supplier")
    purchases         = relationship("Purchase", back_populates="supplier")
    supplier_payments = relationship("SupplierPayment", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier {self.supplier_name}>"


# ── Products ──────────────────────────────────────────────────────────────────

class Product(Base):
    """Product master record. Barcode must be unique."""
    __tablename__ = "products"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    barcode          = Column(String(100), unique=True, nullable=False, index=True)
    product_name     = Column(String(200), nullable=False)
    category_id      = Column(Integer, ForeignKey("categories.id"), nullable=True)
    description      = Column(Text, default="")
    cost_price       = Column(Float, nullable=False, default=0.0)
    selling_price    = Column(Float, nullable=False, default=0.0)
    quantity         = Column(Float, nullable=False, default=0.0)
    minimum_quantity = Column(Float, nullable=False, default=5.0)
    supplier_id      = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    is_deleted       = Column(Boolean, default=False, nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category               = relationship("Category", back_populates="products")
    supplier               = relationship("Supplier", back_populates="products")
    sale_items             = relationship("SaleItem", back_populates="product")
    purchase_items         = relationship("PurchaseItem", back_populates="product")
    inventory_transactions = relationship("InventoryTransaction", back_populates="product")

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.minimum_quantity

    @property
    def profit_margin(self) -> float:
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return 0.0

    def __repr__(self):
        return f"<Product {self.product_name} [{self.barcode}]>"


# ── Purchases (from Supplier) ─────────────────────────────────────────────────

class Purchase(Base):
    """Purchase order / goods received from a supplier."""
    __tablename__ = "purchases"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id    = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    total_amount   = Column(Float, nullable=False, default=0.0)
    amount_paid    = Column(Float, nullable=False, default=0.0)
    balance        = Column(Float, nullable=False, default=0.0)  # unpaid to supplier
    purchase_date  = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes          = Column(Text, default="")
    is_deleted     = Column(Boolean, default=False)

    supplier       = relationship("Supplier", back_populates="purchases")
    purchase_items = relationship("PurchaseItem", back_populates="purchase",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Purchase {self.invoice_number}>"


class PurchaseItem(Base):
    """Line items within a purchase order."""
    __tablename__ = "purchase_items"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False)
    product_id  = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity    = Column(Float, nullable=False)
    cost_price  = Column(Float, nullable=False)
    subtotal    = Column(Float, nullable=False)

    purchase = relationship("Purchase", back_populates="purchase_items")
    product  = relationship("Product", back_populates="purchase_items")


# ── Customers ─────────────────────────────────────────────────────────────────

class Customer(Base):
    """Customer records for credit sales."""
    __tablename__ = "customers"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    name         = Column(String(150), nullable=False)
    phone        = Column(String(30), default="", index=True)
    address      = Column(Text, default="")
    credit_limit = Column(Float, default=0.0)
    is_deleted   = Column(Boolean, default=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    sales           = relationship("Sale", back_populates="customer")
    credit_accounts = relationship("CreditAccount", back_populates="customer")

    @property
    def total_outstanding(self) -> float:
        """Sum of all unpaid credit balances."""
        return sum(ca.balance for ca in self.credit_accounts
                   if ca.status != CreditStatus.PAID)

    def __repr__(self):
        return f"<Customer {self.name}>"


# ── Sales ─────────────────────────────────────────────────────────────────────

class Sale(Base):
    """A sales transaction (POS sale)."""
    __tablename__ = "sales"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    customer_id    = Column(Integer, ForeignKey("customers.id"), nullable=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    total_amount   = Column(Float, nullable=False, default=0.0)
    discount       = Column(Float, nullable=False, default=0.0)
    tax_amount     = Column(Float, nullable=False, default=0.0)
    amount_paid    = Column(Float, nullable=False, default=0.0)
    balance        = Column(Float, nullable=False, default=0.0)
    payment_type   = Column(Enum(PaymentType), default=PaymentType.CASH, nullable=False)
    sale_date      = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_void        = Column(Boolean, default=False)
    notes          = Column(Text, default="")

    customer    = relationship("Customer", back_populates="sales")
    user        = relationship("User", back_populates="sales")
    sale_items  = relationship("SaleItem", back_populates="sale",
                               cascade="all, delete-orphan")
    credit_account = relationship("CreditAccount", back_populates="sale",
                                  uselist=False)

    @property
    def net_total(self) -> float:
        return self.total_amount - self.discount + self.tax_amount

    def __repr__(self):
        return f"<Sale {self.invoice_number}>"


class SaleItem(Base):
    """Line items within a sale."""
    __tablename__ = "sale_items"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    sale_id    = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity   = Column(Float, nullable=False)
    price      = Column(Float, nullable=False)   # selling price at time of sale
    cost_price = Column(Float, nullable=False, default=0.0)  # cost at time of sale
    discount   = Column(Float, nullable=False, default=0.0)
    subtotal   = Column(Float, nullable=False)

    sale    = relationship("Sale", back_populates="sale_items")
    product = relationship("Product", back_populates="sale_items")

    @property
    def profit(self) -> float:
        return (self.price - self.cost_price) * self.quantity


# ── Credit Accounts & Payments ────────────────────────────────────────────────

class CreditAccount(Base):
    """Tracks credit extended to a customer for a specific sale."""
    __tablename__ = "credit_accounts"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    sale_id     = Column(Integer, ForeignKey("sales.id"), nullable=True)
    amount      = Column(Float, nullable=False)   # original credit amount
    balance     = Column(Float, nullable=False)   # remaining unpaid
    status      = Column(Enum(CreditStatus), default=CreditStatus.OPEN, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    due_date    = Column(DateTime, nullable=True)

    customer         = relationship("Customer", back_populates="credit_accounts")
    sale             = relationship("Sale", back_populates="credit_account")
    credit_payments  = relationship("CreditPayment", back_populates="credit_account",
                                    cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CreditAccount customer={self.customer_id} balance={self.balance}>"


class CreditPayment(Base):
    """Installment payment towards a customer's credit account."""
    __tablename__ = "credit_payments"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    credit_id      = Column(Integer, ForeignKey("credit_accounts.id"), nullable=False)
    amount         = Column(Float, nullable=False)
    payment_date   = Column(DateTime, default=datetime.utcnow, nullable=False)
    payment_method = Column(String(50), default="CASH")
    notes          = Column(Text, default="")

    credit_account = relationship("CreditAccount", back_populates="credit_payments")


# ── Supplier Payments ─────────────────────────────────────────────────────────

class SupplierPayment(Base):
    """Payment made to a supplier to reduce our debt."""
    __tablename__ = "supplier_payments"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id    = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    purchase_id    = Column(Integer, ForeignKey("purchases.id"), nullable=True)
    amount         = Column(Float, nullable=False)
    payment_date   = Column(DateTime, default=datetime.utcnow, nullable=False)
    payment_method = Column(String(50), default="CASH")
    notes          = Column(Text, default="")

    supplier = relationship("Supplier", back_populates="supplier_payments")


# ── Inventory Transactions ────────────────────────────────────────────────────

class InventoryTransaction(Base):
    """Audit trail of every stock movement."""
    __tablename__ = "inventory_transactions"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    product_id       = Column(Integer, ForeignKey("products.id"), nullable=False)
    transaction_type = Column(Enum(InventoryTransactionType), nullable=False)
    quantity         = Column(Float, nullable=False)   # positive = in, negative = out
    balance_after    = Column(Float, nullable=False)   # stock level after this move
    reference        = Column(String(150), default="")  # invoice/PO number
    notes            = Column(Text, default="")
    created_by       = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="inventory_transactions")

    def __repr__(self):
        return f"<InvTx {self.transaction_type} qty={self.quantity}>"


# ── Expenses ──────────────────────────────────────────────────────────────────

class Expense(Base):
    """Business expense records."""
    __tablename__ = "expenses"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    category    = Column(String(100), nullable=False)
    description = Column(Text, default="")
    amount      = Column(Float, nullable=False)
    date        = Column(DateTime, default=datetime.utcnow, nullable=False)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_deleted  = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Expense {self.category} {self.amount}>"


# ── Audit Logs ────────────────────────────────────────────────────────────────

class AuditLog(Base):
    """
    Immutable log of important user actions.
    Never soft-deleted — audit records are permanent.
    """
    __tablename__ = "audit_logs"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    action    = Column(String(200), nullable=False)
    details   = Column(Text, default="")
    module    = Column(String(50), default="")
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} @ {self.timestamp}>"
