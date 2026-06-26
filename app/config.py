"""
Application configuration and constants
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# Database
DATABASE_PATH = DATA_DIR / "smartretail.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Business settings
BUSINESS_NAME = "Smart Retail Shop"
BUSINESS_ADDRESS = "123 Main Street, Accra, Ghana"
BUSINESS_PHONE = "+233 50 123 4567"
CURRENCY = "GHS"
CURRENCY_SYMBOL = "₵"
TAX_RATE = 0.0  # 0% tax by default
LOW_STOCK_THRESHOLD = 10

# App settings
APP_NAME = "SmartRetail POS"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# User roles
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_CASHIER = "cashier"
ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER]

# Payment types
PAYMENT_CASH = "cash"
PAYMENT_CREDIT = "credit"
PAYMENT_MOBILE = "mobile_money"
PAYMENT_MIXED = "mixed"
PAYMENT_TYPES = [PAYMENT_CASH, PAYMENT_CREDIT, PAYMENT_MOBILE, PAYMENT_MIXED]

# Receipt settings
RECEIPT_WIDTH = 42  # characters for text receipt
ENABLE_THERMAL_PRINTER = False