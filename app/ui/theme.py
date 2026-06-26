from PySide6.QtWidgets import QApplication


def apply_global_theme(app: QApplication) -> None:
    """Apply a premium dark/futuristic visual theme to the application."""
    app.setStyle("Fusion")
    app.setStyleSheet("""
        * {
            font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif;
        }

        QWidget {
            color: #e5eefc;
            background-color: #07111f;
        }

        QMainWindow, QDialog {
            background-color: #07111f;
        }

        QFrame {
            border: none;
            background-color: transparent;
        }

        QLabel {
            color: #e5eefc;
            background: transparent;
        }

        QPushButton {
            background-color: #142338;
            color: #f8fbff;
            border: 1px solid #24384f;
            border-radius: 10px;
            padding: 10px 14px;
            font-weight: 600;
        }

        QPushButton:hover {
            background-color: #1f3550;
            border-color: #2f6fd8;
        }

        QPushButton:pressed {
            background-color: #0f1c2d;
        }

        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
            background-color: #0f172b;
            color: #f8fbff;
            border: 1px solid #24415d;
            border-radius: 10px;
            padding: 9px 12px;
        }

        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
            border: 1px solid #3b82f6;
        }

        QTableWidget {
            background-color: #0b1322;
            color: #e5eefc;
            border: 1px solid #24384f;
            border-radius: 12px;
            gridline-color: #1d2f46;
            alternate-background-color: #101b2d;
        }

        QHeaderView::section {
            background-color: #122036;
            color: #8fb2ff;
            padding: 10px;
            border: none;
            font-weight: 700;
        }

        QScrollArea {
            border: none;
            background: transparent;
        }
    """)
