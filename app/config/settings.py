"""
SmartRetail POS - Application Configuration
All constants, paths, and settings are centralized here.
"""

import os
from pathlib import Path

# ── Base Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
ASSETS_DIR = BASE_DIR / "app" / "assets"
REPORTS_DIR = BASE_DIR / "reports_output"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist at import time
for _dir in [DATA_DIR, BACKUP_DIR, ASSETS_DIR, REPORTS_DIR, LOG_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_PATH = DATA_DIR / "smartretail.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ── Application Metadata ──────────────────────────────────────────────────────
APP_NAME = "SmartRetail POS"
APP_VERSION = "1.0.0"
APP_AUTHOR = "SmartRetail Systems"
CURRENCY_SYMBOL = "GHS"
CURRENCY_CODE = "GHS"

# ── Business Settings (editable by admin) ────────────────────────────────────
BUSINESS_NAME = "My Retail Shop"
BUSINESS_ADDRESS = "123 Market Street, Accra, Ghana"
BUSINESS_PHONE = "+233 20 000 0000"
BUSINESS_EMAIL = "shop@example.com"
BUSINESS_TIN = ""  # Tax Identification Number

# ── Receipt Settings ──────────────────────────────────────────────────────────
RECEIPT_WIDTH_58MM = 32   # characters per line for 58mm printer
RECEIPT_WIDTH_80MM = 48   # characters per line for 80mm printer
DEFAULT_RECEIPT_WIDTH = RECEIPT_WIDTH_80MM
PRINTER_TYPE = "80mm"     # "58mm" or "80mm"

# ── Inventory Rules ───────────────────────────────────────────────────────────
ALLOW_NEGATIVE_STOCK = False
DEFAULT_LOW_STOCK_THRESHOLD = 5

# ── Tax ───────────────────────────────────────────────────────────────────────
TAX_ENABLED = False
TAX_RATE = 0.0  # e.g. 0.125 for 12.5%
TAX_LABEL = "VAT"

# ── Session ───────────────────────────────────────────────────────────────────
SESSION_TIMEOUT_MINUTES = 60

# ── Backup ───────────────────────────────────────────────────────────────────
AUTO_BACKUP_ENABLED = True
AUTO_BACKUP_INTERVAL_HOURS = 24
MAX_BACKUP_FILES = 30  # Keep last 30 backups

# ── Roles ─────────────────────────────────────────────────────────────────────
ROLE_ADMIN = "Administrator"
ROLE_MANAGER = "Manager"
ROLE_CASHIER = "Cashier"
ROLE_STOREKEEPER = "Storekeeper"

ALL_ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER, ROLE_STOREKEEPER]

# ── Permissions map: role -> list of allowed module keys ─────────────────────
PERMISSIONS = {
    ROLE_ADMIN: [
        "dashboard", "products", "inventory", "pos", "customers",
        "suppliers", "reports", "expenses", "backup", "settings", "users",
        "price_change",
    ],
    ROLE_MANAGER: [
        "dashboard", "products", "inventory", "pos", "customers",
        "suppliers", "reports", "expenses",
    ],
    ROLE_CASHIER: [
        "dashboard", "pos", "customers",
    ],
    ROLE_STOREKEEPER: [
        "dashboard", "products", "inventory", "suppliers",
    ],
}

# ── UI Theme ──────────────────────────────────────────────────────────────────
THEME_DEFAULT = "light"  # "light" or "dark"
SIDEBAR_WIDTH = 220
HEADER_HEIGHT = 60

# ── Date / Time Formats ───────────────────────────────────────────────────────
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DISPLAY_DATE_FORMAT = "%d %b %Y"
DISPLAY_DATETIME_FORMAT = "%d %b %Y %H:%M"

# ── Invoice prefix ────────────────────────────────────────────────────────────
INVOICE_PREFIX = "INV"
PURCHASE_PREFIX = "PO"
RECEIPT_PREFIX = "RCP"
