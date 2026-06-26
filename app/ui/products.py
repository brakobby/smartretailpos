from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
    QMessageBox,
)
from PySide6.QtCore import Qt

from app.services import create_product, list_products, search_products


class ProductsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Product catalogue")
        header.setStyleSheet("font-size: 20px; font-weight: 700; color: #0f172a;")
        layout.addWidget(header)

        controls = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or barcode")
        self.search_input.setStyleSheet("QLineEdit { padding: 10px; border: 1px solid #cbd5e1; border-radius: 10px; }")
        self.search_input.textChanged.connect(self.load_products)
        controls.addWidget(self.search_input)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("QPushButton { background: #334155; color: white; border-radius: 10px; padding: 10px 14px; font-weight: 600; }")
        refresh_btn.clicked.connect(self.load_products)
        controls.addWidget(refresh_btn)
        layout.addLayout(controls)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Barcode", "Category", "Cost", "Price", "Stock"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
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
        self.name_input = QLineEdit()
        self.barcode_input = QLineEdit()
        self.category_input = QLineEdit("General")
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setMaximum(1000000)
        self.cost_input.setStyleSheet("QDoubleSpinBox { padding: 8px; border-radius: 8px; border: 1px solid #cbd5e1; }")
        self.selling_input = QDoubleSpinBox()
        self.selling_input.setMaximum(1000000)
        self.selling_input.setStyleSheet("QDoubleSpinBox { padding: 8px; border-radius: 8px; border: 1px solid #cbd5e1; }")
        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(100000)
        self.stock_input.setStyleSheet("QSpinBox { padding: 8px; border-radius: 8px; border: 1px solid #cbd5e1; }")
        self.low_stock_input = QSpinBox()
        self.low_stock_input.setValue(10)
        self.low_stock_input.setMaximum(100000)
        self.low_stock_input.setStyleSheet("QSpinBox { padding: 8px; border-radius: 8px; border: 1px solid #cbd5e1; }")

        form_layout.addRow("Name", self.name_input)
        form_layout.addRow("Barcode", self.barcode_input)
        form_layout.addRow("Category", self.category_input)
        form_layout.addRow("Cost price", self.cost_input)
        form_layout.addRow("Selling price", self.selling_input)
        form_layout.addRow("Opening stock", self.stock_input)
        form_layout.addRow("Low-stock alert", self.low_stock_input)

        add_button = QPushButton("Create product")
        add_button.setStyleSheet("QPushButton { background: #2563eb; color: white; border-radius: 10px; padding: 10px 16px; font-weight: 600; }")
        add_button.clicked.connect(self.add_product)
        form_layout.addRow(add_button)
        layout.addWidget(form_frame)

    def add_product(self):
        try:
            product = create_product(
                name=self.name_input.text().strip(),
                barcode=self.barcode_input.text().strip() or None,
                category=self.category_input.text().strip() or "General",
                cost_price=self.cost_input.value(),
                selling_price=self.selling_input.value(),
                stock_quantity=self.stock_input.value(),
                low_stock_alert=self.low_stock_input.value(),
            )
            QMessageBox.information(self, "Success", f"Product {product.name} added successfully")
            self.name_input.clear()
            self.barcode_input.clear()
            self.category_input.setText("General")
            self.cost_input.setValue(0.0)
            self.selling_input.setValue(0.0)
            self.stock_input.setValue(0)
            self.low_stock_input.setValue(10)
            self.load_products()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def load_products(self):
        query = self.search_input.text().strip()
        items = search_products(query) if query else list_products()
        self.table.setRowCount(0)
        for product in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            self.table.setItem(row, 1, QTableWidgetItem(product.name))
            self.table.setItem(row, 2, QTableWidgetItem(product.barcode or ""))
            self.table.setItem(row, 3, QTableWidgetItem(product.category or ""))
            self.table.setItem(row, 4, QTableWidgetItem(f"{product.cost_price:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{product.selling_price:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(str(product.stock_quantity)))
