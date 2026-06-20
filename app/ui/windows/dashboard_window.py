"""
SmartRetail POS — Dashboard Window

Displays:
  - Today's sales, monthly sales, profit, stock value
  - Customer debt, supplier debt
  - Low stock alerts
  - Daily sales bar chart (Matplotlib)
"""

from __future__ import annotations

from datetime import datetime, timedelta, date

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QGridLayout, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView,
)

from app.database.database import get_session
from app.database.models import Sale, Product, CreditAccount, Supplier, SaleItem
from app.utils.helpers import format_currency, get_today_range, get_month_range
from app.utils.session import current_session
from sqlalchemy import func


class StatCard(QFrame):
    """A single KPI card shown on the dashboard."""

    def __init__(self, title: str, value: str, icon: str,
                 color: str = "#2563EB", bg: str = "#DBEAFE", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(110)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Icon circle
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            background-color: {bg};
            border-radius: 24px;
            font-size: 22px;
        """)
        layout.addWidget(icon_lbl)

        # Text
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(
            f"font-size: 22px; font-weight: 700; color: {color};"
        )
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 500;")
        text_col.addWidget(self.value_lbl)
        text_col.addWidget(self.title_lbl)
        layout.addLayout(text_col)
        layout.addStretch()

    def update_value(self, value: str):
        self.value_lbl.setText(value)


class DashboardWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # ── Greeting ──────────────────────────────────────────────────────
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
        name = current_session.full_name or current_session.username or "User"

        greet_lbl = QLabel(f"{greeting}, {name} 👋")
        greet_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        date_lbl = QLabel(datetime.now().strftime("%A, %d %B %Y"))
        date_lbl.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(greet_lbl)
        layout.addWidget(date_lbl)

        # ── KPI Cards ─────────────────────────────────────────────────────
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(16)

        self.card_today   = StatCard("Today's Sales",   "GHS 0.00", "💳", "#2563EB", "#DBEAFE")
        self.card_monthly = StatCard("Monthly Sales",   "GHS 0.00", "📈", "#16A34A", "#DCFCE7")
        self.card_profit  = StatCard("Today's Profit",  "GHS 0.00", "💰", "#D97706", "#FEF3C7")
        self.card_stock   = StatCard("Stock Value",     "GHS 0.00", "📦", "#7C3AED", "#EDE9FE")
        self.card_cust_debt = StatCard("Customer Debt", "GHS 0.00", "👥", "#DC2626", "#FEE2E2")
        self.card_supp_debt = StatCard("Supplier Debt", "GHS 0.00", "🚚", "#0891B2", "#CFFAFE")

        kpi_grid.addWidget(self.card_today,     0, 0)
        kpi_grid.addWidget(self.card_monthly,   0, 1)
        kpi_grid.addWidget(self.card_profit,    0, 2)
        kpi_grid.addWidget(self.card_stock,     1, 0)
        kpi_grid.addWidget(self.card_cust_debt, 1, 1)
        kpi_grid.addWidget(self.card_supp_debt, 1, 2)

        layout.addLayout(kpi_grid)

        # ── Bottom section: chart + low stock ────────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # Weekly sales chart
        chart_card = QFrame()
        chart_card.setObjectName("card")
        chart_card.setStyleSheet("""
            QFrame#card {
                background: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }
        """)
        chart_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        chart_card.setMinimumHeight(280)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(20, 16, 20, 16)

        chart_title = QLabel("Sales — Last 7 Days")
        chart_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #0F172A;")
        chart_layout.addWidget(chart_title)

        self.chart_widget = self._build_chart_placeholder()
        chart_layout.addWidget(self.chart_widget)

        bottom_row.addWidget(chart_card, stretch=2)

        # Low stock list
        low_stock_card = QFrame()
        low_stock_card.setObjectName("card")
        low_stock_card.setStyleSheet("""
            QFrame#card {
                background: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }
        """)
        low_stock_card.setFixedWidth(320)
        low_stock_card.setMinimumHeight(280)
        ls_layout = QVBoxLayout(low_stock_card)
        ls_layout.setContentsMargins(20, 16, 20, 16)

        ls_title = QLabel("⚠️  Low Stock Alert")
        ls_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #D97706;")
        ls_layout.addWidget(ls_title)

        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(3)
        self.low_stock_table.setHorizontalHeaderLabels(["Product", "Qty", "Min"])
        self.low_stock_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.low_stock_table.verticalHeader().setVisible(False)
        self.low_stock_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.low_stock_table.setAlternatingRowColors(True)
        self.low_stock_table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 12px;
            }
        """)
        ls_layout.addWidget(self.low_stock_table)

        bottom_row.addWidget(low_stock_card, stretch=1)
        layout.addLayout(bottom_row)
        layout.addStretch()

    def _build_chart_placeholder(self) -> QWidget:
        """Build Matplotlib chart embedded in Qt widget."""
        try:
            import matplotlib
            matplotlib.use("QtAgg")
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            from matplotlib.figure import Figure

            fig = Figure(figsize=(5, 3), dpi=90)
            fig.patch.set_facecolor("#FFFFFF")
            self._chart_fig = fig
            self._chart_ax  = fig.add_subplot(111)
            canvas = FigureCanvasQTAgg(fig)
            canvas.setStyleSheet("background: transparent;")
            self._chart_canvas = canvas
            return canvas
        except Exception:
            lbl = QLabel("Chart unavailable\n(install matplotlib)")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
            self._chart_canvas = None
            return lbl

    # ── Data Loading ───────────────────────────────────────────────────────

    def refresh(self):
        """Called by MainWindow every time dashboard is navigated to."""
        self._load_kpis()
        self._load_low_stock()
        self._load_chart()

    def _load_kpis(self):
        try:
            with get_session() as session:
                today_start, today_end = get_today_range()
                month_start, month_end = get_month_range()

                # Today's sales
                today_sales = (
                    session.query(func.coalesce(func.sum(Sale.total_amount), 0))
                    .filter(Sale.sale_date.between(today_start, today_end),
                            Sale.is_void == False)
                    .scalar()
                )

                # Monthly sales
                monthly_sales = (
                    session.query(func.coalesce(func.sum(Sale.total_amount), 0))
                    .filter(Sale.sale_date.between(month_start, month_end),
                            Sale.is_void == False)
                    .scalar()
                )

                # Today's profit = sum((price - cost) * qty) for today's sales
                today_profit = (
                    session.query(
                        func.coalesce(
                            func.sum((SaleItem.price - SaleItem.cost_price) * SaleItem.quantity), 0
                        )
                    )
                    .join(Sale)
                    .filter(Sale.sale_date.between(today_start, today_end),
                            Sale.is_void == False)
                    .scalar()
                )

                # Stock value
                stock_value = (
                    session.query(
                        func.coalesce(func.sum(Product.cost_price * Product.quantity), 0)
                    )
                    .filter(Product.is_deleted == False)
                    .scalar()
                )

                # Customer debt
                cust_debt = (
                    session.query(func.coalesce(func.sum(CreditAccount.balance), 0))
                    .scalar()
                )

                # Supplier debt
                supp_debt = (
                    session.query(func.coalesce(func.sum(Supplier.balance), 0))
                    .filter(Supplier.is_deleted == False)
                    .scalar()
                )

            self.card_today.update_value(format_currency(today_sales))
            self.card_monthly.update_value(format_currency(monthly_sales))
            self.card_profit.update_value(format_currency(today_profit))
            self.card_stock.update_value(format_currency(stock_value))
            self.card_cust_debt.update_value(format_currency(cust_debt))
            self.card_supp_debt.update_value(format_currency(supp_debt))
        except Exception as e:
            pass  # Don't crash dashboard on DB error

    def _load_low_stock(self):
        try:
            with get_session() as session:
                products = (
                    session.query(Product)
                    .filter(
                        Product.is_deleted == False,
                        Product.quantity <= Product.minimum_quantity,
                    )
                    .order_by(Product.quantity.asc())
                    .limit(20)
                    .all()
                )

            self.low_stock_table.setRowCount(len(products))
            for row, p in enumerate(products):
                self.low_stock_table.setItem(row, 0, QTableWidgetItem(p.product_name))
                qty_item = QTableWidgetItem(f"{p.quantity:.0f}")
                qty_item.setTextAlignment(Qt.AlignCenter)
                min_item = QTableWidgetItem(f"{p.minimum_quantity:.0f}")
                min_item.setTextAlignment(Qt.AlignCenter)
                if p.quantity == 0:
                    qty_item.setForeground(Qt.red)
                self.low_stock_table.setItem(row, 1, qty_item)
                self.low_stock_table.setItem(row, 2, min_item)
        except Exception:
            pass

    def _load_chart(self):
        if self._chart_canvas is None:
            return
        try:
            # Last 7 days of sales
            today = date.today()
            labels, values = [], []
            with get_session() as session:
                for i in range(6, -1, -1):
                    d = today - timedelta(days=i)
                    start = datetime(d.year, d.month, d.day, 0, 0, 0)
                    end   = datetime(d.year, d.month, d.day, 23, 59, 59)
                    total = (
                        session.query(func.coalesce(func.sum(Sale.total_amount), 0))
                        .filter(Sale.sale_date.between(start, end), Sale.is_void == False)
                        .scalar()
                    )
                    labels.append(d.strftime("%a"))
                    values.append(float(total))

            ax = self._chart_ax
            ax.clear()
            bars = ax.bar(labels, values, color="#2563EB", alpha=0.8, width=0.55, zorder=3)
            ax.set_facecolor("#FFFFFF")
            ax.tick_params(colors="#64748B", labelsize=9)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#E2E8F0")
            ax.spines["bottom"].set_color("#E2E8F0")
            ax.yaxis.grid(True, color="#F1F5F9", zorder=0)
            ax.set_ylabel("GHS", fontsize=9, color="#94A3B8")
            self._chart_fig.tight_layout()
            self._chart_canvas.draw()
        except Exception:
            pass
