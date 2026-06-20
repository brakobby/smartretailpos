"""SmartRetail POS — Suppliers Window"""
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QTextEdit,
    QDialogButtonBox, QMessageBox, QTabWidget,
)
from app.database.database import get_session
from app.database.models import Supplier, Purchase, PurchaseItem, SupplierPayment, Product
from app.services.inventory_service import InventoryService
from app.database.models import InventoryTransactionType
from app.utils.helpers import format_currency, format_datetime, generate_purchase_number


class SupplierDialog(QDialog):
    def __init__(self, supplier=None, parent=None):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle("Edit Supplier" if supplier else "Add Supplier")
        self.setMinimumWidth(400); self.setModal(True)
        self._build_ui()
        if supplier: self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(14)
        title = QLabel("Edit Supplier" if self.supplier else "Add Supplier")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(title)
        form = QFormLayout(); form.setSpacing(12)
        self.name_input  = QLineEdit(); self.name_input.setFixedHeight(36)
        self.phone_input = QLineEdit(); self.phone_input.setFixedHeight(36)
        self.email_input = QLineEdit(); self.email_input.setFixedHeight(36)
        self.addr_input  = QTextEdit(); self.addr_input.setFixedHeight(64)
        form.addRow("Name *", self.name_input)
        form.addRow("Phone", self.phone_input)
        form.addRow("Email", self.email_input)
        form.addRow("Address", self.addr_input)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self):
        s = self.supplier
        self.name_input.setText(s.supplier_name)
        self.phone_input.setText(s.phone or "")
        self.email_input.setText(s.email or "")
        self.addr_input.setText(s.address or "")

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required."); return
        with get_session() as session:
            if self.supplier is None:
                s = Supplier(supplier_name=name, phone=self.phone_input.text().strip(),
                             email=self.email_input.text().strip(),
                             address=self.addr_input.toPlainText())
                session.add(s)
            else:
                s = session.get(Supplier, self.supplier.id)
                if s:
                    s.supplier_name = name
                    s.phone = self.phone_input.text().strip()
                    s.email = self.email_input.text().strip()
                    s.address = self.addr_input.toPlainText()
        self.accept()


class SuppliersWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(16)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("+ Add Supplier")
        add_btn.setFixedHeight(38)
        add_btn.clicked.connect(self._add_supplier)
        toolbar.addStretch(); toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        tabs = QTabWidget()

        sup_tab = QWidget()
        sl = QVBoxLayout(sup_tab); sl.setContentsMargins(0,12,0,0)
        self.sup_table = QTableWidget()
        self.sup_table.setColumnCount(5)
        self.sup_table.setHorizontalHeaderLabels(["Supplier Name","Phone","Email","Balance","Actions"])
        self.sup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.sup_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sup_table.setAlternatingRowColors(True)
        self.sup_table.verticalHeader().setVisible(False)
        sl.addWidget(self.sup_table)
        tabs.addTab(sup_tab, "Suppliers")

        purchase_tab = QWidget()
        pl = QVBoxLayout(purchase_tab); pl.setContentsMargins(0,12,0,0)
        self.purchase_table = QTableWidget()
        self.purchase_table.setColumnCount(6)
        self.purchase_table.setHorizontalHeaderLabels(["Invoice","Supplier","Total","Paid","Balance","Date"])
        self.purchase_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.purchase_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.purchase_table.setAlternatingRowColors(True)
        self.purchase_table.verticalHeader().setVisible(False)
        pl.addWidget(self.purchase_table)
        tabs.addTab(purchase_tab, "Purchase Orders")

        layout.addWidget(tabs)

    def refresh(self):
        self._load_suppliers(); self._load_purchases()

    def _load_suppliers(self):
        with get_session() as session:
            suppliers = session.query(Supplier).filter_by(is_deleted=False).order_by(Supplier.supplier_name).all()
        self.sup_table.setRowCount(len(suppliers))
        for row, s in enumerate(suppliers):
            self.sup_table.setItem(row, 0, QTableWidgetItem(s.supplier_name))
            self.sup_table.setItem(row, 1, QTableWidgetItem(s.phone or "—"))
            self.sup_table.setItem(row, 2, QTableWidgetItem(s.email or "—"))
            bal_item = QTableWidgetItem(format_currency(s.balance))
            if s.balance > 0:
                from PySide6.QtGui import QColor
                bal_item.setForeground(QColor("#DC2626"))
            self.sup_table.setItem(row, 3, bal_item)
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedHeight(28)
            edit_btn.setStyleSheet("QPushButton{background:#DBEAFE;color:#1D4ED8;border:none;border-radius:5px;font-size:11px;font-weight:600;}")
            edit_btn.clicked.connect(lambda _, sid=s.id: self._edit_supplier(sid))
            self.sup_table.setCellWidget(row, 4, edit_btn)

    def _load_purchases(self):
        with get_session() as session:
            purchases = session.query(Purchase).order_by(Purchase.purchase_date.desc()).limit(200).all()
        self.purchase_table.setRowCount(len(purchases))
        for row, p in enumerate(purchases):
            self.purchase_table.setItem(row, 0, QTableWidgetItem(p.invoice_number))
            sup_name = p.supplier.supplier_name if p.supplier else "—"
            self.purchase_table.setItem(row, 1, QTableWidgetItem(sup_name))
            self.purchase_table.setItem(row, 2, QTableWidgetItem(format_currency(p.total_amount)))
            self.purchase_table.setItem(row, 3, QTableWidgetItem(format_currency(p.amount_paid)))
            bal_item = QTableWidgetItem(format_currency(p.balance))
            if p.balance > 0:
                from PySide6.QtGui import QColor
                bal_item.setForeground(QColor("#DC2626"))
            self.purchase_table.setItem(row, 4, bal_item)
            self.purchase_table.setItem(row, 5, QTableWidgetItem(format_datetime(p.purchase_date)))

    def _add_supplier(self):
        dlg = SupplierDialog(parent=self)
        if dlg.exec() == QDialog.Accepted: self.refresh()

    def _edit_supplier(self, sid: int):
        with get_session() as session:
            s = session.get(Supplier, sid)
        dlg = SupplierDialog(supplier=s, parent=self)
        if dlg.exec() == QDialog.Accepted: self.refresh()
