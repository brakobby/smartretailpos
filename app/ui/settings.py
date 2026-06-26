from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt


class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("System Settings")
        header.setStyleSheet("font-size: 22px; font-weight: 700; color: #f8fbff;")
        layout.addWidget(header)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #0f172b;
                border: 1px solid #24384f;
                border-radius: 14px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(8)

        card_layout.addWidget(QLabel("Application: Aurex Retail"))
        card_layout.addWidget(QLabel("Mode: Enterprise Desktop"))
        card_layout.addWidget(QLabel("Documents: Receipt + Invoice PDF output"))
        card_layout.addWidget(QLabel("Security: Local authentication and audit-ready workflows"))
        layout.addWidget(card)
