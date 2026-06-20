"""SmartRetail POS — Inventory Window"""

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QDialog,
    QFormLayout, QComboBox, QDoubleSpinBox, QTextEdit,
    QDialogButtonBox, QMessageBox, QTabWidget, QLineEdit,
)
from app.database.database import get_session
from app.database.models import Product, InventoryTransaction, InventoryTransactionType
from app.services.inventory_service import InventoryService
from app.utils.helpers import format_currency, format_datetime


class StockAdjustDialog(QDialog):
    def __init__(self, mode: str = "in", parent=None):
        super().__init__(parent)
        self.mode = mode  # "in", "out", "adjust"
        titles = {"in": "Stock In", "out": "Stock Out", "adjust": "Adjust Stock"}
        self.setWindowTitle(titles.get(mode, "Stock Update"))
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title_map = {"in": "📦  Stock In", "out": "📤  Stock Out", "adjust": "🔧  Adjust Stock"}
        title = QLabel(title_map.get(self.mode, "Stock"))
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self.product_combo = QComboBox()
        self.product_combo.setFixedHeight(36)
        with get_session() as session:
            products = session.query(Product).filter_by(is_deleted=False).order_by(Product.product_name).all()
            for p in products:
                self.product_combo.addItem(f"{p.product_name} (Stock: {p.quantity:.0f})", p.id)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0, 999999)
        self.qty_spin.setDecimals(0)
        self.qty_spin.setFixedHeight(36)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Invoice/PO number (optional)")
        self.ref_input.setFixedHeight(36)

        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(64)
        self.notes_input.setPlaceholderText("Notes (optional)")

        form.addRow("Product *", self.product_combo)
        qty_label = "New Quantity" if self.mode == "adjust" else "Quantity"
        form.addRow(f"{qty_label} *", self.qty_spin)
        form.addRow("Reference", self.ref_input)
        form.addRow("Notes", self.notes_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        product_id = self.product_combo.currentData()
        qty        = self.qty_spin.value()
        ref        = self.ref_input.text().strip()
        notes      = self.notes_input.toPlainText()

        if qty <= 0:
            QMessageBox.warning(self, "Validation", "Quantity must be greater than 0.")
            return

        if self.mode == "in":
            ok, msg = InventoryService.stock_in(product_id, qty, ref, notes)
        elif self.mode == "out":
            ok, msg = InventoryService.stock_out(product_id, qty, ref, notes)
        else:
            ok, msg = InventoryService.set_stock_level(product_id, qty, notes)

        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)


class InventoryWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        btn_in  = QPushButton("📦  Stock In")
        btn_out = QPushButton("📤  Stock Out")
        btn_adj = QPushButton("🔧  Adjust")
        for btn, mode in [(btn_in, "in"), (btn_out, "out"), (btn_adj, "adjust")]:
            btn.setFixedHeight(38)
            btn.clicked.connect(lambda _, m=mode: self._open_dialog(m))
            toolbar.addWidget(btn)
        btn_out.setStyleSheet("QPushButton { background: #FEF3C7; color: #D97706; border: none; border-radius: 7px; padding: 0 14px; font-weight: 600; } QPushButton:hover { background: #FDE68A; }")
        btn_adj.setStyleSheet("QPushButton { background: #E0E7FF; color: #4F46E5; border: none; border-radius: 7px; padding: 0 14px; font-weight: 600; } QPushButton:hover { background: #C7D2FE; }")
        toolbar.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search history…")
        self.search_input.setFixedHeight(38)
        self.search_input.setMaximumWidth(280)
        toolbar.addWidget(self.search_input)
        layout.addLayout(toolbar)

        # Tabs: current stock | history
        tabs = QTabWidget()

        # Stock tab
        stock_tab = QWidget()
        stock_layout = QVBoxLayout(stock_tab)
        stock_layout.setContentsMargins(0, 12, 0, 0)
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(7)
        self.stock_table.setHorizontalHeaderLabels(["Barcode","Product","Category","Cost","Price","Stock","Status"])
        self.stock_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.stock_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.verticalHeader().setVisible(False)
        stock_layout.addWidget(self.stock_table)
        tabs.addTab(stock_tab, "Current Stock")

        # History tab
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        history_layout.setContentsMargins(0, 12, 0, 0)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(["Date","Product","Type","Qty Change","Balance","Reference"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)
        history_layout.addWidget(self.history_table)
        tabs.addTab(history_tab, "Transaction History")

        layout.addWidget(tabs)
        self._tabs = tabs

    def refresh(self):
        self._load_stock()
        self._load_history()

    def _load_stock(self):
        with get_session() as session:
            products = session.query(Product).filter_by(is_deleted=False).order_by(Product.product_name).all()
        self.stock_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.stock_table.setItem(row, 0, QTableWidgetItem(p.barcode))
            self.stock_table.setItem(row, 1, QTableWidgetItem(p.product_name))
            self.stock_table.setItem(row, 2, QTableWidgetItem(p.category.name if p.category else "—"))
            self.stock_table.setItem(row, 3, QTableWidgetItem(format_currency(p.cost_price)))
            self.stock_table.setItem(row, 4, QTableWidgetItem(format_currency(p.selling_price)))
            qty_item = QTableWidgetItem(f"{p.quantity:.0f}")
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.stock_table.setItem(row, 5, qty_item)
            if p.quantity == 0:
                status = "OUT"
                color = "#DC2626"
            elif p.quantity <= p.minimum_quantity:
                status = "LOW"
                color = "#D97706"
            else:
                status = "OK"
                color = "#16A34A"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(__import__("PySide6.QtGui", fromlist=["QColor"]).QColor(color))
            self.stock_table.setItem(row, 6, status_item)

    def _load_history(self):
        with get_session() as session:
            txns = session.query(InventoryTransaction).order_by(
                InventoryTransaction.created_at.desc()
            ).limit(300).all()
        self.history_table.setRowCount(len(txns))
        for row, t in enumerate(txns):
            self.history_table.setItem(row, 0, QTableWidgetItem(format_datetime(t.created_at)))
            prod_name = t.product.product_name if t.product else "—"
            self.history_table.setItem(row, 1, QTableWidgetItem(prod_name))
            self.history_table.setItem(row, 2, QTableWidgetItem(t.transaction_type.value))
            qty_item = QTableWidgetItem(f"{t.quantity:+.0f}")
            qty_item.setTextAlignment(Qt.AlignCenter)
            if t.quantity > 0:
                qty_item.setForeground(__import__("PySide6.QtGui", fromlist=["QColor"]).QColor("#16A34A"))
            else:
                qty_item.setForeground(__import__("PySide6.QtGui", fromlist=["QColor"]).QColor("#DC2626"))
            self.history_table.setItem(row, 3, qty_item)
            bal_item = QTableWidgetItem(f"{t.balance_after:.0f}")
            bal_item.setTextAlignment(Qt.AlignCenter)
            self.history_table.setItem(row, 4, bal_item)
            self.history_table.setItem(row, 5, QTableWidgetItem(t.reference or "—"))

    def _open_dialog(self, mode: str):
        dlg = StockAdjustDialog(mode=mode, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()
