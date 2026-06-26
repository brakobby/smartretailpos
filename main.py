"""
SmartRetail POS - Main Entry Point
A simple, robust Point of Sale and Inventory Management System
"""
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

from app.database import init_db, create_default_admin
from app.ui.login import LoginWindow
from app.ui.theme import apply_global_theme


def main():
    """Application entry point"""
    # Initialize database
    print("Initializing database...")
    init_db()
    create_default_admin()
    print("Database ready!")
    
    # Start Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Aurex Retail")
    apply_global_theme(app)
    
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