"""
SmartRetail POS — Login Window

A clean, professional login screen.
Emits login_successful signal on success so the main window can open.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QSizePolicy,
    QSpacerItem, QGraphicsDropShadowEffect, QApplication,
)
from PySide6.QtGui import QColor

from app.services.auth_service import AuthService
from app.config.settings import APP_NAME, APP_VERSION, BUSINESS_NAME


class LoginWindow(QWidget):
    """Standalone login screen displayed before the main application."""

    login_successful = Signal()   # Emitted on successful authentication

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Login")
        self.setMinimumSize(420, 560)
        self.setFixedSize(420, 560)
        self._build_ui()
        self._connect_signals()

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Full-height gradient background split: left brand / right form
        outer = QHBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Centre card
        card = QFrame()
        card.setObjectName("login_card")
        card.setStyleSheet("""
            QFrame#login_card {
                background: #FFFFFF;
                border-radius: 0px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 48, 48, 48)
        card_layout.setSpacing(0)

        # Logo / Brand
        brand_icon = QLabel("🛒")
        brand_icon.setAlignment(Qt.AlignCenter)
        brand_icon.setStyleSheet("font-size: 48px; margin-bottom: 4px;")

        app_label = QLabel(APP_NAME)
        app_label.setAlignment(Qt.AlignCenter)
        app_label.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #1E293B; margin-bottom: 2px;"
        )

        business_label = QLabel(BUSINESS_NAME)
        business_label.setAlignment(Qt.AlignCenter)
        business_label.setStyleSheet(
            "font-size: 13px; color: #64748B; margin-bottom: 32px;"
        )

        # Welcome text
        welcome = QLabel("Welcome back")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #0F172A; margin-bottom: 4px;"
        )

        subtitle = QLabel("Sign in to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 13px; color: #94A3B8; margin-bottom: 28px;"
        )

        # Error label (hidden by default)
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("""
            background: #FEE2E2;
            color: #DC2626;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 500;
        """)
        self.error_label.hide()

        # Username field
        lbl_user = QLabel("Username")
        lbl_user.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 4px;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setStyleSheet(self._input_style())
        self.username_input.setFixedHeight(44)

        # Password field
        lbl_pass = QLabel("Password")
        lbl_pass.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 4px; margin-top: 14px;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(self._input_style())
        self.password_input.setFixedHeight(44)

        # Show/hide password toggle
        show_pw_row = QHBoxLayout()
        show_pw_row.setContentsMargins(0, 6, 0, 0)
        self.show_pw_btn = QPushButton("Show password")
        self.show_pw_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #2563EB;
                border: none;
                font-size: 12px;
                padding: 0;
                font-weight: 500;
            }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.show_pw_btn.setCheckable(True)
        show_pw_row.addStretch()
        show_pw_row.addWidget(self.show_pw_btn)

        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setFixedHeight(46)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 9px;
                font-size: 14px;
                font-weight: 700;
                margin-top: 22px;
            }
            QPushButton:hover { background: #1D4ED8; }
            QPushButton:pressed { background: #1E40AF; }
            QPushButton:disabled { background: #93C5FD; }
        """)

        # Version footer
        version_lbl = QLabel(f"v{APP_VERSION}")
        version_lbl.setAlignment(Qt.AlignCenter)
        version_lbl.setStyleSheet(
            "font-size: 11px; color: #CBD5E1; margin-top: 28px;"
        )

        # Assemble
        card_layout.addWidget(brand_icon)
        card_layout.addWidget(app_label)
        card_layout.addWidget(business_label)
        card_layout.addWidget(welcome)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.error_label)
        card_layout.addWidget(lbl_user)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(lbl_pass)
        card_layout.addWidget(self.password_input)
        card_layout.addLayout(show_pw_row)
        card_layout.addWidget(self.login_btn)
        card_layout.addStretch()
        card_layout.addWidget(version_lbl)

        outer.addWidget(card)
        root.addLayout(outer)

    def _input_style(self) -> str:
        return """
            QLineEdit {
                background: #F8FAFC;
                border: 1.5px solid #E2E8F0;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 13px;
                color: #0F172A;
            }
            QLineEdit:focus {
                border-color: #2563EB;
                background: #FFFFFF;
            }
        """

    # ── Signals ────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self.login_btn.clicked.connect(self._attempt_login)
        self.username_input.returnPressed.connect(self._attempt_login)
        self.password_input.returnPressed.connect(self._attempt_login)
        self.show_pw_btn.toggled.connect(self._toggle_password_visibility)

    def _toggle_password_visibility(self, checked: bool):
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_pw_btn.setText("Hide password")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_pw_btn.setText("Show password")

    # ── Login Logic ────────────────────────────────────────────────────────

    def _attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        self.error_label.hide()

        if not username:
            self._show_error("Please enter your username.")
            self.username_input.setFocus()
            return

        if not password:
            self._show_error("Please enter your password.")
            self.password_input.setFocus()
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in…")
        QApplication.processEvents()

        try:
            user = AuthService.authenticate(username, password)
            if user:
                self.login_successful.emit()
            else:
                self._show_error("Invalid username or password.")
                self.password_input.clear()
                self.password_input.setFocus()
        except Exception as e:
            self._show_error(f"Login error: {e}")
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Sign In")

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()
