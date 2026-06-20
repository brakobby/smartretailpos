"""
SmartRetail POS — Products Window

Features:
  - Searchable product list with category filter
  - Add / Edit / Delete products
  - Stock level badges
  - Barcode lookup
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QDialog,
    QFormLayout, QDoubleSpinBox, QSpinBox, QTextEdit,
    QDialogButtonBox,
)
from PySide6.QtGui import QColor

from app.database.database import get_session
from app.database.models import Product, Category, Supplier
from app.services.inventory_service import InventoryService
from app.utils.helpers import format_currency
from app.utils.session import current_session
from app.config.settings import ROLE_ADMIN, ROLE_MANAGER


class ProductDialog(QDialog):
    """Add or Edit product dialog."""

    def __init__(self, product: Product = None, parent=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Edit Product" if product else "Add New Product")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        if product:
            self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Edit Product" if self.product else "Add New Product")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan or type barcode")
        self.barcode_input.setFixedHeight(36)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product name")
        self.name_input.setFixedHeight(36)

        self.category_combo = QComboBox()
        self.category_combo.setFixedHeight(36)
        self._load_categories()

        self.supplier_combo = QComboBox()
        self.supplier_combo.setFixedHeight(36)
        self._load_suppliers()

        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 999999)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setPrefix("GHS ")
        self.cost_spin.setFixedHeight(36)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("GHS ")
        self.price_spin.setFixedHeight(36)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0, 999999)
        self.qty_spin.setDecimals(0)
        self.qty_spin.setFixedHeight(36)

        self.min_qty_spin = QDoubleSpinBox()
        self.min_qty_spin.setRange(0, 999999)
        self.min_qty_spin.setDecimals(0)
        self.min_qty_spin.setValue(5)
        self.min_qty_spin.setFixedHeight(36)

        self.desc_input = QTextEdit()
        self.desc_input.setFixedHeight(72)
        self.desc_input.setPlaceholderText("Optional description")

        form.addRow("Barcode *", self.barcode_input)
        form.addRow("Product Name *", self.name_input)
        form.addRow("Category", self.category_combo)
        form.addRow("Supplier", self.supplier_combo)
        form.addRow("Cost Price *", self.cost_spin)
        form.addRow("Selling Price *", self.price_spin)
        form.addRow("Initial Stock", self.qty_spin)
        form.addRow("Min Stock", self.min_qty_spin)
        form.addRow("Description", self.desc_input)

        layout.addLayout(form)

        # Disable price editing for non-admins
        if not current_session.has_permission("price_change"):
            self.price_spin.setEnabled(False)
            self.cost_spin.setEnabled(False)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setStyleSheet("""
            QPushButton { background: #2563EB; color: white; border-radius: 7px;
                          padding: 8px 20px; font-weight: 600; }
            QPushButton:hover { background: #1D4ED8; }
        """)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_categories(self):
        self.category_combo.addItem("— Select Category —", None)
        with get_session() as session:
            cats = session.query(Category).filter_by(is_deleted=False).all()
            for c in cats:
                self.category_combo.addItem(c.name, c.id)

    def _load_suppliers(self):
        self.supplier_combo.addItem("— Select Supplier —", None)
        with get_session() as session:
            sups = session.query(Supplier).filter_by(is_deleted=False).all()
            for s in sups:
                self.supplier_combo.addItem(s.supplier_name, s.id)

    def _populate(self):
        p = self.product
        self.barcode_input.setText(p.barcode)
        self.name_input.setText(p.product_name)
        self.cost_spin.setValue(p.cost_price)
        self.price_spin.setValue(p.selling_price)
        self.qty_spin.setValue(p.quantity)
        self.min_qty_spin.setValue(p.minimum_quantity)
        self.desc_input.setText(p.description or "")
        # Set category
        idx = self.category_combo.findData(p.category_id)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        idx = self.supplier_combo.findData(p.supplier_id)
        if idx >= 0:
            self.supplier_combo.setCurrentIndex(idx)
        # Disable barcode editing
        self.barcode_input.setEnabled(False)
        self.qty_spin.setEnabled(False)  # use inventory module to change stock

    def _save(self):
        barcode = self.barcode_input.text().strip()
        name    = self.name_input.text().strip()

        if not barcode:
            QMessageBox.warning(self, "Validation", "Barcode is required.")
            return
        if not name:
            QMessageBox.warning(self, "Validation", "Product name is required.")
            return
        if self.price_spin.value() <= 0:
            QMessageBox.warning(self, "Validation", "Selling price must be greater than 0.")
            return

        with get_session() as session:
            if self.product is None:
                # Check unique barcode
                existing = session.query(Product).filter_by(barcode=barcode).first()
                if existing:
                    QMessageBox.warning(self, "Duplicate", f"Barcode '{barcode}' already exists.")
                    return

                p = Product(
                    barcode=barcode,
                    product_name=name,
                    category_id=self.category_combo.currentData(),
                    supplier_id=self.supplier_combo.currentData(),
                    cost_price=self.cost_spin.value(),
                    selling_price=self.price_spin.value(),
                    quantity=self.qty_spin.value(),
                    minimum_quantity=self.min_qty_spin.value(),
                    description=self.desc_input.toPlainText(),
                )
                session.add(p)
                session.flush()

                # Create stock-in transaction for initial stock
                if self.qty_spin.value() > 0:
                    InventoryService.stock_in(
                        p.id, self.qty_spin.value(),
                        reference="INITIAL-STOCK",
                        notes="Initial stock on product creation",
                    )
            else:
                p = session.get(Product, self.product.id)
                if p:
                    p.product_name    = name
                    p.category_id     = self.category_combo.currentData()
                    p.supplier_id     = self.supplier_combo.currentData()
                    p.cost_price      = self.cost_spin.value()
                    p.selling_price   = self.price_spin.value()
                    p.minimum_quantity = self.min_qty_spin.value()
                    p.description     = self.desc_input.toPlainText()

        self.accept()


class ProductsWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_products = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Toolbar ────────────────────────────────────────────────────
        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by name or barcode…")
        self.search_input.setFixedHeight(38)
        self.search_input.setMaximumWidth(340)
        self.search_input.textChanged.connect(self._filter_products)

        self.cat_filter = QComboBox()
        self.cat_filter.setFixedHeight(38)
        self.cat_filter.setFixedWidth(180)
        self.cat_filter.currentIndexChanged.connect(self._filter_products)

        add_btn = QPushButton("+ Add Product")
        add_btn.setFixedHeight(38)
        add_btn.clicked.connect(self._add_product)

        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.cat_filter)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        # Stats row
        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        layout.addWidget(self.stats_lbl)

        # ── Table ──────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Barcode", "Product Name", "Category",
            "Cost", "Price", "Stock", "Min Stock", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)

    def refresh(self):
        self._load_categories()
        self._load_products()

    def _load_categories(self):
        self.cat_filter.blockSignals(True)
        self.cat_filter.clear()
        self.cat_filter.addItem("All Categories", None)
        with get_session() as session:
            cats = session.query(Category).filter_by(is_deleted=False).order_by(Category.name).all()
            for c in cats:
                self.cat_filter.addItem(c.name, c.id)
        self.cat_filter.blockSignals(False)

    def _load_products(self):
        with get_session() as session:
            self._all_products = (
                session.query(Product)
                .filter_by(is_deleted=False)
                .order_by(Product.product_name)
                .all()
            )
        self._filter_products()

    def _filter_products(self):
        search = self.search_input.text().strip().lower()
        cat_id = self.cat_filter.currentData()

        filtered = []
        for p in self._all_products:
            if cat_id and p.category_id != cat_id:
                continue
            if search and search not in p.product_name.lower() and search not in p.barcode.lower():
                continue
            filtered.append(p)

        self._populate_table(filtered)
        total_val = sum(p.cost_price * p.quantity for p in filtered)
        self.stats_lbl.setText(
            f"{len(filtered)} products  •  Stock value: {format_currency(total_val)}"
        )

    def _populate_table(self, products):
        self.table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(p.barcode))
            self.table.setItem(row, 1, QTableWidgetItem(p.product_name))

            cat_name = p.category.name if p.category else "—"
            self.table.setItem(row, 2, QTableWidgetItem(cat_name))
            self.table.setItem(row, 3, QTableWidgetItem(format_currency(p.cost_price)))
            self.table.setItem(row, 4, QTableWidgetItem(format_currency(p.selling_price)))

            # Stock with color indicator
            stock_item = QTableWidgetItem(f"{p.quantity:.0f}")
            stock_item.setTextAlignment(Qt.AlignCenter)
            if p.quantity == 0:
                stock_item.setForeground(QColor("#DC2626"))
                stock_item.setText(f"{p.quantity:.0f} ⚠️")
            elif p.quantity <= p.minimum_quantity:
                stock_item.setForeground(QColor("#D97706"))
            else:
                stock_item.setForeground(QColor("#16A34A"))
            self.table.setItem(row, 5, stock_item)

            min_item = QTableWidgetItem(f"{p.minimum_quantity:.0f}")
            min_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, min_item)

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(6)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedHeight(28)
            edit_btn.setFixedWidth(56)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: #DBEAFE; color: #1D4ED8;
                    border-radius: 5px; font-size: 11px; font-weight: 600; border: none;
                }
                QPushButton:hover { background: #BFDBFE; }
            """)
            edit_btn.clicked.connect(lambda _, pid=p.id: self._edit_product(pid))

            del_btn = QPushButton("Delete")
            del_btn.setFixedHeight(28)
            del_btn.setFixedWidth(60)
            del_btn.setStyleSheet("""
                QPushButton {
                    background: #FEE2E2; color: #DC2626;
                    border-radius: 5px; font-size: 11px; font-weight: 600; border: none;
                }
                QPushButton:hover { background: #FECACA; }
            """)
            del_btn.clicked.connect(lambda _, pid=p.id: self._delete_product(pid))

            action_layout.addWidget(edit_btn)
            action_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 7, action_widget)

        self.table.resizeRowsToContents()

    def _add_product(self):
        dlg = ProductDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()

    def _edit_product(self, product_id: int):
        with get_session() as session:
            p = session.get(Product, product_id)
        dlg = ProductDialog(product=p, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()

    def _delete_product(self, product_id: int):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this product?\n"
            "It will be archived and hidden from the system.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            with get_session() as session:
                p = session.get(Product, product_id)
                if p:
                    p.is_deleted = True
            self.refresh()
