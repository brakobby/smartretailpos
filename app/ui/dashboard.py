"""
Executive Dashboard Widget - Futuristic operations overview.
"""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from datetime import datetime, timedelta

from app.services import get_dashboard_data


class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.bars = []
        self.setup_ui()
        self.refresh_data()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(30000)

    def setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 10px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #29466a;
                border-radius: 5px;
                min-height: 20px;
            }
        """)

        content = QWidget()
        content.setObjectName("dashboard_content")
        content.setStyleSheet("""
            QWidget#dashboard_content {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #050b14, stop:1 #0b1322);
            }
        """)

        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(22)

        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f1b2f, stop:1 #13253f);
                border: 1px solid #24384f;
                border-radius: 24px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 22, 24, 22)

        left_column = QVBoxLayout()
        left_column.setSpacing(8)

        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good Morning"
            emoji = "☀️"
        elif hour < 17:
            greeting = "Good Afternoon"
            emoji = "🌤️"
        else:
            greeting = "Good Evening"
            emoji = "🌙"

        title = QLabel(f"{emoji} {greeting}")
        title.setStyleSheet("font-size: 26px; font-weight: 700; color: #f8fbff;")
        left_column.addWidget(title)

        subtitle = QLabel("Live retail intelligence, stock health, and sales momentum in one executive view.")
        subtitle.setStyleSheet("font-size: 13px; color: #8fb2ff;")
        subtitle.setWordWrap(True)
        left_column.addWidget(subtitle)

        header_layout.addLayout(left_column)
        header_layout.addStretch()

        right_column = QVBoxLayout()
        right_column.setSpacing(8)
        live_badge = QLabel("● LIVE OPERATIONS")
        live_badge.setStyleSheet("font-size: 11px; font-weight: 700; color: #34d399; letter-spacing: 1.2px;")
        right_column.addWidget(live_badge, 0, Qt.AlignRight)

        status_card = QFrame()
        status_card.setStyleSheet("""
            QFrame {
                background: rgba(59,130,246,0.16);
                border: 1px solid rgba(147,197,253,0.2);
                border-radius: 14px;
            }
        """)
        status_layout = QHBoxLayout(status_card)
        status_layout.setContentsMargins(14, 10, 14, 10)
        status_layout.setSpacing(10)
        status_layout.addWidget(QLabel("⚡ System Ready"))
        status_layout.addWidget(QLabel("• Database Active"))
        right_column.addWidget(status_card)

        header_layout.addLayout(right_column)
        main_layout.addWidget(header_frame)

        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(18)

        self.today_sales_card = self.create_kpi_card(
            "TODAY'S SALES",
            "₵0.00",
            "📈",
            "#3b82f6",
            "today_sales",
            "live revenue",
        )
        kpi_grid.addWidget(self.today_sales_card, 0, 0)

        self.transactions_card = self.create_kpi_card(
            "TRANSACTIONS",
            "0",
            "🧾",
            "#8b5cf6",
            "transactions_count",
            "today's activity",
        )
        kpi_grid.addWidget(self.transactions_card, 0, 1)

        self.inventory_card = self.create_kpi_card(
            "INVENTORY VALUE",
            "₵0.00",
            "📦",
            "#22c55e",
            "inventory_value",
            "current stock",
        )
        kpi_grid.addWidget(self.inventory_card, 0, 2)

        self.debt_card = self.create_kpi_card(
            "OUTSTANDING DEBT",
            "₵0.00",
            "👥",
            "#ef4444",
            "outstanding_debt",
            "customer credit",
        )
        kpi_grid.addWidget(self.debt_card, 0, 3)

        main_layout.addLayout(kpi_grid)

        analytics_layout = QHBoxLayout()
        analytics_layout.setSpacing(20)

        chart_frame = QFrame()
        chart_frame.setMinimumHeight(360)
        chart_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172b, stop:1 #121d31);
                border: 1px solid #24384f;
                border-radius: 20px;
            }
        """)
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(20, 20, 20, 20)
        chart_layout.setSpacing(16)

        chart_header = QHBoxLayout()
        chart_title = QLabel("Sales Pulse")
        chart_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fbff;")
        chart_subtitle = QLabel("7-day trend")
        chart_subtitle.setStyleSheet("font-size: 12px; color: #8fb2ff;")
        chart_header.addWidget(chart_title)
        chart_header.addStretch()
        chart_header.addWidget(chart_subtitle)
        chart_layout.addLayout(chart_header)

        chart_content = QWidget()
        chart_content.setStyleSheet("background: transparent; border: none;")
        chart_content.setMinimumHeight(280)
        bars_layout = QHBoxLayout(chart_content)
        bars_layout.setSpacing(12)
        bars_layout.setContentsMargins(8, 0, 8, 16)

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.bars = []
        for day in days:
            bar_col = QVBoxLayout()
            bar_col.setSpacing(8)

            value_label = QLabel("₵0")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #dceafe;")
            bar_col.addWidget(value_label)

            bar = QFrame()
            bar.setFixedWidth(44)
            bar.setMinimumHeight(10)
            bar.setMaximumHeight(10)
            bar.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3b82f6, stop:1 #2563eb);
                    border-radius: 10px;
                    border: none;
                }
            """)
            bar_col.addWidget(bar)

            day_label = QLabel(day)
            day_label.setAlignment(Qt.AlignCenter)
            day_label.setStyleSheet("font-size: 11px; color: #8fb2ff;")
            bar_col.addWidget(day_label)
            bar_col.addStretch()
            bars_layout.addLayout(bar_col)
            self.bars.append((value_label, bar))

        chart_layout.addWidget(chart_content)
        analytics_layout.addWidget(chart_frame, 2)

        table_frame = QFrame()
        table_frame.setMinimumHeight(360)
        table_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172b, stop:1 #121d31);
                border: 1px solid #24384f;
                border-radius: 20px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.setSpacing(12)

        table_header = QHBoxLayout()
        table_title = QLabel("Recent Sales")
        table_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fbff;")
        table_header.addWidget(table_title)
        table_header.addStretch()
        table_header.addWidget(QLabel("Live"))
        table_layout.addLayout(table_header)

        self.recent_sales_table = QTableWidget()
        self.recent_sales_table.setColumnCount(4)
        self.recent_sales_table.setHorizontalHeaderLabels(["Invoice", "Customer", "Amount", "Status"])
        self.recent_sales_table.horizontalHeader().setStretchLastSection(True)
        self.recent_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_sales_table.setAlternatingRowColors(True)
        self.recent_sales_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #24384f;
                border-radius: 12px;
                background: #0b1322;
                gridline-color: #1d2f46;
                color: #eaf4ff;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #122036;
                color: #8fb2ff;
                padding: 10px;
                border: none;
                font-weight: 700;
            }
            QTableWidget::item:alternate {
                background-color: #101b2d;
            }
        """)
        table_layout.addWidget(self.recent_sales_table)
        analytics_layout.addWidget(table_frame, 1)

        main_layout.addLayout(analytics_layout)
        main_layout.addStretch()
        scroll.setWidget(content)

        final_layout = QVBoxLayout(self)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.addWidget(scroll)

    def create_kpi_card(self, title, value, icon, color, object_name, subtitle=""):
        card = QFrame()
        card.setMinimumHeight(138)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #101b2d, stop:1 #13253f);
                border: 1px solid #24384f;
                border-radius: 18px;
                border-left: 4px solid {color};
            }}
            QFrame:hover {{
                border: 1px solid {color};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 700; letter-spacing: 1.1px;")
        header_row.addWidget(title_label)
        header_row.addStretch()

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px;")
        header_row.addWidget(icon_label)
        layout.addLayout(header_row)

        value_label = QLabel(value)
        value_label.setObjectName(f"kpi_{object_name}")
        value_label.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {color};")
        layout.addWidget(value_label)

        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet("font-size: 11px; color: #8fb2ff;")
        layout.addWidget(sub_label)
        return card

    def refresh_data(self):
        try:
            data = get_dashboard_data()
            self.update_value("kpi_today_sales", f"₵{data['today_sales']:,.2f}")
            self.update_value("kpi_transactions_count", str(data['transactions_count']))
            self.update_value("kpi_inventory_value", f"₵{data['inventory_value']:,.2f}")
            self.update_value("kpi_outstanding_debt", f"₵{data['outstanding_debt']:,.2f}")
            self.update_recent_sales_table()
            self.update_sales_chart()
        except Exception as exc:
            print(f"Error refreshing dashboard: {exc}")

    def update_value(self, object_name, text):
        widget = self.findChild(QLabel, object_name)
        if widget and widget.text() != text:
            widget.setText(text)
            self.animate_fade(widget)

    def animate_fade(self, widget):
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect.setOpacity(0.35)
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(450)
        animation.setStartValue(0.35)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()

    def update_recent_sales_table(self):
        try:
            from app.database import SessionLocal, Sale
            from sqlalchemy import desc

            session = SessionLocal()
            try:
                recent_sales = session.query(Sale).order_by(desc(Sale.created_at)).limit(5).all()
                self.recent_sales_table.setRowCount(len(recent_sales))
                for row, sale in enumerate(recent_sales):
                    self.recent_sales_table.setItem(row, 0, QTableWidgetItem(sale.invoice_number or "-"))
                    self.recent_sales_table.setItem(row, 1, QTableWidgetItem(sale.customer.name if sale.customer else "Walk-in"))
                    self.recent_sales_table.setItem(row, 2, QTableWidgetItem(f"₵{sale.total_amount:,.2f}"))
                    self.recent_sales_table.setItem(row, 3, QTableWidgetItem(sale.payment_status.title()))
            finally:
                session.close()
        except Exception as exc:
            print(f"Error updating recent sales table: {exc}")

    def update_sales_chart(self):
        try:
            from app.database import SessionLocal, Sale
            from sqlalchemy import func

            session = SessionLocal()
            try:
                today = datetime.now().date()
                daily_sales = []
                for offset in range(6, -1, -1):
                    target_date = today - timedelta(days=offset)
                    sales = session.query(func.sum(Sale.total_amount)).filter(
                        func.date(Sale.created_at) == target_date
                    ).scalar() or 0
                    daily_sales.append(float(sales))

                max_sales = max(daily_sales) if max(daily_sales) > 0 else 1

                for index, (value_label, bar) in enumerate(self.bars[:7]):
                    value = daily_sales[index]
                    value_label.setText(f"₵{value:,.0f}" if value > 0 else "₵0")
                    target_height = max(18, int((value / max_sales) * 220))

                    if value > 0:
                        bar.setStyleSheet("""
                            QFrame {
                                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #60a5fa, stop:1 #2563eb);
                                border-radius: 10px;
                                border: none;
                            }
                        """)
                    else:
                        bar.setStyleSheet("""
                            QFrame {
                                background: #24384f;
                                border-radius: 10px;
                                border: none;
                            }
                        """)

                    animation = QPropertyAnimation(bar, b"maximumHeight")
                    animation.setDuration(700)
                    animation.setStartValue(bar.maximumHeight())
                    animation.setEndValue(target_height)
                    animation.setEasingCurve(QEasingCurve.OutCubic)
                    animation.start()
            finally:
                session.close()
        except Exception as exc:
            print(f"Error updating chart: {exc}")