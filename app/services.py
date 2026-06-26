from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .config import BACKUP_DIR, DATA_DIR
from .database import (
    CreditPayment,
    Customer,
    InventoryTransaction,
    Product,
    Sale,
    SaleItem,
    Supplier,
    SupplierTransaction,
    get_session,
)


def _generate_invoice_number(session) -> str:
    last_sale = session.query(Sale).order_by(Sale.id.desc()).first()
    next_number = (last_sale.id + 1) if last_sale else 1
    return f"INV-{next_number:06d}"


def create_product(
    name: str,
    barcode: Optional[str] = None,
    category: str = "General",
    cost_price: float = 0.0,
    selling_price: float = 0.0,
    stock_quantity: int = 0,
    low_stock_alert: int = 10,
    supplier_id: Optional[int] = None,
    unit: str = "pcs",
) -> Product:
    session = get_session()
    try:
        if barcode and session.query(Product).filter(Product.barcode == barcode).first():
            raise ValueError("A product with that barcode already exists")

        product = Product(
            name=name,
            barcode=barcode,
            category=category,
            cost_price=float(cost_price),
            selling_price=float(selling_price),
            stock_quantity=int(stock_quantity),
            low_stock_alert=int(low_stock_alert),
            supplier_id=supplier_id,
            unit=unit,
        )
        session.add(product)
        session.commit()
        session.refresh(product)
        return product
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def list_products() -> List[Product]:
    session = get_session()
    try:
        return session.query(Product).filter(Product.is_active.is_(True)).order_by(Product.name).all()
    finally:
        session.close()


def search_products(query: str) -> List[Product]:
    session = get_session()
    try:
        term = f"%{query.lower()}%"
        return (
            session.query(Product)
            .filter(Product.is_active.is_(True))
            .filter((Product.name.ilike(term)) | (Product.barcode.ilike(term)))
            .order_by(Product.name)
            .all()
        )
    finally:
        session.close()


def get_product_by_barcode(barcode: str) -> Optional[Product]:
    session = get_session()
    try:
        return session.query(Product).filter(Product.barcode == barcode).first()
    finally:
        session.close()


def adjust_stock(product_id: int, quantity_change: int, reference: str = "manual", notes: str = "") -> Product:
    session = get_session()
    try:
        product = session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found")

        product.stock_quantity = max(0, product.stock_quantity + int(quantity_change))
        product.updated_at = datetime.now()
        session.add(
            InventoryTransaction(
                product_id=product.id,
                transaction_type="adjustment",
                quantity=int(quantity_change),
                balance_after=product.stock_quantity,
                reference=reference,
                notes=notes,
            )
        )
        session.commit()
        session.refresh(product)
        return product
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_low_stock_products() -> List[Product]:
    session = get_session()
    try:
        return session.query(Product).filter(Product.is_active.is_(True)).filter(Product.stock_quantity <= Product.low_stock_alert).order_by(Product.stock_quantity).all()
    finally:
        session.close()


def create_supplier(name: str, contact_person: str = "", phone: str = "", email: str = "", address: str = "") -> Supplier:
    session = get_session()
    try:
        supplier = Supplier(name=name, contact_person=contact_person, phone=phone, email=email, address=address)
        session.add(supplier)
        session.commit()
        session.refresh(supplier)
        return supplier
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def list_suppliers() -> List[Supplier]:
    session = get_session()
    try:
        return session.query(Supplier).filter(Supplier.is_active.is_(True)).order_by(Supplier.name).all()
    finally:
        session.close()


