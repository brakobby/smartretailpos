"""
SmartRetail POS — Theme / Stylesheet System

Provides:
  - get_stylesheet(mode)  → full Qt stylesheet string
  - COLORS dict for in-code color references
"""

COLORS_LIGHT = {
    "primary":        "#2563EB",   # Blue 600
    "primary_hover":  "#1D4ED8",   # Blue 700
    "primary_light":  "#DBEAFE",   # Blue 100
    "secondary":      "#64748B",   # Slate 500
    "success":        "#16A34A",   # Green 600
    "success_light":  "#DCFCE7",
    "warning":        "#D97706",   # Amber 600
    "warning_light":  "#FEF3C7",
    "danger":         "#DC2626",   # Red 600
    "danger_light":   "#FEE2E2",
    "bg_main":        "#F1F5F9",   # Slate 100
    "bg_card":        "#FFFFFF",
    "bg_sidebar":     "#1E293B",   # Slate 800
    "sidebar_text":   "#CBD5E1",   # Slate 300
    "sidebar_active": "#2563EB",
    "text_primary":   "#0F172A",   # Slate 900
    "text_secondary": "#64748B",
    "text_muted":     "#94A3B8",
    "border":         "#E2E8F0",
    "input_bg":       "#FFFFFF",
    "table_header":   "#F8FAFC",
    "table_row_alt":  "#F8FAFC",
    "scrollbar":      "#CBD5E1",
}

COLORS_DARK = {
    "primary":        "#3B82F6",
    "primary_hover":  "#2563EB",
    "primary_light":  "#1E3A5F",
    "secondary":      "#94A3B8",
    "success":        "#22C55E",
    "success_light":  "#14532D",
    "warning":        "#F59E0B",
    "warning_light":  "#451A03",
    "danger":         "#EF4444",
    "danger_light":   "#450A0A",
    "bg_main":        "#0F172A",
    "bg_card":        "#1E293B",
    "bg_sidebar":     "#0F172A",
    "sidebar_text":   "#CBD5E1",
    "sidebar_active": "#3B82F6",
    "text_primary":   "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted":     "#64748B",
    "border":         "#334155",
    "input_bg":       "#1E293B",
    "table_header":   "#1E293B",
    "table_row_alt":  "#0F172A",
    "scrollbar":      "#475569",
}

COLORS = COLORS_LIGHT  # Default; replaced by set_theme()


