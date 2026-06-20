"""SmartRetail POS — Settings Window"""
from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QFormLayout, QComboBox, QDialog, QDialogButtonBox,
    QCheckBox,
)

from app.config.settings import (
    BACKUP_DIR, DATABASE_PATH, ALL_ROLES,
    APP_NAME, APP_VERSION,
)
from app.database.database import get_session
from app.database.models import User, Role, AuditLog, UserStatus
from app.services.auth_service import AuthService
from app.utils.helpers import format_datetime
from app.utils.session import current_session


class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New User"); self.setMinimumWidth(400); self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(14)
        title = QLabel("Add New User")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        form = QFormLayout(); form.setSpacing(12)
        self.username_input = QLineEdit(); self.username_input.setFixedHeight(36)
        self.fullname_input = QLineEdit(); self.fullname_input.setFixedHeight(36)
        self.password_input = QLineEdit(); self.password_input.setEchoMode(QLineEdit.Password); self.password_input.setFixedHeight(36)
        self.role_combo = QComboBox(); self.role_combo.setFixedHeight(36)
        for role in ALL_ROLES:
            self.role_combo.addItem(role)

        form.addRow("Username *", self.username_input)
        form.addRow("Full Name *", self.fullname_input)
        form.addRow("Password *", self.password_input)
        form.addRow("Role *", self.role_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        username  = self.username_input.text().strip()
        fullname  = self.fullname_input.text().strip()
        password  = self.password_input.text()
        role_name = self.role_combo.currentText()

        if not username or not fullname or not password:
            QMessageBox.warning(self, "Validation", "All fields are required."); return
        if len(password) < 6:
            QMessageBox.warning(self, "Validation", "Password must be at least 6 characters."); return
        try:
            AuthService.create_user(username, password, fullname, role_name)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(16)

        tabs = QTabWidget()

        # ── Backup Tab ────────────────────────────────────────────────
        backup_tab = QWidget()
        bt = QVBoxLayout(backup_tab); bt.setContentsMargins(20, 20, 20, 20); bt.setSpacing(16)

        bt.addWidget(self._section_title("💾  Database Backup & Restore"))

        info_lbl = QLabel(
            f"Database location: {DATABASE_PATH}\n"
            f"Backup folder: {BACKUP_DIR}"
        )
        info_lbl.setStyleSheet("font-size: 12px; color: #64748B; background: #F8FAFC; "
                               "border-radius: 8px; padding: 12px;")
        info_lbl.setWordWrap(True)
        bt.addWidget(info_lbl)

        btn_row = QHBoxLayout()
        backup_btn = QPushButton("📦  Create Backup Now")
        backup_btn.setFixedHeight(42)
        backup_btn.clicked.connect(self._create_backup)
        restore_btn = QPushButton("📂  Restore from Backup")
        restore_btn.setFixedHeight(42)
        restore_btn.setStyleSheet("QPushButton{background:#FEF3C7;color:#D97706;border:none;border-radius:8px;padding:0 16px;font-weight:600;}QPushButton:hover{background:#FDE68A;}")
        restore_btn.clicked.connect(self._restore_backup)
        btn_row.addWidget(backup_btn); btn_row.addWidget(restore_btn); btn_row.addStretch()
        bt.addLayout(btn_row)

        bt.addWidget(self._section_title("Recent Backups"))
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(3)
        self.backup_table.setHorizontalHeaderLabels(["Filename", "Size", "Created"])
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.backup_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.backup_table.setAlternatingRowColors(True)
        self.backup_table.verticalHeader().setVisible(False)
        bt.addWidget(self.backup_table)
        tabs.addTab(backup_tab, "💾 Backup")

        # ── Users Tab ─────────────────────────────────────────────────
        users_tab = QWidget()
        ut = QVBoxLayout(users_tab); ut.setContentsMargins(20, 20, 20, 20); ut.setSpacing(14)
        ut.addWidget(self._section_title("👥  User Management"))

        user_toolbar = QHBoxLayout()
        add_user_btn = QPushButton("+ Add User"); add_user_btn.setFixedHeight(36)
        add_user_btn.clicked.connect(self._add_user)
        user_toolbar.addStretch(); user_toolbar.addWidget(add_user_btn)
        ut.addLayout(user_toolbar)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["Username", "Full Name", "Role", "Status", "Last Login"])
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.verticalHeader().setVisible(False)
        ut.addWidget(self.users_table)
        tabs.addTab(users_tab, "👥 Users")

        # ── Audit Log Tab ─────────────────────────────────────────────
        audit_tab = QWidget()
        al = QVBoxLayout(audit_tab); al.setContentsMargins(20, 20, 20, 20); al.setSpacing(14)
        al.addWidget(self._section_title("📋  Audit Log"))
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(4)
        self.audit_table.setHorizontalHeaderLabels(["Timestamp", "User", "Action", "Details"])
        self.audit_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.audit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.audit_table.setAlternatingRowColors(True)
        self.audit_table.verticalHeader().setVisible(False)
        al.addWidget(self.audit_table)
        tabs.addTab(audit_tab, "📋 Audit Log")

        # ── About Tab ─────────────────────────────────────────────────
        about_tab = QWidget()
        abt = QVBoxLayout(about_tab); abt.setContentsMargins(40, 40, 40, 40); abt.setSpacing(12)
        abt.addStretch()
        logo = QLabel("🛒"); logo.setAlignment(Qt.AlignCenter); logo.setStyleSheet("font-size: 64px;")
        abt.addWidget(logo)
        app_name = QLabel(APP_NAME); app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet("font-size: 24px; font-weight: 700; color: #0F172A;")
        abt.addWidget(app_name)
        ver = QLabel(f"Version {APP_VERSION}"); ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("font-size: 14px; color: #64748B;")
        abt.addWidget(ver)
        desc = QLabel("Offline Inventory, POS & Business Management System\nBuilt with Python · PySide6 · SQLAlchemy")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #94A3B8; line-height: 1.6;")
        abt.addWidget(desc)
        abt.addStretch()
        tabs.addTab(about_tab, "ℹ️ About")

        layout.addWidget(tabs)
        self._tabs = tabs

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A; padding-bottom: 4px;")
        return lbl

    def refresh(self):
        self._load_backups()
        self._load_users()
        self._load_audit()

    # ── Backup ─────────────────────────────────────────────────────────

    def _create_backup(self):
        try:
            timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
            dest = BACKUP_DIR / f"backup_{timestamp}.db"
            shutil.copy2(DATABASE_PATH, dest)
            QMessageBox.information(self, "Backup Created",
                                    f"Backup saved to:\n{dest}")
            self._load_backups()
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", str(e))

    def _restore_backup(self):
        if not current_session.is_admin():
            QMessageBox.warning(self, "Permission Denied", "Only administrators can restore backups.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", str(BACKUP_DIR), "SQLite DB (*.db)"
        )
        if not path:
            return
        reply = QMessageBox.warning(
            self, "⚠️ Confirm Restore",
            "Restoring will REPLACE the current database!\n"
            "All unsaved changes will be lost.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            # Create a safety backup first
            safety = BACKUP_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(DATABASE_PATH, safety)
            shutil.copy2(path, DATABASE_PATH)
            QMessageBox.information(
                self, "Restore Complete",
                f"Database restored from:\n{path}\n\n"
                f"Safety backup saved to:\n{safety}\n\n"
                "Please restart the application."
            )
        except Exception as e:
            QMessageBox.critical(self, "Restore Failed", str(e))

    def _load_backups(self):
        backups = sorted(BACKUP_DIR.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
        self.backup_table.setRowCount(len(backups))
        for row, f in enumerate(backups):
            stat = f.stat()
            self.backup_table.setItem(row, 0, QTableWidgetItem(f.name))
            size_kb = stat.st_size / 1024
            self.backup_table.setItem(row, 1, QTableWidgetItem(f"{size_kb:.1f} KB"))
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.backup_table.setItem(row, 2, QTableWidgetItem(mtime))

    # ── Users ──────────────────────────────────────────────────────────

    def _add_user(self):
        if not current_session.is_admin():
            QMessageBox.warning(self, "Permission Denied", "Only administrators can add users.")
            return
        dlg = AddUserDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._load_users()

    def _load_users(self):
        with get_session() as session:
            users = session.query(User).join(Role).all()
        self.users_table.setRowCount(len(users))
        for row, u in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(u.username))
            self.users_table.setItem(row, 1, QTableWidgetItem(u.full_name))
            self.users_table.setItem(row, 2, QTableWidgetItem(u.role.role_name if u.role else "—"))
            status_item = QTableWidgetItem(u.status.value)
            status_item.setTextAlignment(Qt.AlignCenter)
            if u.status == UserStatus.ACTIVE:
                from PySide6.QtGui import QColor
                status_item.setForeground(QColor("#16A34A"))
            else:
                from PySide6.QtGui import QColor
                status_item.setForeground(QColor("#DC2626"))
            self.users_table.setItem(row, 3, status_item)
            login_str = format_datetime(u.last_login) if u.last_login else "Never"
            self.users_table.setItem(row, 4, QTableWidgetItem(login_str))

    # ── Audit Log ──────────────────────────────────────────────────────

    def _load_audit(self):
        with get_session() as session:
            logs = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(500).all()
        self.audit_table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.audit_table.setItem(row, 0, QTableWidgetItem(format_datetime(log.timestamp)))
            user_str = log.user.username if log.user else "System"
            self.audit_table.setItem(row, 1, QTableWidgetItem(user_str))
            self.audit_table.setItem(row, 2, QTableWidgetItem(log.action))
            self.audit_table.setItem(row, 3, QTableWidgetItem(log.details or ""))