def record_supplier_transaction(supplier_id: int, transaction_type: str, amount: float, reference: str = "", notes: str = "") -> SupplierTransaction:
    session = get_session()
    try:
        supplier = session.get(Supplier, supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")

        amount_value = float(amount or 0.0)
        normalized_type = (transaction_type or "").lower()

        if normalized_type in {"purchase", "debit", "stock", "invoice"}:
            supplier.total_purchases += amount_value
            supplier.balance_due += amount_value
        elif normalized_type in {"payment", "settlement", "refund"}:
            supplier.total_paid += amount_value
            supplier.balance_due = max(0.0, supplier.balance_due - amount_value)
        else:
            supplier.balance_due += amount_value

        transaction = SupplierTransaction(
            supplier_id=supplier.id,
            transaction_type=normalized_type or "adjustment",
            amount=amount_value,
            reference=reference,
            notes=notes,
        )
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        session.refresh(supplier)
        return transaction
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_supplier_balance(supplier_id: int) -> float:
    session = get_session()
    try:
        supplier = session.get(Supplier, supplier_id)
        return float(supplier.balance_due) if supplier else 0.0
    finally:
        session.close()


def create_customer(name: str, phone: str = "", email: str = "", address: str = "", credit_limit: float = 0.0) -> Customer:
    session = get_session()
    try:
        customer = Customer(name=name, phone=phone, email=email, address=address, credit_limit=float(credit_limit))
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return customer
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def list_customers() -> List[Customer]:
    session = get_session()
    try:
        return session.query(Customer).filter(Customer.is_active.is_(True)).order_by(Customer.name).all()
    finally:
        session.close()


def record_customer_payment(customer_id: int, amount: float, notes: str = "", payment_method: str = "cash") -> CreditPayment:
    session = get_session()
    try:
        customer = session.get(Customer, customer_id)
        if not customer:
            raise ValueError("Customer not found")

        amount_value = float(amount or 0.0)
        customer.total_paid += amount_value
        customer.balance_due = max(0.0, customer.balance_due - amount_value)
        customer.total_sales = float(customer.total_sales or 0.0)

        payment = CreditPayment(
            customer_id=customer.id,
            amount=amount_value,
            payment_method=payment_method,
            notes=notes,
        )
        session.add(payment)
        session.commit()
        session.refresh(customer)
        session.refresh(payment)
        return payment
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_customer_balance_summary(customer_id: int) -> Dict[str, Any]:
    session = get_session()
    try:
        customer = session.get(Customer, customer_id)
        if not customer:
            return {"opening_balance": 0.0, "outstanding_balance": 0.0, "paid_so_far": 0.0, "total_sales": 0.0}

        outstanding_balance = max(0.0, float(customer.balance_due or 0.0))
        return {
            "opening_balance": float(customer.opening_balance or 0.0),
            "outstanding_balance": outstanding_balance,
            "paid_so_far": float(customer.total_paid or 0.0),
            "total_sales": float(customer.total_sales or 0.0),
        }
    finally:
        session.close()


def _build_document_path(sale_id: int, document_type: str) -> Path:
    output_dir = DATA_DIR / "documents"
    output_dir.mkdir(exist_ok=True)
    return output_dir / f"sale-{sale_id}-{document_type}.pdf"


def generate_receipt_pdf(sale_id: int) -> Path:
    session = get_session()
    try:
        sale = session.get(Sale, sale_id)
        if not sale:
            raise ValueError("Sale not found")

        path = _build_document_path(sale.id, "receipt")
        doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=0.5 * inch, leftMargin=0.5 * inch, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("SmartRetail POS", styles["Title"]))
        story.append(Paragraph("Receipt", styles["Heading2"]))
        story.append(Paragraph(f"Invoice: {sale.invoice_number}", styles["BodyText"]))
        story.append(Paragraph(f"Date: {sale.created_at.strftime('%Y-%m-%d %H:%M') if sale.created_at else '-'}", styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))

        data = [["Product", "Qty", "Unit Price", "Total"]]
        for item in sale.items:
            data.append([item.product_name or "", str(item.quantity), f"{item.unit_price:.2f}", f"{item.total_price:.2f}"])

        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"Subtotal: {sale.total_amount + sale.discount - sale.tax:.2f}", styles["BodyText"]))
        story.append(Paragraph(f"Discount: {sale.discount:.2f}", styles["BodyText"]))
        story.append(Paragraph(f"Tax: {sale.tax:.2f}", styles["BodyText"]))
        story.append(Paragraph(f"Total: {sale.total_amount:.2f}", styles["Heading3"]))
        story.append(Paragraph(f"Amount Paid: {sale.amount_paid:.2f}", styles["BodyText"]))
        story.append(Paragraph(f"Balance: {sale.balance:.2f}", styles["BodyText"]))
        doc.build(story)
        return path
    finally:
        session.close()


