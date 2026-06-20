"""SmartRetail POS — Expenses Window"""
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QTextEdit,
    QDialogButtonBox, QMessageBox, QComboBox, QDateEdit,
)
from PySide6.QtCore import QDate
from app.database.database import get_session
from app.database.models import Expense
from app.utils.helpers import format_currency, format_datetime
from app.utils.session import current_session
from datetime import datetime

EXPENSE_CATEGORIES = [
    "Rent", "Utilities", "Salaries", "Transport", "Maintenance",
    "Supplies", "Marketing", "Miscellaneous",
]


class ExpenseDialog(QDialog):
    def __init__(self, expense: Expense = None, parent=None):
        super().__init__(parent)
        self.expense = expense
        self.setWindowTitle("Edit Expense" if expense else "Add Expense")
        self.setMinimumWidth(400); self.setModal(True)
        self._build_ui()
        if expense: self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(14)
        title = QLabel("Edit Expense" if self.expense else "Add Expense")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        form = QFormLayout(); form.setSpacing(12)

        self.category_combo = QComboBox(); self.category_combo.setFixedHeight(36)
        for cat in EXPENSE_CATEGORIES:
            self.category_combo.addItem(cat)
        self.category_combo.setEditable(True)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 9999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("GHS ")
        self.amount_spin.setFixedHeight(36)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedHeight(36)

        self.desc_input = QTextEdit(); self.desc_input.setFixedHeight(80)
        self.desc_input.setPlaceholderText("Optional description…")

        form.addRow("Category *", self.category_combo)
        form.addRow("Amount *", self.amount_spin)
        form.addRow("Date", self.date_edit)
        form.addRow("Description", self.desc_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self):
        e = self.expense
        idx = self.category_combo.findText(e.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        else:
            self.category_combo.setCurrentText(e.category)
        self.amount_spin.setValue(e.amount)
        self.desc_input.setText(e.description or "")
        if e.date:
            d = e.date
            self.date_edit.setDate(QDate(d.year, d.month, d.day))

    def _save(self):
        category = self.category_combo.currentText().strip()
        amount   = self.amount_spin.value()
        d        = self.date_edit.date().toPython()
        dt       = datetime(d.year, d.month, d.day)

        if not category:
            QMessageBox.warning(self, "Validation", "Category is required."); return
        if amount <= 0:
            QMessageBox.warning(self, "Validation", "Amount must be greater than 0."); return

        with get_session() as session:
            if self.expense is None:
                exp = Expense(
                    category=category,
                    amount=amount,
                    date=dt,
                    description=self.desc_input.toPlainText(),
                    recorded_by=current_session.user_id,
                )
                session.add(exp)
            else:
                exp = session.get(Expense, self.expense.id)
                if exp:
                    exp.category    = category
                    exp.amount      = amount
                    exp.date        = dt
                    exp.description = self.desc_input.toPlainText()
        self.accept()


class ExpensesWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_expenses = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search expenses…")
        self.search_input.setFixedHeight(38); self.search_input.setMaximumWidth(280)
        self.search_input.textChanged.connect(self._filter)

        self.cat_filter = QComboBox(); self.cat_filter.setFixedHeight(38); self.cat_filter.setFixedWidth(180)
        self.cat_filter.addItem("All Categories")
        for cat in EXPENSE_CATEGORIES:
            self.cat_filter.addItem(cat)
        self.cat_filter.currentIndexChanged.connect(self._filter)

        add_btn = QPushButton("+ Add Expense"); add_btn.setFixedHeight(38)
        add_btn.clicked.connect(self._add_expense)

        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.cat_filter)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        # Summary label
        self.summary_lbl = QLabel()
        self.summary_lbl.setStyleSheet("font-size: 13px; color: #64748B; font-weight: 500;")
        layout.addWidget(self.summary_lbl)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Category", "Amount", "Date", "Description", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)

    def refresh(self):
        self._load_expenses()

    def _load_expenses(self):
        with get_session() as session:
            self._all_expenses = (
                session.query(Expense)
                .filter_by(is_deleted=False)
                .order_by(Expense.date.desc())
                .all()
            )
        self._filter()

    def _filter(self):
        search  = self.search_input.text().strip().lower() if hasattr(self, 'search_input') else ""
        cat_sel = self.cat_filter.currentText() if hasattr(self, 'cat_filter') else "All Categories"

        filtered = []
        for e in self._all_expenses:
            if cat_sel != "All Categories" and e.category != cat_sel:
                continue
            if search and search not in e.category.lower() and search not in (e.description or "").lower():
                continue
            filtered.append(e)

        total = sum(e.amount for e in filtered)
        self.summary_lbl.setText(
            f"{len(filtered)} expense(s)  •  Total: {format_currency(total)}"
        )

        self.table.setRowCount(len(filtered))
        for row, e in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(e.category))
            amt_item = QTableWidgetItem(format_currency(e.amount))
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, amt_item)
            self.table.setItem(row, 2, QTableWidgetItem(format_datetime(e.date)[:10]))
            self.table.setItem(row, 3, QTableWidgetItem(e.description or "—"))

            action_widget = QWidget()
            al = QHBoxLayout(action_widget); al.setContentsMargins(4, 2, 4, 2); al.setSpacing(6)

            edit_btn = QPushButton("Edit"); edit_btn.setFixedHeight(28); edit_btn.setFixedWidth(52)
            edit_btn.setStyleSheet("QPushButton{background:#DBEAFE;color:#1D4ED8;border:none;border-radius:5px;font-size:11px;font-weight:600;}QPushButton:hover{background:#BFDBFE;}")
            edit_btn.clicked.connect(lambda _, eid=e.id: self._edit_expense(eid))

            del_btn = QPushButton("Del"); del_btn.setFixedHeight(28); del_btn.setFixedWidth(44)
            del_btn.setStyleSheet("QPushButton{background:#FEE2E2;color:#DC2626;border:none;border-radius:5px;font-size:11px;font-weight:600;}QPushButton:hover{background:#FECACA;}")
            del_btn.clicked.connect(lambda _, eid=e.id: self._delete_expense(eid))

            al.addWidget(edit_btn); al.addWidget(del_btn)
            self.table.setCellWidget(row, 4, action_widget)

    def _add_expense(self):
        dlg = ExpenseDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()

    def _edit_expense(self, expense_id: int):
        with get_session() as session:
            e = session.get(Expense, expense_id)
        dlg = ExpenseDialog(expense=e, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()

    def _delete_expense(self, expense_id: int):
        reply = QMessageBox.question(
            self, "Delete Expense", "Delete this expense record?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with get_session() as session:
                e = session.get(Expense, expense_id)
                if e: e.is_deleted = True
            self.refresh()
