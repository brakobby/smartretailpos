"""
Database setup and all models
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

from .config import DATABASE_URL

# Setup engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ==================== MODELS ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False, default="cashier")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    audit_logs = relationship("AuditLog", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    barcode = Column(String(50), unique=True)
    category = Column(String(50))
    cost_price = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    stock_quantity = Column(Integer, default=0)
    low_stock_alert = Column(Integer, default=10)
    reorder_level = Column(Integer, default=10)
    unit = Column(String(20), default="pcs")
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    supplier = relationship("Supplier", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")
    inventory_transactions = relationship("InventoryTransaction", back_populates="product")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(String(200))
    credit_limit = Column(Float, default=0.0)
    opening_balance = Column(Float, default=0.0)
    balance_due = Column(Float, default=0.0)
    total_sales = Column(Float, default=0.0)
    total_paid = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    sales = relationship("Sale", back_populates="customer")
    credit_payments = relationship("CreditPayment", back_populates="customer")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(String(200))
    opening_balance = Column(Float, default=0.0)
    balance_due = Column(Float, default=0.0)
    total_purchases = Column(Float, default=0.0)
    total_paid = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    products = relationship("Product", back_populates="supplier")
    transactions = relationship("SupplierTransaction", back_populates="supplier", cascade="all, delete-orphan")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    total_amount = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    amount_paid = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    payment_type = Column(String(20), default="cash")
    payment_status = Column(String(20), default="paid")
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)

    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(String(100))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float)
    total_price = Column(Float)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    transaction_type = Column(String(20))
    quantity = Column(Integer)
    balance_after = Column(Integer)
    reference = Column(String(100))
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)

    product = relationship("Product", back_populates="inventory_transactions")


class CreditPayment(Base):
    __tablename__ = "credit_payments"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    amount = Column(Float, nullable=False)
    payment_method = Column(String(20))
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)

    customer = relationship("Customer", back_populates="credit_payments")


class SupplierTransaction(Base):
    __tablename__ = "supplier_transactions"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    transaction_type = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    reference = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    supplier = relationship("Supplier", back_populates="transactions")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    category = Column(String(50))
    description = Column(String(200))
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100))
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="audit_logs")


# ==================== DATABASE FUNCTIONS ====================

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def get_session():
    """Get database session"""
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise


def create_default_admin():
    """Create default admin user if not exists"""
    from .auth import hash_password

    session = SessionLocal()
    try:
        admin = session.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                full_name="Administrator",
                role="admin",
            )
            session.add(admin)
            session.commit()
            print("Default admin user created!")
    except Exception as e:
        session.rollback()
        print(f"Error creating admin: {e}")
    finally:
        session.close()