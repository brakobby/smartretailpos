# SmartRetail POS & Inventory Management System

> A complete offline retail management system — POS, Inventory, Suppliers, Customer Credit, Reports, and Backup — built with Python, PySide6, and SQLite.

---

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Default Credentials](#default-credentials)
- [Module Guide](#module-guide)
- [Business Rules](#business-rules)
- [Running Tests](#running-tests)
- [Packaging with PyInstaller](#packaging-with-pyinstaller)
- [Architecture Overview](#architecture-overview)

---

## ✨ Features

| Module | Features |
|--------|----------|
| **Authentication** | Login, role-based access, password hashing (bcrypt), session management |
| **Dashboard** | Today's/monthly sales, profit, stock value, debt KPIs, 7-day sales chart, low-stock alerts |
| **Products** | Add/edit/delete, barcode lookup, category & supplier linking, stock indicators |
| **Inventory** | Stock In / Stock Out / Adjust, full transaction history with audit trail |
| **POS** | Barcode scanning, shopping cart, cash/credit/mobile money/mixed payments, F-key shortcuts |
| **Customers** | Customer registration, credit sales, installment tracking, outstanding balances |
| **Suppliers** | Supplier records, purchase orders, debt tracking, payment recording |
| **Reports** | Sales, profit, inventory, date-range filtering, Excel export, PDF generation |
| **Expenses** | Categorised expense tracking, totals, search |
| **Settings** | User management, backup/restore, audit log, about |

---

## 🛠 Technology Stack

```
Language:     Python 3.12+
UI:           PySide6 (Qt6)
Database:     SQLite (WAL mode)
ORM:          SQLAlchemy 2.x
Reports:      ReportLab (PDF) + OpenPyXL (Excel)
Charts:       Matplotlib (embedded in Qt)
Printing:     python-escpos (ESC/POS thermal)
Auth:         bcrypt
Packaging:    PyInstaller
```

---

## 📁 Project Structure

```
SmartRetailPOS/
│
├── main.py                        ← Application entry point
├── requirements.txt
├── README.md
│
├── app/
│   ├── config/
│   │   └── settings.py            ← All constants, paths, permissions
│   │
│   ├── database/
│   │   ├── database.py            ← Engine, session factory, init_db()
│   │   └── models/
│   │       └── models.py          ← All SQLAlchemy ORM models
│   │
│   ├── services/                  ← Business logic (no UI, no raw SQL)
│   │   ├── auth_service.py        ← Login, user management
│   │   ├── inventory_service.py   ← Stock movements, audit trail
│   │   └── sales_service.py       ← POS transactions, cart, credit
│   │
│   ├── ui/
│   │   ├── theme.py               ← Qt stylesheet (light/dark)
│   │   └── windows/
│   │       ├── login_window.py
│   │       ├── main_window.py     ← Shell + sidebar navigation
│   │       ├── dashboard_window.py
│   │       ├── products_window.py
│   │       ├── inventory_window.py
│   │       ├── pos_window.py
│   │       ├── customers_window.py
│   │       ├── suppliers_window.py
│   │       ├── reports_window.py
│   │       ├── expenses_window.py
│   │       └── settings_window.py
│   │
│   ├── reports/
│   │   └── pdf_reports.py         ← ReportLab PDF generation
│   │
│   ├── printing/
│   │   └── receipt_printer.py     ← ESC/POS + text fallback
│   │
│   └── utils/
│       ├── helpers.py             ← Formatting, ID generation, hashing
│       └── session.py             ← Current user session singleton
│
├── data/                          ← Created at runtime (gitignore this)
│   └── smartretail.db
│
├── backups/                       ← Backup .db files
├── reports_output/                ← Generated PDFs and Excel files
├── logs/                          ← Application logs
│
└── tests/
    └── test_core.py               ← Unit tests (pytest)
```

---

## 🚀 Quick Start

### 1. Install Python dependencies

```bash
cd SmartRetailPOS
pip install -r requirements.txt
```

> **On Linux**, if you see `externally-managed-environment`:
> ```bash
> pip install -r requirements.txt --break-system-packages
> ```

### 2. Run the application

```bash
python main.py
```

The database is created automatically on first run at `data/smartretail.db`.

---

## 🔑 Default Credentials

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Administrator |

> ⚠️ **Change the admin password immediately** after first login via Settings → Users.

---

## 📖 Module Guide

### POS Window

| Action | Keyboard |
|--------|----------|
| New Sale | `F1` |
| Focus barcode/search | `F2` |
| Open payment dialog | `F3` |
| Reprint last receipt | `F4` |

1. Scan or type a barcode → product is added to cart
2. Or type a product name → pick from the search list
3. Press **F3** or click **Process Payment**
4. Choose payment type, enter amount, confirm

### Credit Sales

1. In the Payment dialog, select **Credit** or **Mixed**
2. Select a registered customer (required)
3. Enter the amount paid now
4. The system creates a **Credit Account** for the balance
5. Go to **Customers → Credit Accounts** to record installment payments

### Inventory

- **Stock In**: receive goods from a supplier
- **Stock Out**: remove items (damaged, expired, etc.)
- **Adjust**: correct the stock level after a physical count

Every movement is logged in the **Transaction History** with the user, time, and balance after.

### Backup & Restore

- Go to **Settings → Backup**
- Click **Create Backup Now** → saved as `backup_YYYY_MM_DD_HHMMSS.db`
- To restore: click **Restore from Backup**, select a file
- A safety backup is automatically created before any restore

---

## ⚖️ Business Rules

1. **No negative stock** — the system blocks sales/stock-out that would go below zero
2. **Price changes** — only Administrators can edit cost/selling prices
3. **Credit sales** — require a registered customer record
4. **Soft deletes** — products, customers, suppliers are archived, never hard-deleted
5. **Audit trail** — every important action (login, sale, stock change) is logged with user + timestamp
6. **Unique invoices** — every sale and purchase order gets a unique timestamped invoice number

---

## 🧪 Running Tests

```bash
# From the project root
python -m pytest tests/ -v

# With coverage (if pytest-cov is installed)
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

Tests use an **in-memory SQLite database** and do not touch `data/smartretail.db`.

---

## 📦 Packaging with PyInstaller

```bash
pyinstaller --onefile --windowed --name SmartRetailPOS \
  --add-data "app:app" \
  main.py
```

The executable is created in `dist/SmartRetailPOS`.

For Windows, add `--icon=app/assets/icon.ico` to set the application icon.

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    PySide6 UI Layer                  │
│   LoginWindow → MainWindow → [Module Windows]        │
└───────────────────────┬─────────────────────────────┘
                        │ calls
┌───────────────────────▼─────────────────────────────┐
│               Service Layer (Business Logic)         │
│   AuthService  |  InventoryService  |  SalesService  │
└───────────────────────┬─────────────────────────────┘
                        │ uses
┌───────────────────────▼─────────────────────────────┐
│             SQLAlchemy ORM + get_session()            │
│        (context manager — auto commit/rollback)      │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│              SQLite Database (WAL mode)               │
│                  data/smartretail.db                  │
└─────────────────────────────────────────────────────┘
```

**Data flow for a POS sale:**

```
User scans barcode
    → POSWindow._on_barcode_entered()
    → SalesService.find_product_by_barcode()    [reads DB]
    → CartItem added to cart list
    → User clicks Pay → PaymentDialog
    → SalesService.create_sale(cart_items, ...)
        → validates stock
        → writes Sale + SaleItems to DB
        → calls InventoryService.adjust_stock() per item
            → writes InventoryTransaction
        → writes AuditLog
        → commits transaction
    → UI shows success, receipt printed
```

---

## 📝 Customisation

Edit `app/config/settings.py` to change:

- `BUSINESS_NAME`, `BUSINESS_ADDRESS`, `BUSINESS_PHONE`
- `CURRENCY_SYMBOL` (default: `GHS`)
- `PRINTER_TYPE` (`"58mm"` or `"80mm"`)
- `TAX_ENABLED` / `TAX_RATE`
- `DEFAULT_LOW_STOCK_THRESHOLD`
- `AUTO_BACKUP_ENABLED` / `AUTO_BACKUP_INTERVAL_HOURS`

---

## 🖨 Thermal Printer Setup

1. Connect your ESC/POS USB printer
2. In `app/config/settings.py`, set `PRINTER_TYPE = "80mm"` or `"58mm"`
3. In `app/printing/receipt_printer.py`, call `receipt_printer.connect_usb(vendor_id, product_id)`
   - Common IDs: Epson TM-T20 → `(0x04b8, 0x0202)`
4. If no printer is connected, receipts are printed to the console (text fallback)

---

*Built with ❤️ for small retail businesses operating offline.*