def generate_invoice_pdf(sale_id: int) -> Path:
    session = get_session()
    try:
        sale = session.get(Sale, sale_id)
        if not sale:
            raise ValueError("Sale not found")

        path = _build_document_path(sale.id, "invoice")
        doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=0.5 * inch, leftMargin=0.5 * inch, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("SmartRetail POS", styles["Title"]))
        story.append(Paragraph("Invoice", styles["Heading2"]))
        story.append(Paragraph(f"Invoice Number: {sale.invoice_number}", styles["BodyText"]))
        story.append(Paragraph(f"Customer: {sale.customer.name if sale.customer else 'Walk-in'}", styles["BodyText"]))
        story.append(Paragraph(f"Date: {sale.created_at.strftime('%Y-%m-%d %H:%M') if sale.created_at else '-'}", styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))

        data = [["Product", "Qty", "Unit Price", "Total"]]
        for item in sale.items:
            data.append([item.product_name or "", str(item.quantity), f"{item.unit_price:.2f}", f"{item.total_price:.2f}"])

        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2ecc71")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"Total Amount: {sale.total_amount:.2f}", styles["Heading3"]))
        story.append(Paragraph(f"Amount Paid: {sale.amount_paid:.2f}", styles["BodyText"]))
        story.append(Paragraph(f"Balance Due: {sale.balance:.2f}", styles["BodyText"]))
        doc.build(story)
        return path
    finally:
        session.close()


def get_dashboard_data() -> Dict[str, Any]:
    session = get_session()
    try:
        sales = session.query(Sale).all()
        products = session.query(Product).filter(Product.is_active.is_(True)).all()
        customers = session.query(Customer).filter(Customer.is_active.is_(True)).all()

        total_sales = sum(sale.total_amount for sale in sales)
        total_customers = len(customers)
        total_products = len(products)
        low_stock_products = [product for product in products if product.stock_quantity <= product.low_stock_alert]
        outstanding_debt = sum(max(0.0, customer.balance_due or 0.0) for customer in customers)
        inventory_value = sum((product.cost_price or 0.0) * (product.stock_quantity or 0) for product in products)

        return {
            "today_sales": round(sum(sale.total_amount for sale in sales if sale.created_at and sale.created_at.date() == datetime.now().date()), 2),
            "monthly_sales": round(sum(sale.total_amount for sale in sales if sale.created_at and sale.created_at.month == datetime.now().month), 2),
            "transactions_count": len(sales),
            "inventory_value": round(inventory_value, 2),
            "low_stock_count": len(low_stock_products),
            "outstanding_debt": round(outstanding_debt, 2),
            "total_products": total_products,
            "total_customers": total_customers,
        }
    finally:
        session.close()


def create_sale(
    items: List[Dict[str, Any]],
    customer_id: Optional[int] = None,
    payment_type: str = "cash",
    amount_paid: float = 0.0,
    discount: float = 0.0,
    tax: float = 0.0,
    notes: str = "",
    created_by: Optional[int] = None,
) -> Sale:
    session = get_session()
    try:
        sale = Sale(
            invoice_number=_generate_invoice_number(session),
            customer_id=customer_id,
            discount=float(discount),
            tax=float(tax),
            amount_paid=float(amount_paid),
            payment_type=payment_type,
            notes=notes,
            created_by=created_by,
        )
        session.add(sale)
        session.flush()

        subtotal = 0.0
        for item in items:
            product = session.get(Product, int(item["product_id"]))
            if not product:
                raise ValueError("Product not found")

            quantity = int(item.get("quantity", 1))
            if product.stock_quantity < quantity:
                raise ValueError(f"Insufficient stock for {product.name}")

            unit_price = float(item.get("unit_price", product.selling_price))
            total_price = round(unit_price * quantity, 2)
            subtotal += total_price

            product.stock_quantity -= quantity
            product.updated_at = datetime.now()

            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
            )
            session.add(sale_item)
            session.add(
                InventoryTransaction(
                    product_id=product.id,
                    transaction_type="sale",
                    quantity=-quantity,
                    balance_after=product.stock_quantity,
                    reference=sale.invoice_number,
                    notes=notes or f"Sold {quantity} {product.name}",
                    created_by=created_by,
                )
            )

        sale.total_amount = round(subtotal + float(tax) - float(discount), 2)
        sale.balance = round(max(0.0, sale.total_amount - float(amount_paid)), 2)
        sale.payment_status = "paid" if sale.balance <= 0 else "partial"
        session.commit()
        session.refresh(sale)

        if customer_id:
            customer = session.get(Customer, customer_id)
            if customer:
                customer.total_sales += sale.total_amount
                customer.balance_due += sale.balance
                customer.total_paid += min(float(amount_paid), sale.total_amount)
                session.commit()

        generate_receipt_pdf(sale.id)
        generate_invoice_pdf(sale.id)
        return sale
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()