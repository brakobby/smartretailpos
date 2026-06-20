"""
SmartRetail POS — Unit Tests

Run with:  python -m pytest tests/ -v

Tests cover:
  - Database initialisation
  - Authentication service
  - Inventory service (stock rules)
  - Sales service (cart + transaction)
  - Helper utilities
"""

import sys
import os
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Use an in-memory SQLite database for testing
os.environ["SMARTRETAIL_TEST_DB"] = "sqlite:///:memory:"

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    """Initialise in-memory DB once per test session."""
    # Patch the DATABASE_URL before importing database module
    import app.config.settings as settings
    settings.DATABASE_URL = "sqlite:///:memory:"
    settings.DATABASE_PATH = Path(":memory:")

    from app.database.database import init_db
    init_db()
    yield


@pytest.fixture
def admin_session():
    """Log in as the default admin user."""
    from app.services.auth_service import AuthService
    user = AuthService.authenticate("admin", "admin123")
    assert user is not None, "Default admin login should succeed"
    yield user
    AuthService.logout()


# ── Helper Utilities ──────────────────────────────────────────────────────────

class TestHelpers:

    def test_format_currency(self):
        from app.utils.helpers import format_currency
        assert format_currency(1250.5) == "GHS 1,250.50"
        assert format_currency(0) == "GHS 0.00"

    def test_generate_invoice_number(self):
        from app.utils.helpers import generate_invoice_number
        inv1 = generate_invoice_number()
        inv2 = generate_invoice_number()
        assert inv1.startswith("INV-")
        assert inv1 != inv2  # Should be unique

    def test_validate_barcode(self):
        from app.utils.helpers import validate_barcode
        assert validate_barcode("1234567890123") is True
        assert validate_barcode("ABC") is True
        assert validate_barcode("X") is False   # Too short
        assert validate_barcode("") is False

    def test_hash_and_verify_password(self):
        from app.utils.helpers import hash_password, verify_password
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_left_right_text(self):
        from app.utils.helpers import left_right_text
        result = left_right_text("Left", "Right", 20)
        assert result.startswith("Left")
        assert result.endswith("Right")
        assert len(result) == 20

    def test_get_today_range(self):
        from app.utils.helpers import get_today_range
        start, end = get_today_range()
        assert start < end
        assert start.hour == 0
        assert end.hour == 23

    def test_safe_divide(self):
        from app.utils.helpers import safe_divide
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=99) == 99


# ── Authentication Service ────────────────────────────────────────────────────

class TestAuthService:

    def test_valid_login(self):
        from app.services.auth_service import AuthService
        user = AuthService.authenticate("admin", "admin123")
        assert user is not None
        assert user.username == "admin"
        AuthService.logout()

    def test_invalid_password(self):
        from app.services.auth_service import AuthService
        user = AuthService.authenticate("admin", "wrongpassword")
        assert user is None

    def test_invalid_username(self):
        from app.services.auth_service import AuthService
        user = AuthService.authenticate("nobody", "anything")
        assert user is None

    def test_session_populated_after_login(self, admin_session):
        from app.utils.session import current_session
        assert current_session.is_authenticated
        assert current_session.username == "admin"
        assert current_session.role is not None

    def test_change_password(self, admin_session):
        from app.services.auth_service import AuthService
        from app.utils.session import current_session
        user_id = current_session.user_id
        ok = AuthService.change_password(user_id, "admin123", "newpass123")
        assert ok is True
        # Change back
        ok2 = AuthService.change_password(user_id, "newpass123", "admin123")
        assert ok2 is True

    def test_change_password_wrong_old(self, admin_session):
        from app.services.auth_service import AuthService
        from app.utils.session import current_session
        ok = AuthService.change_password(current_session.user_id, "wrongold", "newpass")
        assert ok is False


# ── Inventory Service ─────────────────────────────────────────────────────────

class TestInventoryService:

    @pytest.fixture
    def sample_product(self, admin_session):
        """Create a test product and return its ID."""
        from app.database.database import get_session
        from app.database.models import Product
        with get_session() as session:
            p = Product(
                barcode=f"TEST{id(self):08d}",
                product_name="Test Product",
                cost_price=10.0,
                selling_price=15.0,
                quantity=100.0,
                minimum_quantity=5.0,
            )
            session.add(p)
            session.flush()
            pid = p.id
        return pid

    def test_stock_in(self, sample_product, admin_session):
        from app.services.inventory_service import InventoryService
        from app.database.database import get_session
        from app.database.models import Product

        ok, msg = InventoryService.stock_in(sample_product, 50, "TEST-REF")
        assert ok is True

        with get_session() as session:
            p = session.get(Product, sample_product)
            assert p.quantity == 150.0

    def test_stock_out(self, sample_product, admin_session):
        from app.services.inventory_service import InventoryService
        from app.database.database import get_session
        from app.database.models import Product

        ok, msg = InventoryService.stock_out(sample_product, 30)
        assert ok is True

        with get_session() as session:
            p = session.get(Product, sample_product)
            assert p.quantity == 70.0  # 100 - 30

    def test_stock_cannot_go_negative(self, sample_product, admin_session):
        from app.services.inventory_service import InventoryService
        # Try to remove more than available
        ok, msg = InventoryService.stock_out(sample_product, 99999)
        assert ok is False
        assert "Insufficient" in msg or "stock" in msg.lower()

    def test_stock_adjustment(self, sample_product, admin_session):
        from app.services.inventory_service import InventoryService
        from app.database.database import get_session
        from app.database.models import Product

        ok, msg = InventoryService.set_stock_level(sample_product, 75.0, "Physical count")
        assert ok is True

        with get_session() as session:
            p = session.get(Product, sample_product)
            assert p.quantity == 75.0

    def test_inventory_transaction_created(self, sample_product, admin_session):
        from app.services.inventory_service import InventoryService
        InventoryService.stock_in(sample_product, 10, "AUDIT-TEST")
        history = InventoryService.get_product_history(sample_product, limit=5)
        assert len(history) > 0
        assert any(t.reference == "AUDIT-TEST" for t in history)


