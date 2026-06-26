from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

from app.services import get_dashboard_data


class ReportsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Executive Reports")
        header.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fbff;")
        layout.addWidget(header)

        cards = QHBoxLayout()
        cards.setSpacing(16)

        for title, value, accent in [
            ("Daily Sales", "₵0.00", "#3b82f6"),
            ("Transactions", "0", "#10b981"),
            ("Debt", "₵0.00", "#ef4444"),
        ]:
            frame = QFrame()
            frame.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #111d31, stop:1 #0a1322);
                    border: 1px solid #24384f;
                    border-left: 4px solid {accent};
                    border-radius: 14px;
                }}
            """)
            card_layout = QVBoxLayout(frame)
            card_layout.setContentsMargins(16, 16, 16, 16)
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 12px; color: #8fb2ff; font-weight: 600;")
            value_label = QLabel(value)
            value_label.setObjectName(f"report_{title.lower().replace(' ', '_')}")
            value_label.setStyleSheet("font-size: 24px; font-weight: 700; color: #f8fbff;")
            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            cards.addWidget(frame)

        layout.addLayout(cards)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Invoice", "Customer", "Amount", "Status"])
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #0b1322;
                border: 1px solid #24384f;
                border-radius: 12px;
                gridline-color: #1d2f46;
            }
            QHeaderView::section {
                background-color: #122036;
                color: #8fb2ff;
                padding: 10px;
                border: none;
            }
        """)
        layout.addWidget(self.table)

    def load_data(self):
        data = get_dashboard_data()
        self.findChild(QLabel, "report_daily_sales").setText(f"₵{data['today_sales']:,.2f}")
        self.findChild(QLabel, "report_transactions").setText(str(data['transactions_count']))
        self.findChild(QLabel, "report_debt").setText(f"₵{data['outstanding_debt']:,.2f}")
