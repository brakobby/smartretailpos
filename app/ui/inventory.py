from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QSpinBox,
    QPushButton,
    QFormLayout,
    QMessageBox,
    QLineEdit,
)
from PySide6.QtCore import Qt

from app.services import adjust_stock, get_low_stock_products, list_products


class InventoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_inventory()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Inventory control")
        header.setStyleSheet("font-size: 20px; font-weight: 700; color: #0f172a;")
        layout.addWidget(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Stock", "Low Alert", "Status"])
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                background: #ffffff;
                gridline-color: #f1f5f9;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #0f172a;
                font-weight: 600;
                padding: 10px;
                border: none;
            }
        """)
        layout.addWidget(self.table)

        form_frame = QWidget()
        form_frame.setStyleSheet("""
            QWidget {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }
        """)
        form_layout = QFormLayout(form_frame)
        self.product_combo = QComboBox()
        self.quantity_box = QSpinBox()
        self.quantity_box.setRange(-100000, 100000)
        self.notes_input = QLineEdit()
        form_layout.addRow("Product", self.product_combo)
        form_layout.addRow("Quantity change", self.quantity_box)
        form_layout.addRow("Notes", self.notes_input)

        update_btn = QPushButton("Adjust stock")
        update_btn.setStyleSheet("QPushButton { background: #2563eb; color: white; border-radius: 10px; padding: 10px 16px; font-weight: 600; }")
        update_btn.clicked.connect(self.adjust_inventory)
        form_layout.addRow(update_btn)
        layout.addWidget(form_frame)

    def adjust_inventory(self):
        try:
            product_id = self.product_combo.currentData()
            if product_id is None:
                raise ValueError("Select a product")
            adjust_stock(product_id, self.quantity_box.value(), notes=self.notes_input.text().strip())
            QMessageBox.information(self, "Success", "Stock updated")
            self.notes_input.clear()
            self.quantity_box.setValue(0)
            self.load_inventory()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def load_inventory(self):
        self.table.setRowCount(0)
        products = get_low_stock_products()
        self.product_combo.clear()

        for product in list_products():
            self.product_combo.addItem(product.name, product.id)

        for product in products:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            self.table.setItem(row, 1, QTableWidgetItem(product.name))
            self.table.setItem(row, 2, QTableWidgetItem(str(product.stock_quantity)))
            self.table.setItem(row, 3, QTableWidgetItem(str(product.low_stock_alert)))
            status = "LOW STOCK" if product.stock_quantity <= product.low_stock_alert else "OK"
            self.table.setItem(row, 4, QTableWidgetItem(status))
