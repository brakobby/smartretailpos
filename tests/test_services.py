import os
import unittest

from app.database import Base, engine, get_session
from app.services import (
    create_customer,
    create_product,
    create_sale,
    create_supplier,
    generate_invoice_pdf,
    generate_receipt_pdf,
    get_customer_balance_summary,
    get_supplier_balance,
    record_customer_payment,
    record_supplier_transaction,
)


class ServicesTestCase(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_supplier_balance_and_customer_balance_flow(self):
        supplier = create_supplier(name="North Supplies", phone="0200000000")
        self.assertEqual(get_supplier_balance(supplier.id), 0.0)

        record_supplier_transaction(supplier.id, "purchase", 5000.0, "Initial stock")
        self.assertEqual(get_supplier_balance(supplier.id), 5000.0)

        record_supplier_transaction(supplier.id, "payment", 1500.0, "Partial payment")
        self.assertEqual(get_supplier_balance(supplier.id), 3500.0)

        customer = create_customer(name="Alice Credit", phone="0551234567")
        self.assertEqual(get_customer_balance_summary(customer.id)["outstanding_balance"], 0.0)

        record_customer_payment(customer.id, 200.0, "Partial payment")
        self.assertEqual(get_customer_balance_summary(customer.id)["paid_so_far"], 200.0)
        self.assertEqual(get_customer_balance_summary(customer.id)["outstanding_balance"], 0.0)

    def test_sale_documents_are_generated(self):
        product = create_product(name="Notebook", barcode="1001", selling_price=12.5, stock_quantity=5)
        sale = create_sale(items=[{"product_id": product.id, "quantity": 2, "unit_price": 12.5}], amount_paid=25.0)

        receipt_path = generate_receipt_pdf(sale.id)
        invoice_path = generate_invoice_pdf(sale.id)

        self.assertTrue(receipt_path.exists())
        self.assertTrue(invoice_path.exists())


if __name__ == "__main__":
    unittest.main()