# ── Sales Service ─────────────────────────────────────────────────────────────

class TestSalesService:

    @pytest.fixture
    def cart_product(self, admin_session):
        """Create a product for POS testing."""
        from app.database.database import get_session
        from app.database.models import Product
        with get_session() as session:
            p = Product(
                barcode=f"POS{id(self):08d}",
                product_name="POS Test Item",
                cost_price=20.0,
                selling_price=30.0,
                quantity=50.0,
                minimum_quantity=2.0,
            )
            session.add(p)
            session.flush()
            return {"id": p.id, "name": p.product_name,
                    "price": p.selling_price, "cost": p.cost_price,
                    "barcode": p.barcode}

    def test_cash_sale(self, cart_product, admin_session):
        from app.services.sales_service import SalesService, CartItem
        from app.database.models import PaymentType

        cart = [CartItem(
            product_id=cart_product["id"],
            product_name=cart_product["name"],
            barcode=cart_product["barcode"],
            price=cart_product["price"],
            cost_price=cart_product["cost"],
            quantity=2,
        )]
        ok, msg, sale = SalesService.create_sale(
            cart_items=cart,
            payment_type=PaymentType.CASH,
            amount_paid=60.0,
        )
        assert ok is True
        assert sale is not None
        assert sale.total_amount == 60.0  # 2 x 30
        assert sale.invoice_number.startswith("INV-")

    def test_stock_deducted_after_sale(self, cart_product, admin_session):
        from app.services.sales_service import SalesService, CartItem
        from app.database.models import PaymentType, Product
        from app.database.database import get_session

        with get_session() as session:
            p = session.get(Product, cart_product["id"])
            qty_before = p.quantity

        cart = [CartItem(
            product_id=cart_product["id"],
            product_name=cart_product["name"],
            barcode=cart_product["barcode"],
            price=cart_product["price"],
            cost_price=cart_product["cost"],
            quantity=3,
        )]
        SalesService.create_sale(cart, PaymentType.CASH, 90.0)

        with get_session() as session:
            p = session.get(Product, cart_product["id"])
            assert p.quantity == qty_before - 3

    def test_credit_sale_requires_customer(self, cart_product, admin_session):
        from app.services.sales_service import SalesService, CartItem
        from app.database.models import PaymentType

        cart = [CartItem(
            product_id=cart_product["id"],
            product_name=cart_product["name"],
            barcode=cart_product["barcode"],
            price=cart_product["price"],
            cost_price=cart_product["cost"],
            quantity=1,
        )]
        ok, msg, sale = SalesService.create_sale(
            cart_items=cart,
            payment_type=PaymentType.CREDIT,
            amount_paid=0,
            customer_id=None,  # No customer
        )
        assert ok is False
        assert "customer" in msg.lower()

    def test_empty_cart_rejected(self, admin_session):
        from app.services.sales_service import SalesService
        from app.database.models import PaymentType
        ok, msg, sale = SalesService.create_sale([], PaymentType.CASH, 0)
        assert ok is False
        assert "empty" in msg.lower()

    def test_product_search_by_barcode(self, cart_product, admin_session):
        from app.services.sales_service import SalesService
        product = SalesService.find_product_by_barcode(cart_product["barcode"])
        assert product is not None
        assert product.id == cart_product["id"]

    def test_product_search_by_name(self, cart_product, admin_session):
        from app.services.sales_service import SalesService
        results = SalesService.search_products("POS Test")
        assert len(results) > 0
        assert any(p.id == cart_product["id"] for p in results)


# ── Session Manager ────────────────────────────────────────────────────────────

class TestSession:

    def test_permissions(self, admin_session):
        from app.utils.session import current_session
        assert current_session.has_permission("dashboard") is True
        assert current_session.has_permission("users") is True
        assert current_session.is_admin() is True

    def test_logout_clears_session(self):
        from app.services.auth_service import AuthService
        from app.utils.session import current_session
        AuthService.authenticate("admin", "admin123")
        assert current_session.is_authenticated
        AuthService.logout()
        assert not current_session.is_authenticated
        assert current_session.user_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
