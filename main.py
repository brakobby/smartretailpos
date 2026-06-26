"""
SmartRetail POS - Main Entry Point
A simple, robust Point of Sale and Inventory Management System
"""
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.database import init_db, create_default_admin
from app.ui.login import LoginWindow


def main():
    """Application entry point"""
    # Initialize database
    print("Initializing database...")
    init_db()
    create_default_admin()
    print("Database ready!")
    
    # Start Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("SmartRetail POS")
    app.setStyle("Fusion")  # Modern look
    
    # Apply basic stylesheet for the whole app
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QPushButton {
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background: white;
        }
        QTableWidget {
            gridline-color: #e0e0e0;
            background-color: white;
            alternate-background-color: #f9f9f9;
        }
        QHeaderView::section {
            background-color: #34495e;
            color: white;
            padding: 8px;
            border: none;
        }
    """)
    
    # Show login window
    login = LoginWindow()
    if login.exec() == LoginWindow.Accepted:
        # Start main application if login successful
        from app.ui.main_window import MainWindow
        window = MainWindow(login.user_data)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()