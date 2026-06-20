"""
SmartRetail POS — Application Entry Point

Startup sequence:
  1. Configure logging
  2. Initialise the database (create tables + seed data)
  3. Show the Login window
  4. On successful login → show the Main window
  5. On logout → return to Login window
"""

import logging
import sys
from pathlib import Path

# ── Add project root to sys.path so imports work when run directly ────────────
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Logging configuration ─────────────────────────────────────────────────────
from app.config.settings import LOG_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "smartretail.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
    from PySide6.QtCore import Qt

    # ── Create Qt application ─────────────────────────────────────────────
    app = QApplication(sys.argv)
    app.setApplicationName("SmartRetail POS")
    app.setOrganizationName("SmartRetail Systems")
    app.setApplicationVersion("1.0.0")

    # High-DPI support
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # ── Initialise database ───────────────────────────────────────────────
    logger.info("Starting SmartRetail POS…")
    try:
        from app.database.database import init_db
        init_db()
        logger.info("Database initialised successfully.")
    except Exception as e:
        logger.critical("Database initialisation failed: %s", e, exc_info=True)
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None, "Startup Error",
            f"Failed to initialise the database:\n\n{e}\n\n"
            "Please check that the data directory is writable."
        )
        return 1

    # ── Apply global stylesheet ───────────────────────────────────────────
    from app.ui.theme import get_stylesheet
    app.setStyleSheet(get_stylesheet("light"))

    # ── State: current windows ────────────────────────────────────────────
    login_window = None
    main_window  = None

    def show_login():
        nonlocal login_window, main_window

        # Close main window if open
        if main_window is not None:
            main_window.close()
            main_window = None

        from app.ui.windows.login_window import LoginWindow
        login_window = LoginWindow()
        login_window.login_successful.connect(show_main)
        login_window.show()

    def show_main():
        nonlocal login_window, main_window

        # Close login window
        if login_window is not None:
            login_window.close()

        from app.ui.windows.main_window import MainWindow
        main_window = MainWindow()
        main_window.logout_requested.connect(show_login)
        main_window.show()

    # ── Start with login ──────────────────────────────────────────────────
    show_login()

    logger.info("Application event loop started.")
    exit_code = app.exec()
    logger.info("Application exited with code %d.", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
