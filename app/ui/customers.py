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

from app.services import create_customer, list_customers, record_customer_payment


class CustomersWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_customers()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("Customers and creditors")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        controls = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_customers)
        controls.addWidget(refresh_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Credit Limit", "Outstanding", "Paid So Far"])
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        form_frame = QWidget()
        form_layout = QFormLayout(form_frame)
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()
        self.limit_input = QLineEdit("0")
        self.payment_input = QLineEdit("0")

        form_layout.addRow("Name", self.name_input)
        form_layout.addRow("Phone", self.phone_input)
        form_layout.addRow("Email", self.email_input)
        form_layout.addRow("Address", self.address_input)
        form_layout.addRow("Credit limit", self.limit_input)
        form_layout.addRow("Payment amount", self.payment_input)

        add_button = QPushButton("Add customer")
        add_button.clicked.connect(self.add_customer)
        form_layout.addRow(add_button)

        pay_button = QPushButton("Record payment")
        pay_button.clicked.connect(self.record_payment)
        form_layout.addRow(pay_button)
        layout.addWidget(form_frame)

    def add_customer(self):
        try:
            create_customer(
                name=self.name_input.text().strip(),
                phone=self.phone_input.text().strip(),
                email=self.email_input.text().strip(),
                address=self.address_input.text().strip(),
                credit_limit=float(self.limit_input.text().strip() or 0.0),
            )
            QMessageBox.information(self, "Success", "Customer created")
            self.name_input.clear()
            self.phone_input.clear()
            self.email_input.clear()
            self.address_input.clear()
            self.limit_input.setText("0")
            self.load_customers()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def record_payment(self):
        try:
            customer_id = self.get_selected_customer_id()
            if customer_id is None:
                raise ValueError("Select a customer from the table")
            amount = float(self.payment_input.text().strip() or 0.0)
            record_customer_payment(customer_id, amount, notes="Manual payment")
            QMessageBox.information(self, "Success", "Customer payment recorded")
            self.payment_input.setText("0")
            self.load_customers()
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def get_selected_customer_id(self):
        selected = self.table.selectedItems()
        if not selected:
            return None
        return int(selected[0].text())

    def load_customers(self):
        self.table.setRowCount(0)
        for customer in list_customers():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(customer.id)))
            self.table.setItem(row, 1, QTableWidgetItem(customer.name))
            self.table.setItem(row, 2, QTableWidgetItem(customer.phone or ""))
            self.table.setItem(row, 3, QTableWidgetItem(f"{customer.credit_limit:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{customer.balance_due:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{customer.total_paid:.2f}"))