def get_stylesheet(mode: str = "light") -> str:
    c = COLORS_DARK if mode == "dark" else COLORS_LIGHT
    return f"""
/* ── Global ─────────────────────────────────────────────────────────── */
QWidget {{
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: {c['text_primary']};
    background-color: {c['bg_main']};
}}

/* ── Main Window ─────────────────────────────────────────────────────── */
QMainWindow {{
    background-color: {c['bg_main']};
}}

/* ── Cards / Panels ──────────────────────────────────────────────────── */
QFrame#card {{
    background-color: {c['bg_card']};
    border-radius: 12px;
    border: 1px solid {c['border']};
}}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
QFrame#sidebar {{
    background-color: {c['bg_sidebar']};
    border-radius: 0px;
}}
QLabel#sidebar_title {{
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 700;
    padding: 8px 0px;
}}
QPushButton#nav_button {{
    background-color: transparent;
    color: {c['sidebar_text']};
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#nav_button:hover {{
    background-color: rgba(255,255,255,0.08);
    color: #FFFFFF;
}}
QPushButton#nav_button[active="true"] {{
    background-color: {c['sidebar_active']};
    color: #FFFFFF;
    font-weight: 600;
}}

/* ── Buttons ─────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {c['primary']};
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {c['primary_hover']};
}}
QPushButton:pressed {{
    background-color: {c['primary_hover']};
    padding-top: 9px;
}}
QPushButton:disabled {{
    background-color: {c['border']};
    color: {c['text_muted']};
}}
QPushButton#btn_secondary {{
    background-color: transparent;
    color: {c['primary']};
    border: 1.5px solid {c['primary']};
}}
QPushButton#btn_secondary:hover {{
    background-color: {c['primary_light']};
}}
QPushButton#btn_danger {{
    background-color: {c['danger']};
}}
QPushButton#btn_danger:hover {{
    background-color: #B91C1C;
}}
QPushButton#btn_success {{
    background-color: {c['success']};
}}
QPushButton#btn_success:hover {{
    background-color: #15803D;
}}
QPushButton#btn_warning {{
    background-color: {c['warning']};
}}

/* ── Line Edits / Inputs ─────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
QDateEdit, QComboBox {{
    background-color: {c['input_bg']};
    border: 1.5px solid {c['border']};
    border-radius: 7px;
    padding: 7px 10px;
    color: {c['text_primary']};
    selection-background-color: {c['primary']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QComboBox:focus {{
    border-color: {c['primary']};
    outline: none;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}
QComboBox QAbstractItemView {{
    background-color: {c['bg_card']};
    border: 1px solid {c['border']};
    border-radius: 7px;
    selection-background-color: {c['primary_light']};
    selection-color: {c['primary']};
    padding: 4px;
}}

/* ── Tables ──────────────────────────────────────────────────────────── */
QTableWidget, QTableView {{
    background-color: {c['bg_card']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    gridline-color: {c['border']};
    selection-background-color: {c['primary_light']};
    selection-color: {c['primary']};
    alternate-background-color: {c['table_row_alt']};
}}
QHeaderView::section {{
    background-color: {c['table_header']};
    color: {c['text_secondary']};
    font-weight: 600;
    font-size: 12px;
    padding: 8px 10px;
    border: none;
    border-bottom: 1.5px solid {c['border']};
}}
QTableWidget::item, QTableView::item {{
    padding: 6px 10px;
    border: none;
}}

/* ── Labels ──────────────────────────────────────────────────────────── */
QLabel#label_title {{
    font-size: 22px;
    font-weight: 700;
    color: {c['text_primary']};
}}
QLabel#label_subtitle {{
    font-size: 13px;
    color: {c['text_secondary']};
}}
QLabel#stat_value {{
    font-size: 28px;
    font-weight: 700;
    color: {c['text_primary']};
}}
QLabel#stat_label {{
    font-size: 12px;
    color: {c['text_secondary']};
    font-weight: 500;
}}
QLabel#badge_success {{
    background-color: {c['success_light']};
    color: {c['success']};
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel#badge_danger {{
    background-color: {c['danger_light']};
    color: {c['danger']};
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel#badge_warning {{
    background-color: {c['warning_light']};
    color: {c['warning']};
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}}

/* ── Tab Widget ──────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {c['border']};
    border-radius: 8px;
    background: {c['bg_card']};
}}
QTabBar::tab {{
    background: transparent;
    color: {c['text_secondary']};
    padding: 8px 18px;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    color: {c['primary']};
    border-bottom-color: {c['primary']};
    font-weight: 600;
}}
QTabBar::tab:hover {{
    color: {c['text_primary']};
}}

/* ── Scroll Bars ─────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {c['scrollbar']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ── Dialog ──────────────────────────────────────────────────────────── */
QDialog {{
    background-color: {c['bg_card']};
    border-radius: 12px;
}}

/* ── Group Box ───────────────────────────────────────────────────────── */
QGroupBox {{
    border: 1.5px solid {c['border']};
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 8px;
    font-weight: 600;
    color: {c['text_secondary']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {c['text_secondary']};
}}

/* ── Message Box ─────────────────────────────────────────────────────── */
QMessageBox {{
    background-color: {c['bg_card']};
}}

/* ── Status Bar ──────────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {c['bg_card']};
    border-top: 1px solid {c['border']};
    color: {c['text_secondary']};
    font-size: 12px;
}}

/* ── Tool Tip ────────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {c['bg_sidebar']};
    color: {c['sidebar_text']};
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""


_current_mode = "light"


def set_theme(mode: str) -> None:
    global COLORS, _current_mode
    _current_mode = mode
    COLORS = COLORS_DARK if mode == "dark" else COLORS_LIGHT


def current_theme() -> str:
    return _current_mode
