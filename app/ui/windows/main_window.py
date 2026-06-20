"""
SmartRetail POS — Main Application Window

Shell that contains:
  - Sidebar navigation
  - Header bar (user info, clock, theme toggle)
  - Central stacked widget (one page per module)
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget,
    QSizePolicy, QSpacerItem, QStatusBar, QApplication,
)

from app.config.settings import (
    APP_NAME, SIDEBAR_WIDTH, BUSINESS_NAME, ROLE_ADMIN,
)
from app.utils.session import current_session
from app.ui.theme import get_stylesheet, set_theme, current_theme, COLORS_LIGHT

# Page imports (lazy-safe: we import classes, not instances)
from app.ui.windows.dashboard_window import DashboardWindow
from app.ui.windows.products_window import ProductsWindow
from app.ui.windows.inventory_window import InventoryWindow
from app.ui.windows.pos_window import POSWindow
from app.ui.windows.customers_window import CustomersWindow
from app.ui.windows.suppliers_window import SuppliersWindow
from app.ui.windows.reports_window import ReportsWindow
from app.ui.windows.expenses_window import ExpensesWindow
from app.ui.windows.settings_window import SettingsWindow


NAV_ITEMS = [
    ("dashboard",  "🏠",  "Dashboard",    "dashboard"),
    ("pos",        "💳",  "Point of Sale","pos"),
    ("products",   "📦",  "Products",     "products"),
    ("inventory",  "🗃️",  "Inventory",    "inventory"),
    ("customers",  "👥",  "Customers",    "customers"),
    ("suppliers",  "🚚",  "Suppliers",    "suppliers"),
    ("reports",    "📊",  "Reports",      "reports"),
    ("expenses",   "💸",  "Expenses",     "expenses"),
    ("settings",   "⚙️",  "Settings",     "settings"),
]


class MainWindow(QMainWindow):
    """The primary shell window after login."""

    logout_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — {BUSINESS_NAME}")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 860)

        self._pages: dict[str, QWidget] = {}
        self._nav_buttons: dict[str, QPushButton] = {}
        self._current_page = ""

        self._build_ui()
        self._setup_timer()
        self._navigate_to("dashboard")

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar)

        # Right side: header + content
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        header = self._build_header()
        right_layout.addWidget(header)

        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack)

        main_layout.addWidget(right)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        # Build all pages
        self._init_pages()

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #1E293B;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        # Logo
        logo_lbl = QLabel("🛒  SmartRetail")
        logo_lbl.setObjectName("sidebar_title")
        logo_lbl.setStyleSheet("""
            color: #FFFFFF;
            font-size: 16px;
            font-weight: 700;
            padding: 8px 12px 20px 12px;
        """)
        layout.addWidget(logo_lbl)

        # Navigation buttons
        for key, icon, label, perm_key in NAV_ITEMS:
            if not current_session.has_permission(perm_key):
                continue
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("nav_button")
            btn.setFixedHeight(42)
            btn.setStyleSheet(self._nav_btn_style(active=False))
            btn.clicked.connect(lambda checked, k=key: self._navigate_to(k))
            btn.setCursor(Qt.PointingHandCursor)
            self._nav_buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Logout button
        logout_btn = QPushButton("  🚪   Logout")
        logout_btn.setObjectName("nav_button")
        logout_btn.setFixedHeight(42)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #F87171;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(239,68,68,0.12);
            }
        """)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self._on_logout)
        layout.addWidget(logout_btn)

        return sidebar

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
            }
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        # Page title
        self.page_title_lbl = QLabel("Dashboard")
        self.page_title_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #0F172A;"
        )

        layout.addWidget(self.page_title_lbl)
        layout.addStretch()

        # Clock
        self.clock_lbl = QLabel()
        self.clock_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        layout.addWidget(self.clock_lbl)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(div)

        # User info
        role_lbl = QLabel(f"👤  {current_session.full_name or current_session.username}")
        role_lbl.setStyleSheet("font-size: 12px; color: #374151; font-weight: 500;")
        layout.addWidget(role_lbl)

        role_badge = QLabel(current_session.role or "")
        role_badge.setStyleSheet("""
            background: #DBEAFE;
            color: #1D4ED8;
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        layout.addWidget(role_badge)

        return header

    # ── Pages ──────────────────────────────────────────────────────────────

    def _init_pages(self):
        page_map = {
            "dashboard": DashboardWindow,
            "products":  ProductsWindow,
            "inventory": InventoryWindow,
            "pos":       POSWindow,
            "customers": CustomersWindow,
            "suppliers": SuppliersWindow,
            "reports":   ReportsWindow,
            "expenses":  ExpensesWindow,
            "settings":  SettingsWindow,
        }
        for key, cls in page_map.items():
            page = cls()
            self._pages[key] = page
            self.stack.addWidget(page)

    def _navigate_to(self, key: str):
        if key not in self._pages:
            return

        # Update active button styles
        for k, btn in self._nav_buttons.items():
            btn.setStyleSheet(self._nav_btn_style(active=(k == key)))
            btn.setProperty("active", "true" if k == key else "false")

        self.stack.setCurrentWidget(self._pages[key])
        self._current_page = key

        # Update header title
        for nav_key, icon, label, _ in NAV_ITEMS:
            if nav_key == key:
                self.page_title_lbl.setText(f"{icon}  {label}")
                break

        # Refresh page data if it has a refresh method
        page = self._pages[key]
        if hasattr(page, "refresh"):
            page.refresh()

        self._status_bar.showMessage(f"Navigated to {key.title()}")

    # ── Timer (clock) ──────────────────────────────────────────────────────

    def _setup_timer(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_clock)
        self._timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        now = datetime.now().strftime("%a %d %b %Y  %H:%M:%S")
        self.clock_lbl.setText(now)

    # ── Logout ─────────────────────────────────────────────────────────────

    def _on_logout(self):
        from app.services.auth_service import AuthService
        AuthService.logout()
        self.logout_requested.emit()

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _nav_btn_style(active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background-color: #2563EB;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 16px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 600;
                }
            """
        return """
            QPushButton {
                background-color: transparent;
                color: #CBD5E1;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.08);
                color: #FFFFFF;
            }
        """
