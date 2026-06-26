"""
Point of Sale Widget
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QDoubleSpinBox,
    QMessageBox,
)
from PySide6.QtCore import Qt

from app.services import create_sale, get_product_by_barcode, list_customers


class POSWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.cart_items = []
        self.setup_ui()
        self.load_customers()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("Fast checkout")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        scan_row = QHBoxLayout()
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan barcode or type it and press Enter")
        self.barcode_input.returnPressed.connect(self.add_scanned_product)
        scan_row.addWidget(self.barcode_input)
        add_button = QPushButton("Add item")
        add_button.clicked.connect(self.add_scanned_product)
        scan_row.addWidget(add_button)
        layout.addLayout(scan_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Product", "Qty", "Unit Price", "Total", "Action"])
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        bottom_row = QHBoxLayout()
        customer_label = QLabel("Customer")
        bottom_row.addWidget(customer_label)
        self.customer_combo = QComboBox()
        bottom_row.addWidget(self.customer_combo)

        payment_label = QLabel("Payment")
        bottom_row.addWidget(payment_label)
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["cash", "credit", "mobile_money"])
        bottom_row.addWidget(self.payment_combo)

        self.amount_paid = QDoubleSpinBox()
        self.amount_paid.setMaximum(1000000)
        self.amount_paid.setValue(0.0)
        bottom_row.addWidget(QLabel("Amount paid"))
        bottom_row.addWidget(self.amount_paid)
        layout.addLayout(bottom_row)

        buttons = QHBoxLayout()
        checkout_btn = QPushButton("Checkout")
        checkout_btn.clicked.connect(self.checkout)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_cart)
        receipt_btn = QPushButton("Open docs folder")
        receipt_btn.clicked.connect(self.open_documents_folder)
        buttons.addWidget(checkout_btn)
        buttons.addWidget(clear_btn)
        buttons.addWidget(receipt_btn)
        layout.addLayout(buttons)

        self.total_label = QLabel("Total: ₵0.00")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.total_label)

    def load_customers(self):
        self.customer_combo.clear()
        self.customer_combo.addItem("Walk-in", None)
        for customer in list_customers():
            self.customer_combo.addItem(customer.name, customer.id)

    def add_scanned_product(self):
        barcode = self.barcode_input.text().strip()
        if not barcode:
            return

        product = get_product_by_barcode(barcode)
        if not product:
            QMessageBox.warning(self, "Not found", "No product found for that barcode")
            return

        self.cart_items.append({
            "product_id": product.id,
            "name": product.name,
            "quantity": 1,
            "unit_price": product.selling_price,
        })
        self.barcode_input.clear()
        self.refresh_cart()

    def refresh_cart(self):
        self.table.setRowCount(0)
        total = 0.0
        for item in self.cart_items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(item["quantity"])))
            self.table.setItem(row, 2, QTableWidgetItem(f"{item['unit_price']:.2f}"))
            total_price = item["quantity"] * item["unit_price"]
            self.table.setItem(row, 3, QTableWidgetItem(f"{total_price:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem("Remove"))
            total += total_price
        self.total_label.setText(f"Total: ₵{total:.2f}")

    def clear_cart(self):
        self.cart_items = []
        self.table.setRowCount(0)
        self.total_label.setText("Total: ₵0.00")

    def checkout(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Empty cart", "Add at least one product")
            return

        try:
            sale = create_sale(
                items=self.cart_items,
                customer_id=self.customer_combo.currentData(),
                payment_type=self.payment_combo.currentText(),
                amount_paid=self.amount_paid.value(),
                notes="POS checkout",
            )
            QMessageBox.information(self, "Success", f"Sale {sale.invoice_number} completed. Receipt and invoice created.")
            self.clear_cart()
            self.amount_paid.setValue(0.0)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def open_documents_folder(self):
        from app.config import DATA_DIR
        import os

        documents_dir = DATA_DIR / "documents"
        documents_dir.mkdir(exist_ok=True)
        os.system(f"xdg-open '{documents_dir}'")
