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
    QMessageBox,
)
from PySide6.QtCore import Qt

from app.services import create_supplier, list_suppliers, record_supplier_transaction


class SuppliersWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_suppliers()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Suppliers and payables")
        header.setStyleSheet("font-size: 20px; font-weight: 700; color: #0f172a;")
        layout.addWidget(header)

        controls = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("QPushButton { background: #334155; color: white; border-radius: 10px; padding: 10px 14px; font-weight: 600; }")
        refresh_btn.clicked.connect(self.load_suppliers)
        controls.addWidget(refresh_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Contact", "Phone", "Balance Due", "Total Paid"])
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
        self.name_input = QLineEdit()
        self.contact_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()
        self.payment_input = QLineEdit()

        form_layout.addRow("Name", self.name_input)
        form_layout.addRow("Contact person", self.contact_input)
        form_layout.addRow("Phone", self.phone_input)
        form_layout.addRow("Email", self.email_input)
        form_layout.addRow("Address", self.address_input)
        form_layout.addRow("Payment amount", self.payment_input)

        add_button = QPushButton("Add supplier")
        add_button.setStyleSheet("QPushButton { background: #2563eb; color: white; border-radius: 10px; padding: 10px 16px; font-weight: 600; }")
        add_button.clicked.connect(self.add_supplier)
        form_layout.addRow(add_button)

        pay_button = QPushButton("Record payment")
        pay_button.setStyleSheet("QPushButton { background: #16a34a; color: white; border-radius: 10px; padding: 10px 16px; font-weight: 600; }")
        pay_button.clicked.connect(self.record_payment)
        form_layout.addRow(pay_button)
        layout.addWidget(form_frame)

    def add_supplier(self):
        try:
            create_supplier(
                name=self.name_input.text().strip(),
                contact_person=self.contact_input.text().strip(),
                phone=self.phone_input.text().strip(),
                email=self.email_input.text().strip(),
                address=self.address_input.text().strip(),
            )
            QMessageBox.information(self, "Success", "Supplier created")
            self.name_input.clear()
            self.contact_input.clear()
            self.phone_input.clear()
            self.email_input.clear()
            self.address_input.clear()
            self.load_suppliers()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def record_payment(self):
        try:
            supplier_id = self.get_selected_supplier_id()
            if supplier_id is None:
                raise ValueError("Select a supplier from the table")
            amount = float(self.payment_input.text().strip() or 0.0)
            record_supplier_transaction(supplier_id, "payment", amount, notes="Manual payment")
            QMessageBox.information(self, "Success", "Supplier payment recorded")
            self.payment_input.clear()
            self.load_suppliers()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def get_selected_supplier_id(self):
        selected = self.table.selectedItems()
        if not selected:
            return None
        return int(selected[0].text())

    def load_suppliers(self):
        self.table.setRowCount(0)
        for supplier in list_suppliers():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(supplier.id)))
            self.table.setItem(row, 1, QTableWidgetItem(supplier.name))
            self.table.setItem(row, 2, QTableWidgetItem(supplier.contact_person or ""))
            self.table.setItem(row, 3, QTableWidgetItem(supplier.phone or ""))
            self.table.setItem(row, 4, QTableWidgetItem(f"{supplier.balance_due:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{supplier.total_paid:.2f}"))
