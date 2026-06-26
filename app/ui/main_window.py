"""
Main Window - Application shell with sidebar navigation
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                QPushButton, QLabel, QStackedWidget, QFrame,
                                QSizePolicy, QSpacerItem)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon


class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.current_module = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main window UI"""
        self.setWindowTitle("SmartRetail POS")
        self.setMinimumSize(1200, 700)
        
        # Remove title bar
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ====== SIDEBAR ======
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a, stop:1 #111827);
                border: none;
                border-right: 1px solid #1f2937;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # App logo/title in sidebar
        sidebar_header = QFrame()
        sidebar_header.setFixedHeight(92)
        sidebar_header.setStyleSheet("""
            QFrame {
                background: transparent;
                border-bottom: 1px solid #1f2937;
            }
            QLabel {
                color: white;
                border: none;
                background: transparent;
            }
        """)
        
        header_layout = QHBoxLayout(sidebar_header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        header_title = QLabel("🏪 SmartRetail")
        header_title.setStyleSheet("font-size: 18px; font-weight: 700; letter-spacing: 0.5px;")
        header_layout.addWidget(header_title)
        
        sidebar_layout.addWidget(sidebar_header)
        
        # Navigation buttons
        self.nav_buttons = []
        
        # Define navigation items
        nav_items = [
            ("📊", "Dashboard", "dashboard"),
            ("💰", "Point of Sale", "pos"),
            ("📦", "Products", "products"),
            ("🏗️", "Inventory", "inventory"),
            ("👥", "Customers", "customers"),
            ("🚚", "Suppliers", "suppliers"),
            ("📈", "Reports", "reports"),
            ("⚙️", "Settings", "settings"),
        ]
        
        for icon, text, module in nav_items:
            btn = QPushButton(f"  {icon}  {text}")
            btn.setFixedHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    color: #cbd5e1;
                    text-align: left;
                    font-size: 13px;
                    border: 1px solid transparent;
                    border-radius: 10px;
                    padding: 12px 14px;
                    margin: 4px 12px;
                    background: transparent;
                }
                QPushButton:hover {
                    color: white;
                    background-color: rgba(255,255,255,0.08);
                    border: 1px solid rgba(255,255,255,0.12);
                }
                QPushButton:checked {
                    color: white;
                    background-color: #2563eb;
                    border: 1px solid #3b82f6;
                    font-weight: 600;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=module: self.switch_module(m))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        # Spacer to push user info to bottom
        sidebar_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # User info at bottom of sidebar
        user_frame = QFrame()
        user_frame.setFixedHeight(88)
        user_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.04);
                border-top: 1px solid #1f2937;
            }
            QLabel {
                color: white;
                border: none;
                background: transparent;
            }
        """)
        
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(15, 10, 15, 10)
        user_layout.setSpacing(3)
        
        user_name = QLabel(self.user_data.get('full_name', 'User'))
        user_name.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        user_role = QLabel(self.user_data.get('role', '').upper())
        user_role.setStyleSheet("font-size: 11px; color: #95a5a6;")
        
        user_layout.addWidget(user_name)
        user_layout.addWidget(user_role)
        
        sidebar_layout.addWidget(user_frame)
        
        main_layout.addWidget(sidebar)
        
        # ====== MAIN CONTENT AREA ======
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #f4f7fb;
                border: none;
            }
        """)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top bar
        top_bar = QFrame()
        top_bar.setFixedHeight(68)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e5e7eb;
            }
            QLabel {
                border: none;
                background: transparent;
                color: #0f172a;
            }
            QPushButton {
                border: none;
                background: transparent;
                color: #64748b;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #2563eb;
            }
        """)
        
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        # Page title (will be updated dynamically)
        self.page_title = QLabel("Dashboard")
        self.page_title.setStyleSheet("font-size: 18px; font-weight: 700;")
        top_layout.addWidget(self.page_title)

        self.status_badge = QLabel("● Live")
        self.status_badge.setStyleSheet("font-size: 12px; color: #16a34a; font-weight: 600;")
        top_layout.addWidget(self.status_badge)
        top_layout.addStretch()
        
        # Minimize button
        minimize_btn = QPushButton("─")
        minimize_btn.setFixedSize(35, 35)
        minimize_btn.setCursor(Qt.PointingHandCursor)
        minimize_btn.clicked.connect(self.showMinimized)
        top_layout.addWidget(minimize_btn)
        
        # Maximize button
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(35, 35)
        self.maximize_btn.setCursor(Qt.PointingHandCursor)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        top_layout.addWidget(self.maximize_btn)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(35, 35)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        top_layout.addWidget(close_btn)
        
        content_layout.addWidget(top_bar)
        
        # Stacked widget for pages
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background-color: #f4f7fb;")
        
        # Create placeholder pages
        from .dashboard import DashboardWidget
        from .pos import POSWidget
        from .products import ProductsWidget
        from .inventory import InventoryWidget
        from .customers import CustomersWidget
        from .suppliers import SuppliersWidget
        from .reports import ReportsWidget
        from .settings import SettingsWidget
        
        self.dashboard_widget = DashboardWidget()
        self.pos_widget = POSWidget()
        self.products_widget = ProductsWidget()
        self.inventory_widget = InventoryWidget()
        self.customers_widget = CustomersWidget()
        self.suppliers_widget = SuppliersWidget()
        self.reports_widget = ReportsWidget()
        self.settings_widget = SettingsWidget()
        
        self.pages.addWidget(self.dashboard_widget)    # 0
        self.pages.addWidget(self.pos_widget)           # 1
        self.pages.addWidget(self.products_widget)      # 2
        self.pages.addWidget(self.inventory_widget)     # 3
        self.pages.addWidget(self.customers_widget)     # 4
        self.pages.addWidget(self.suppliers_widget)     # 5
        self.pages.addWidget(self.reports_widget)       # 6
        self.pages.addWidget(self.settings_widget)      # 7
        
        content_layout.addWidget(self.pages)
        
        main_layout.addWidget(content_frame)
        
        # Show dashboard by default
        self.switch_module("dashboard")
    
    def switch_module(self, module_name):
        """Switch between modules"""
        modules = {
            "dashboard": (0, "Dashboard"),
            "pos": (1, "Point of Sale"),
            "products": (2, "Products"),
            "inventory": (3, "Inventory"),
            "customers": (4, "Customers"),
            "suppliers": (5, "Suppliers"),
            "reports": (6, "Reports"),
            "settings": (7, "Settings"),
        }
        
        if module_name in modules:
            index, title = modules[module_name]
            self.pages.setCurrentIndex(index)
            self.page_title.setText(title)
            self.status_badge.setText("● Live")
            
            # Update button states
            for btn in self.nav_buttons:
                btn.setChecked(False)
            
            # Find and check the correct button
            nav_map = {
                "dashboard": 0, "pos": 1, "products": 2, 
                "inventory": 3, "customers": 4, "suppliers": 5,
                "reports": 6, "settings": 7
            }
            if module_name in nav_map:
                self.nav_buttons[nav_map[module_name]].setChecked(True)
    
    def toggle_maximize(self):
        """Toggle maximize/restore window"""
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")
    
    # Window dragging functionality
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()