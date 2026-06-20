"""SmartRetail POS — Customers & Credit Management Window"""

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QTextEdit,
    QDialogButtonBox, QMessageBox, QTabWidget,
)
from app.database.database import get_session
from app.database.models import Customer, CreditAccount, CreditPayment, CreditStatus
from app.utils.helpers import format_currency, format_datetime


class CustomerDialog(QDialog):
    def __init__(self, customer: Customer = None, parent=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("Edit Customer" if customer else "Add Customer")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build_ui()
        if customer:
            self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        title = QLabel("Edit Customer" if self.customer else "Add Customer")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        self.name_input   = QLineEdit(); self.name_input.setFixedHeight(36)
        self.phone_input  = QLineEdit(); self.phone_input.setFixedHeight(36)
        self.addr_input   = QTextEdit(); self.addr_input.setFixedHeight(64)
        self.limit_spin   = QDoubleSpinBox()
        self.limit_spin.setRange(0, 9999999); self.limit_spin.setDecimals(2)
        self.limit_spin.setPrefix("GHS "); self.limit_spin.setFixedHeight(36)

        form.addRow("Full Name *", self.name_input)
        form.addRow("Phone", self.phone_input)
        form.addRow("Address", self.addr_input)
        form.addRow("Credit Limit", self.limit_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self):
        c = self.customer
        self.name_input.setText(c.name)
        self.phone_input.setText(c.phone or "")
        self.addr_input.setText(c.address or "")
        self.limit_spin.setValue(c.credit_limit or 0)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required.")
            return
        with get_session() as session:
            if self.customer is None:
                c = Customer(name=name, phone=self.phone_input.text().strip(),
                             address=self.addr_input.toPlainText(),
                             credit_limit=self.limit_spin.value())
                session.add(c)
            else:
                c = session.get(Customer, self.customer.id)
                if c:
                    c.name = name
                    c.phone = self.phone_input.text().strip()
                    c.address = self.addr_input.toPlainText()
                    c.credit_limit = self.limit_spin.value()
        self.accept()


class CreditPaymentDialog(QDialog):
    def __init__(self, credit_account: CreditAccount, parent=None):
        super().__init__(parent)
        self.credit_account = credit_account
        self.setWindowTitle("Record Credit Payment")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        title = QLabel("💰  Record Payment")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        layout.addWidget(title)

        bal_lbl = QLabel(f"Outstanding Balance: {format_currency(self.credit_account.balance)}")
        bal_lbl.setStyleSheet("font-size: 13px; color: #DC2626; font-weight: 600;")
        layout.addWidget(bal_lbl)

        form = QFormLayout()
        form.setSpacing(12)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, self.credit_account.balance)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("GHS ")
        self.amount_spin.setValue(self.credit_account.balance)
        self.amount_spin.setFixedHeight(36)
        self.method_input = QLineEdit()
        self.method_input.setText("CASH")
        self.method_input.setFixedHeight(36)
        form.addRow("Amount Paid", self.amount_spin)
        form.addRow("Payment Method", self.method_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        amount = self.amount_spin.value()
        method = self.method_input.text().strip() or "CASH"
        with get_session() as session:
            ca = session.get(CreditAccount, self.credit_account.id)
            if ca is None:
                return
            payment = CreditPayment(credit_id=ca.id, amount=amount, payment_method=method)
            session.add(payment)
            ca.balance -= amount
            if ca.balance <= 0:
                ca.balance = 0
                ca.status = CreditStatus.PAID
            else:
                ca.status = CreditStatus.PARTIAL
        self.accept()


class CustomersWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search customers…")
        self.search_input.setFixedHeight(38)
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self._filter)
        add_btn = QPushButton("+ Add Customer")
        add_btn.setFixedHeight(38)
        add_btn.clicked.connect(self._add_customer)
        toolbar.addWidget(self.search_input)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        tabs = QTabWidget()

        # Customers tab
        cust_tab = QWidget()
        cust_layout = QVBoxLayout(cust_tab)
        cust_layout.setContentsMargins(0, 12, 0, 0)
        self.cust_table = QTableWidget()
        self.cust_table.setColumnCount(6)
        self.cust_table.setHorizontalHeaderLabels(["Name","Phone","Address","Credit Limit","Outstanding","Actions"])
        self.cust_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cust_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cust_table.setAlternatingRowColors(True)
        self.cust_table.verticalHeader().setVisible(False)
        cust_layout.addWidget(self.cust_table)
        tabs.addTab(cust_tab, "Customers")

        # Credit tab
        credit_tab = QWidget()
        credit_layout = QVBoxLayout(credit_tab)
        credit_layout.setContentsMargins(0, 12, 0, 0)
        self.credit_table = QTableWidget()
        self.credit_table.setColumnCount(6)
        self.credit_table.setHorizontalHeaderLabels(["Customer","Amount","Balance","Status","Created","Action"])
        self.credit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.credit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.credit_table.setAlternatingRowColors(True)
        self.credit_table.verticalHeader().setVisible(False)
        credit_layout.addWidget(self.credit_table)
        tabs.addTab(credit_tab, "Credit Accounts")

        layout.addWidget(tabs)
        self._all_customers = []

    def refresh(self):
        self._load_customers()
        self._load_credits()

    def _load_customers(self):
        with get_session() as session:
            self._all_customers = session.query(Customer).filter_by(is_deleted=False).order_by(Customer.name).all()
        self._filter()

    def _filter(self):
        q = self.search_input.text().strip().lower() if hasattr(self, 'search_input') else ""
        filtered = [c for c in self._all_customers
                    if not q or q in c.name.lower() or q in (c.phone or "").lower()]
        self.cust_table.setRowCount(len(filtered))
        for row, c in enumerate(filtered):
            self.cust_table.setItem(row, 0, QTableWidgetItem(c.name))
            self.cust_table.setItem(row, 1, QTableWidgetItem(c.phone or "—"))
            self.cust_table.setItem(row, 2, QTableWidgetItem(c.address or "—"))
            self.cust_table.setItem(row, 3, QTableWidgetItem(format_currency(c.credit_limit)))
            outstanding = c.total_outstanding
            out_item = QTableWidgetItem(format_currency(outstanding))
            out_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if outstanding > 0:
                from PySide6.QtGui import QColor
                out_item.setForeground(QColor("#DC2626"))
            self.cust_table.setItem(row, 4, out_item)
            actions = QWidget()
            al = QHBoxLayout(actions); al.setContentsMargins(4,2,4,2); al.setSpacing(6)
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedHeight(28)
            edit_btn.setStyleSheet("QPushButton{background:#DBEAFE;color:#1D4ED8;border:none;border-radius:5px;font-size:11px;font-weight:600;}QPushButton:hover{background:#BFDBFE;}")
            edit_btn.clicked.connect(lambda _, cid=c.id: self._edit_customer(cid))
            al.addWidget(edit_btn)
            self.cust_table.setCellWidget(row, 5, actions)

    def _load_credits(self):
        with get_session() as session:
            credits = session.query(CreditAccount).order_by(CreditAccount.created_at.desc()).limit(200).all()
        self.credit_table.setRowCount(len(credits))
        for row, ca in enumerate(credits):
            cust_name = ca.customer.name if ca.customer else "—"
            self.credit_table.setItem(row, 0, QTableWidgetItem(cust_name))
            self.credit_table.setItem(row, 1, QTableWidgetItem(format_currency(ca.amount)))
            bal_item = QTableWidgetItem(format_currency(ca.balance))
            if ca.balance > 0:
                from PySide6.QtGui import QColor
                bal_item.setForeground(QColor("#DC2626"))
            self.credit_table.setItem(row, 2, bal_item)
            self.credit_table.setItem(row, 3, QTableWidgetItem(ca.status.value))
            self.credit_table.setItem(row, 4, QTableWidgetItem(format_datetime(ca.created_at)))
            if ca.balance > 0:
                pay_btn = QPushButton("Record Payment")
                pay_btn.setFixedHeight(28)
                pay_btn.setStyleSheet("QPushButton{background:#DCFCE7;color:#16A34A;border:none;border-radius:5px;font-size:11px;font-weight:600;}QPushButton:hover{background:#BBF7D0;}")
                pay_btn.clicked.connect(lambda _, caid=ca.id: self._record_payment(caid))
                self.credit_table.setCellWidget(row, 5, pay_btn)

    def _add_customer(self):
        dlg = CustomerDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()

    def _edit_customer(self, customer_id: int):
        with get_session() as session:
            c = session.get(Customer, customer_id)
        dlg = CustomerDialog(customer=c, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()

    def _record_payment(self, credit_id: int):
        with get_session() as session:
            ca = session.get(CreditAccount, credit_id)
        if ca:
            dlg = CreditPaymentDialog(credit_account=ca, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.refresh()
