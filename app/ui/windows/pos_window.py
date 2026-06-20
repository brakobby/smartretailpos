"""
SmartRetail POS — Point of Sale Window

Layout:
  LEFT: Product search + barcode input
  CENTER: Shopping cart (editable)
  RIGHT: Payment panel

Keyboard shortcuts:
  F1  = New Sale
  F2  = Focus search
  F3  = Open payment dialog
  F4  = Print last receipt
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QComboBox, QDoubleSpinBox, QFormLayout, QSizePolicy,
    QListWidget, QListWidgetItem, QScrollArea, QSpinBox,
)

from app.database.database import get_session
from app.database.models import Customer, PaymentType
from app.services.sales_service import SalesService, CartItem
from app.utils.helpers import format_currency
from app.utils.session import current_session
from app.config.settings import CURRENCY_SYMBOL


class PaymentDialog(QDialog):
    """Payment processing dialog opened from the POS."""

    def __init__(self, cart_total: float, customers, parent=None):
        super().__init__(parent)
        self.cart_total = cart_total
        self.customers  = customers
        self.result_data = {}
        self.setWindowTitle("Process Payment")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("💳  Process Payment")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        # Total display
        total_frame = QFrame()
        total_frame.setStyleSheet("""
            QFrame { background: #F0FDF4; border-radius: 10px; border: 1px solid #BBF7D0; }
        """)
        total_layout = QHBoxLayout(total_frame)
        total_layout.setContentsMargins(16, 12, 16, 12)
        lbl = QLabel("Total Amount:")
        lbl.setStyleSheet("font-size: 14px; color: #15803D; font-weight: 600;")
        val = QLabel(format_currency(self.cart_total))
        val.setStyleSheet("font-size: 20px; font-weight: 700; color: #15803D;")
        total_layout.addWidget(lbl)
        total_layout.addStretch()
        total_layout.addWidget(val)
        layout.addWidget(total_frame)

        form = QFormLayout()
        form.setSpacing(12)

        # Payment type
        self.payment_type_combo = QComboBox()
        self.payment_type_combo.addItem("💵  Cash", PaymentType.CASH)
        self.payment_type_combo.addItem("📱  Mobile Money", PaymentType.MOBILE_MONEY)
        self.payment_type_combo.addItem("📋  Credit", PaymentType.CREDIT)
        self.payment_type_combo.addItem("🔀  Mixed", PaymentType.MIXED)
        self.payment_type_combo.setFixedHeight(38)
        self.payment_type_combo.currentIndexChanged.connect(self._on_payment_type_changed)
        form.addRow("Payment Type:", self.payment_type_combo)

        # Customer
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("Walk-in Customer", None)
        for c in self.customers:
            self.customer_combo.addItem(f"{c.name} ({c.phone})", c.id)
        self.customer_combo.setFixedHeight(38)
        self.customer_row_label = QLabel("Customer:")
        form.addRow(self.customer_row_label, self.customer_combo)

        # Amount paid
        self.amount_paid_spin = QDoubleSpinBox()
        self.amount_paid_spin.setRange(0, 9999999)
        self.amount_paid_spin.setDecimals(2)
        self.amount_paid_spin.setPrefix(f"{CURRENCY_SYMBOL} ")
        self.amount_paid_spin.setValue(self.cart_total)
        self.amount_paid_spin.setFixedHeight(38)
        self.amount_paid_spin.valueChanged.connect(self._update_change)
        form.addRow("Amount Paid:", self.amount_paid_spin)

        # Discount
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, self.cart_total)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setPrefix(f"{CURRENCY_SYMBOL} ")
        self.discount_spin.setFixedHeight(38)
        self.discount_spin.valueChanged.connect(self._update_change)
        form.addRow("Discount:", self.discount_spin)

        layout.addLayout(form)

        # Change display
        self.change_frame = QFrame()
        self.change_frame.setStyleSheet("""
            QFrame { background: #EFF6FF; border-radius: 10px; border: 1px solid #BFDBFE; }
        """)
        change_layout = QHBoxLayout(self.change_frame)
        change_layout.setContentsMargins(16, 10, 16, 10)
        change_lbl = QLabel("Change:")
        change_lbl.setStyleSheet("font-size: 13px; color: #1D4ED8; font-weight: 600;")
        self.change_value_lbl = QLabel(format_currency(0))
        self.change_value_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #1D4ED8;")
        change_layout.addWidget(change_lbl)
        change_layout.addStretch()
        change_layout.addWidget(self.change_value_lbl)
        layout.addWidget(self.change_frame)

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn_secondary")
        cancel_btn.setFixedHeight(42)
        cancel_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #64748B;
                          border: 1.5px solid #E2E8F0; border-radius: 8px;
                          font-weight: 600; padding: 0 20px; }
            QPushButton:hover { background: #F8FAFC; }
        """)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("✓  Confirm Payment")
        confirm_btn.setFixedHeight(42)
        confirm_btn.setStyleSheet("""
            QPushButton { background: #16A34A; color: white; border: none;
                          border-radius: 8px; font-size: 14px; font-weight: 700;
                          padding: 0 24px; }
            QPushButton:hover { background: #15803D; }
        """)
        confirm_btn.clicked.connect(self._confirm)

        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

        self._update_change()

    def _on_payment_type_changed(self):
        pt = self.payment_type_combo.currentData()
        needs_customer = pt in (PaymentType.CREDIT, PaymentType.MIXED)
        self.customer_row_label.setText("Customer *:" if needs_customer else "Customer:")
        if pt == PaymentType.CREDIT:
            self.amount_paid_spin.setValue(0)

    def _update_change(self):
        total   = self.cart_total - self.discount_spin.value()
        paid    = self.amount_paid_spin.value()
        change  = max(paid - total, 0)
        balance = max(total - paid, 0)
        self.change_value_lbl.setText(format_currency(change))
        if balance > 0:
            self.change_frame.setStyleSheet("""
                QFrame { background: #FEF3C7; border-radius: 10px; border: 1px solid #FDE68A; }
            """)
            self.change_value_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #D97706;")
        else:
            self.change_frame.setStyleSheet("""
                QFrame { background: #EFF6FF; border-radius: 10px; border: 1px solid #BFDBFE; }
            """)
            self.change_value_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #1D4ED8;")

    def _confirm(self):
        pt = self.payment_type_combo.currentData()
        customer_id = self.customer_combo.currentData()

        if pt in (PaymentType.CREDIT, PaymentType.MIXED) and customer_id is None:
            QMessageBox.warning(self, "Customer Required",
                                "Please select a customer for credit/mixed payment.")
            return

        self.result_data = {
            "payment_type": pt,
            "customer_id":  customer_id,
            "amount_paid":  self.amount_paid_spin.value(),
            "discount":     self.discount_spin.value(),
        }
        self.accept()


class POSWindow(QWidget):
    """The main Point-of-Sale interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cart: List[CartItem] = []
        self._last_sale = None
        self._customers = []
        self._build_ui()
        self._setup_shortcuts()
        self._load_customers()

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # LEFT PANEL: Search
        left = self._build_left_panel()
        root.addWidget(left)

        # CENTER: Cart
        center = self._build_cart_panel()
        root.addWidget(center, stretch=2)

        # RIGHT: Payment summary
        right = self._build_right_panel()
        root.addWidget(right)

    def _build_left_panel(self) -> QFrame:
        panel = QFrame()
        panel.setFixedWidth(280)
        panel.setStyleSheet("background: #F8FAFC; border-right: 1px solid #E2E8F0;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("🔍  Find Product")
        lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #0F172A;")
        layout.addWidget(lbl)

        # Barcode / search input
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan barcode or type name…")
        self.barcode_input.setFixedHeight(40)
        self.barcode_input.setStyleSheet("""
            QLineEdit { border: 2px solid #2563EB; border-radius: 8px;
                        padding: 0 12px; font-size: 13px; background: #fff; }
        """)
        self.barcode_input.returnPressed.connect(self._on_barcode_entered)
        self.barcode_input.textChanged.connect(self._search_products)
        layout.addWidget(self.barcode_input)

        # Search results list
        self.search_list = QListWidget()
        self.search_list.setStyleSheet("""
            QListWidget { border: 1px solid #E2E8F0; border-radius: 8px;
                          background: #fff; font-size: 12px; }
            QListWidget::item { padding: 8px 10px; border-bottom: 1px solid #F1F5F9; }
            QListWidget::item:hover { background: #EFF6FF; }
            QListWidget::item:selected { background: #DBEAFE; color: #1D4ED8; }
        """)
        self.search_list.itemDoubleClicked.connect(self._add_from_search)
        layout.addWidget(self.search_list)

        shortcut_lbl = QLabel(
            "<b>F1</b> New Sale   <b>F2</b> Search<br>"
            "<b>F3</b> Pay   <b>F4</b> Reprint"
        )
        shortcut_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")
        shortcut_lbl.setTextFormat(Qt.RichText)
        layout.addWidget(shortcut_lbl)

        return panel

    def _build_cart_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet("background: #FFFFFF;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel("🛒  Shopping Cart")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        self.item_count_lbl = QLabel("0 items")
        self.item_count_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.item_count_lbl)
        layout.addLayout(header_row)

        # Cart table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(7)
        self.cart_table.setHorizontalHeaderLabels([
            "#", "Product", "Price", "Qty", "Discount", "Subtotal", ""
        ])
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setShowGrid(False)
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setStyleSheet("""
            QTableWidget { border: 1px solid #E2E8F0; border-radius: 8px; }
        """)
        layout.addWidget(self.cart_table)

        # Clear cart button
        clear_btn = QPushButton("🗑  Clear Cart")
        clear_btn.setStyleSheet("""
            QPushButton { background: #FEE2E2; color: #DC2626; border: none;
                          border-radius: 7px; padding: 8px 16px;
                          font-weight: 600; font-size: 12px; }
            QPushButton:hover { background: #FECACA; }
        """)
        clear_btn.clicked.connect(self._clear_cart)
        layout.addWidget(clear_btn, alignment=Qt.AlignLeft)

        return panel

    def _build_right_panel(self) -> QFrame:
        panel = QFrame()
        panel.setFixedWidth(260)
        panel.setStyleSheet("background: #F8FAFC; border-left: 1px solid #E2E8F0;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(12)

        summary_lbl = QLabel("Order Summary")
        summary_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        layout.addWidget(summary_lbl)

        def stat_row(label: str) -> QLabel:
            row = QHBoxLayout()
            lbl_w = QLabel(label)
            lbl_w.setStyleSheet("font-size: 12px; color: #64748B;")
            val_w = QLabel("GHS 0.00")
            val_w.setStyleSheet("font-size: 13px; font-weight: 600; color: #0F172A;")
            row.addWidget(lbl_w)
            row.addStretch()
            row.addWidget(val_w)
            layout.addLayout(row)
            return val_w

        self.subtotal_lbl = stat_row("Subtotal")
        self.discount_lbl = stat_row("Discount")
        self.tax_lbl      = stat_row("Tax")

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("color: #E2E8F0;")
        layout.addWidget(div)

        # Total
        total_row = QHBoxLayout()
        QLabel_total = QLabel("TOTAL")
        QLabel_total.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F172A;")
        self.total_lbl = QLabel("GHS 0.00")
        self.total_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #2563EB;")
        total_row.addWidget(QLabel_total)
        total_row.addStretch()
        total_row.addWidget(self.total_lbl)
        layout.addLayout(total_row)

        layout.addStretch()

        # Pay button
        self.pay_btn = QPushButton("💳  Process Payment  (F3)")
        self.pay_btn.setFixedHeight(52)
        self.pay_btn.setStyleSheet("""
            QPushButton { background: #16A34A; color: white; border: none;
                          border-radius: 10px; font-size: 14px; font-weight: 700; }
            QPushButton:hover { background: #15803D; }
            QPushButton:disabled { background: #D1D5DB; color: #9CA3AF; }
        """)
        self.pay_btn.setEnabled(False)
        self.pay_btn.clicked.connect(self._process_payment)
        layout.addWidget(self.pay_btn)

        new_sale_btn = QPushButton("+ New Sale  (F1)")
        new_sale_btn.setFixedHeight(40)
        new_sale_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #2563EB;
                          border: 1.5px solid #2563EB; border-radius: 8px;
                          font-weight: 600; font-size: 13px; }
            QPushButton:hover { background: #DBEAFE; }
        """)
        new_sale_btn.clicked.connect(self._new_sale)
        layout.addWidget(new_sale_btn)

        reprint_btn = QPushButton("🖨  Reprint Receipt  (F4)")
        reprint_btn.setFixedHeight(36)
        reprint_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #64748B;
                          border: 1px solid #E2E8F0; border-radius: 7px;
                          font-weight: 500; font-size: 12px; }
            QPushButton:hover { background: #F8FAFC; }
        """)
        reprint_btn.clicked.connect(self._reprint_receipt)
        layout.addWidget(reprint_btn)

        return panel

    # ── Shortcuts ──────────────────────────────────────────────────────────

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("F1"), self).activated.connect(self._new_sale)
        QShortcut(QKeySequence("F2"), self).activated.connect(
            lambda: self.barcode_input.setFocus()
        )
        QShortcut(QKeySequence("F3"), self).activated.connect(self._process_payment)
        QShortcut(QKeySequence("F4"), self).activated.connect(self._reprint_receipt)

    # ── Data Loading ───────────────────────────────────────────────────────

    def _load_customers(self):
        with get_session() as session:
            self._customers = (
                session.query(Customer)
                .filter_by(is_deleted=False)
                .order_by(Customer.name)
                .all()
            )

    def refresh(self):
        self._load_customers()

    # ── Barcode / Search ───────────────────────────────────────────────────

    def _on_barcode_entered(self):
        text = self.barcode_input.text().strip()
        if not text:
            return

        # Try exact barcode lookup first
        product = SalesService.find_product_by_barcode(text)
        if product:
            self._add_to_cart(product)
            self.barcode_input.clear()
            self.search_list.clear()
            return

        # Otherwise treat as name search
        self._search_products(text)

    def _search_products(self, query: str = None):
        text = query if query is not None else self.barcode_input.text().strip()
        self.search_list.clear()
        if len(text) < 2:
            return
        products = SalesService.search_products(text, limit=12)
        for p in products:
            item = QListWidgetItem(
                f"{p.product_name}\n"
                f"  {format_currency(p.selling_price)}  •  Stock: {p.quantity:.0f}"
            )
            item.setData(Qt.UserRole, p.id)
            if p.quantity == 0:
                item.setForeground(QColor("#DC2626"))
            self.search_list.addItem(item)

    def _add_from_search(self, item: QListWidgetItem):
        product_id = item.data(Qt.UserRole)
        with get_session() as session:
            p = session.get(from_product := __import__(
                "app.database.models", fromlist=["Product"]
            ).Product, product_id)
        if p:
            self._add_to_cart(p)
            self.search_list.clear()
            self.barcode_input.clear()
            self.barcode_input.setFocus()

    # ── Cart Management ────────────────────────────────────────────────────

    def _add_to_cart(self, product):
        if product.quantity <= 0:
            QMessageBox.warning(self, "Out of Stock",
                                f"'{product.product_name}' is out of stock.")
            return

        # Check if already in cart → increment
        for item in self.cart:
            if item.product_id == product.id:
                if item.quantity + 1 > product.quantity:
                    QMessageBox.warning(self, "Stock Limit",
                                        f"Only {product.quantity:.0f} units available.")
                    return
                item.quantity += 1
                self._refresh_cart_table()
                return

        cart_item = CartItem(
            product_id=product.id,
            product_name=product.product_name,
            barcode=product.barcode,
            price=product.selling_price,
            cost_price=product.cost_price,
            quantity=1,
        )
        self.cart.append(cart_item)
        self._refresh_cart_table()

    def _refresh_cart_table(self):
        self.cart_table.setRowCount(len(self.cart))
        for row, item in enumerate(self.cart):
            self.cart_table.setItem(row, 0, self._centered(str(row + 1)))
            self.cart_table.setItem(row, 1, QTableWidgetItem(item.product_name))
            self.cart_table.setItem(row, 2, self._centered(format_currency(item.price)))
            self.cart_table.setItem(row, 3, self._centered(f"{item.quantity:.0f}"))
            self.cart_table.setItem(row, 4, self._centered(format_currency(item.discount)))
            self.cart_table.setItem(row, 5, self._centered(format_currency(item.subtotal)))

            # Remove button
            rm_btn = QPushButton("✕")
            rm_btn.setFixedSize(28, 28)
            rm_btn.setStyleSheet("""
                QPushButton { background: #FEE2E2; color: #DC2626; border: none;
                              border-radius: 5px; font-weight: 700; font-size: 13px; }
                QPushButton:hover { background: #FECACA; }
            """)
            rm_btn.clicked.connect(lambda _, r=row: self._remove_cart_item(r))
            self.cart_table.setCellWidget(row, 6, rm_btn)

        self.cart_table.resizeRowsToContents()
        self._update_totals()

    def _centered(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def _remove_cart_item(self, row: int):
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self._refresh_cart_table()

    def _clear_cart(self):
        if self.cart:
            reply = QMessageBox.question(self, "Clear Cart",
                                         "Clear all items from cart?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.cart.clear()
                self._refresh_cart_table()

    def _new_sale(self):
        if self.cart:
            reply = QMessageBox.question(self, "New Sale",
                                         "Start a new sale? Current cart will be cleared.",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        self.cart.clear()
        self._refresh_cart_table()
        self.barcode_input.setFocus()

    def _update_totals(self):
        subtotal = sum(i.subtotal for i in self.cart)
        self.subtotal_lbl.setText(format_currency(subtotal))
        self.discount_lbl.setText(format_currency(0))
        self.tax_lbl.setText(format_currency(0))
        self.total_lbl.setText(format_currency(subtotal))
        self.item_count_lbl.setText(f"{len(self.cart)} item(s)")
        self.pay_btn.setEnabled(len(self.cart) > 0)

    # ── Payment ────────────────────────────────────────────────────────────

    def _process_payment(self):
        if not self.cart:
            return

        total = sum(i.subtotal for i in self.cart)
        dlg = PaymentDialog(total, self._customers, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.result_data
        success, message, sale = SalesService.create_sale(
            cart_items=self.cart,
            payment_type=data["payment_type"],
            amount_paid=data["amount_paid"],
            customer_id=data["customer_id"],
            discount=data["discount"],
        )

        if success:
            self._last_sale = sale
            change = max(data["amount_paid"] - (total - data["discount"]), 0)
            QMessageBox.information(
                self, "Payment Complete",
                f"✅  Sale recorded!\n\n"
                f"Invoice: {sale.invoice_number}\n"
                f"Total: {format_currency(total - data['discount'])}\n"
                f"Paid: {format_currency(data['amount_paid'])}\n"
                f"Change: {format_currency(change)}",
            )
            self.cart.clear()
            self._refresh_cart_table()
        else:
            QMessageBox.critical(self, "Payment Failed", message)

    def _reprint_receipt(self):
        if self._last_sale is None:
            QMessageBox.information(self, "Reprint",
                                    "No recent sale to reprint.")
            return
        QMessageBox.information(self, "Reprint",
                                f"Receipt {self._last_sale.invoice_number} sent to printer.")
