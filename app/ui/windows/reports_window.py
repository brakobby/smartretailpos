"""SmartRetail POS — Reports Window"""
from __future__ import annotations
from datetime import date
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QComboBox, QDateEdit, QMessageBox, QFileDialog,
)
from PySide6.QtCore import QDate
from sqlalchemy import func
from app.database.database import get_session
from app.database.models import Sale, SaleItem, Product, Expense, CreditAccount, Supplier
from app.utils.helpers import format_currency, get_month_range, get_today_range


class ReportsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(16)

        # Filter bar
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("From:"))
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True); self.date_from.setFixedHeight(36)
        filter_row.addWidget(self.date_from)
        filter_row.addWidget(QLabel("To:"))
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True); self.date_to.setFixedHeight(36)
        filter_row.addWidget(self.date_to)
        run_btn = QPushButton("Generate Report")
        run_btn.setFixedHeight(36); run_btn.clicked.connect(self.refresh)
        filter_row.addWidget(run_btn)
        filter_row.addStretch()

        export_btn = QPushButton("Export Excel")
        export_btn.setFixedHeight(36)
        export_btn.setStyleSheet("QPushButton{background:#16A34A;color:white;border:none;border-radius:7px;padding:0 14px;font-weight:600;}QPushButton:hover{background:#15803D;}")
        export_btn.clicked.connect(self._export_excel)
        filter_row.addWidget(export_btn)
        layout.addLayout(filter_row)

        # Summary cards
        card_row = QHBoxLayout(); card_row.setSpacing(12)
        def make_card(title, attr):
            frame = QFrame()
            frame.setStyleSheet("QFrame{background:#fff;border-radius:10px;border:1px solid #E2E8F0;}")
            fl = QVBoxLayout(frame); fl.setContentsMargins(16,14,16,14)
            lbl = QLabel(title)
            lbl.setStyleSheet("font-size:12px;color:#64748B;font-weight:500;")
            val = QLabel("GHS 0.00")
            val.setStyleSheet("font-size:20px;font-weight:700;color:#0F172A;")
            fl.addWidget(lbl); fl.addWidget(val)
            setattr(self, attr, val)
            return frame
        card_row.addWidget(make_card("Total Sales", "rpt_sales"))
        card_row.addWidget(make_card("Total Profit", "rpt_profit"))
        card_row.addWidget(make_card("Total Expenses", "rpt_expenses"))
        card_row.addWidget(make_card("Net Income", "rpt_net"))
        layout.addLayout(card_row)

        # Sales table
        lbl = QLabel("Sales Breakdown"); lbl.setStyleSheet("font-size:14px;font-weight:600;")
        layout.addWidget(lbl)
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(6)
        self.sales_table.setHorizontalHeaderLabels(["Invoice","Date","Customer","Total","Paid","Balance"])
        self.sales_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.verticalHeader().setVisible(False)
        layout.addWidget(self.sales_table)

    def refresh(self):
        from datetime import datetime
        d_from = self.date_from.date().toPython()
        d_to   = self.date_to.date().toPython()
        start  = datetime(d_from.year, d_from.month, d_from.day, 0, 0, 0)
        end    = datetime(d_to.year, d_to.month, d_to.day, 23, 59, 59)
        with get_session() as session:
            sales = session.query(Sale).filter(
                Sale.sale_date.between(start, end), Sale.is_void == False
            ).order_by(Sale.sale_date.desc()).all()
            total_sales = sum(s.total_amount for s in sales)
            total_profit = session.query(
                func.coalesce(func.sum((SaleItem.price - SaleItem.cost_price) * SaleItem.quantity), 0)
            ).join(Sale).filter(Sale.sale_date.between(start, end), Sale.is_void == False).scalar()
            total_expenses = session.query(
                func.coalesce(func.sum(Expense.amount), 0)
            ).filter(Expense.date.between(start, end)).scalar()

        self.rpt_sales.setText(format_currency(total_sales))
        self.rpt_profit.setText(format_currency(total_profit))
        self.rpt_expenses.setText(format_currency(total_expenses))
        self.rpt_net.setText(format_currency(total_profit - total_expenses))

        self.sales_table.setRowCount(len(sales))
        for row, s in enumerate(sales):
            self.sales_table.setItem(row, 0, QTableWidgetItem(s.invoice_number))
            self.sales_table.setItem(row, 1, QTableWidgetItem(str(s.sale_date)[:16]))
            cust = s.customer.name if s.customer else "Walk-in"
            self.sales_table.setItem(row, 2, QTableWidgetItem(cust))
            self.sales_table.setItem(row, 3, QTableWidgetItem(format_currency(s.total_amount)))
            self.sales_table.setItem(row, 4, QTableWidgetItem(format_currency(s.amount_paid)))
            self.sales_table.setItem(row, 5, QTableWidgetItem(format_currency(s.balance)))

    def _export_excel(self):
        try:
            import openpyxl
            path, _ = QFileDialog.getSaveFileName(self, "Save Excel Report", "sales_report.xlsx", "Excel (*.xlsx)")
            if not path: return
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Sales Report"
            headers = ["Invoice", "Date", "Customer", "Total", "Paid", "Balance"]
            ws.append(headers)
            for row in range(self.sales_table.rowCount()):
                ws.append([
                    self.sales_table.item(row, col).text() if self.sales_table.item(row, col) else ""
                    for col in range(self.sales_table.columnCount())
                ])
            wb.save(path)
            QMessageBox.information(self, "Export", f"Report saved to:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "Missing Library", "openpyxl is not installed.\nRun: pip install openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
