"""
Professional Dashboard Widget - Main overview page with KPIs and charts
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QFrame, QGridLayout, QPushButton, QScrollArea,
                                QTableWidget, QTableWidgetItem, QHeaderView,
                                QSizePolicy, QSpacerItem)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QPen, QBrush
from datetime import datetime, timedelta
from app.services import get_dashboard_data, get_low_stock_products


class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()
        
        # Auto-refresh every 30 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(30000)  # 30 seconds
    
    def setup_ui(self):
        """Setup professional dashboard UI"""
        # Main scroll area for the entire dashboard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f6fa;
            }
            QScrollBar:vertical {
                width: 10px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #bdc3c7;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Main content widget
        content = QWidget()
        content.setStyleSheet("background-color: #f5f6fa;")
        
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)
        
        # ===== HEADER SECTION =====
        header_layout = QHBoxLayout()
        
        # Left: Welcome message
        header_left = QVBoxLayout()
        header_left.setSpacing(5)
        
        # Get current time of day for greeting
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good Morning"
            emoji = "☀️"
        elif hour < 17:
            greeting = "Good Afternoon"
            emoji = "🌤️"
        else:
            greeting = "Good Evening"
            emoji = "🌙"
        
        welcome = QLabel(f"{emoji} {greeting}")
        welcome.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            border: none;
            background: transparent;
        """)
        header_left.addWidget(welcome)
        
        date_label = QLabel(datetime.now().strftime("%A, %B %d, %Y"))
        date_label.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
            border: none;
            background: transparent;
        """)
        header_left.addWidget(date_label)
        
        header_layout.addLayout(header_left)
        header_layout.addStretch()
        
        # Right: Quick stats
        quick_stats = QFrame()
        quick_stats.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 15px 25px;
                border: 1px solid #e8e8e8;
            }
        """)
        quick_stats_layout = QHBoxLayout(quick_stats)
        quick_stats_layout.setContentsMargins(20, 10, 20, 10)
        quick_stats_layout.setSpacing(20)
        
        # Active sessions
        sessions_label = QLabel("🟢 System Status")
        sessions_label.setStyleSheet("font-size: 13px; color: #27ae60; border: none; background: transparent;")
        
        # Database status
        db_label = QLabel("💾 Database: Active")
        db_label.setStyleSheet("font-size: 13px; color: #2c3e50; border: none; background: transparent;")
        
        quick_stats_layout.addWidget(sessions_label)
        quick_stats_layout.addWidget(db_label)
        
        header_layout.addWidget(quick_stats)
        main_layout.addLayout(header_layout)
        
        # ===== KPI CARDS - ROW 1 =====
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(20)
        
        # Today's Sales
        self.today_sales_card = self.create_kpi_card(
            "TODAY'S SALES",
            "₵0.00",
            "📊",
            "#2563eb",
            "today",
            ""
        )
        kpi_grid.addWidget(self.today_sales_card, 0, 0)
        
        # Today's Profit
        self.today_profit_card = self.create_kpi_card(
            "TODAY'S PROFIT",
            "₵0.00",
            "💰",
            "#16a34a",
            "net profit",
            ""
        )
        kpi_grid.addWidget(self.today_profit_card, 0, 1)
        
        # Transactions Count
        self.transactions_card = self.create_kpi_card(
            "TRANSACTIONS",
            "0",
            "🧾",
            "#7c3aed",
            "today",
            ""
        )
        kpi_grid.addWidget(self.transactions_card, 0, 2)
        
        # Monthly Revenue
        self.monthly_card = self.create_kpi_card(
            "MONTHLY REVENUE",
            "₵0.00",
            "📅",
            "#f59e0b",
            "this month",
            ""
        )
        kpi_grid.addWidget(self.monthly_card, 0, 3)
        
        main_layout.addLayout(kpi_grid)
        
        # ===== KPI CARDS - ROW 2 =====
        kpi_grid2 = QGridLayout()
        kpi_grid2.setSpacing(20)
        
        # Inventory Value
        self.inventory_card = self.create_kpi_card(
            "INVENTORY VALUE",
            "₵0.00",
            "📦",
            "#0f172a",
            "total stock value",
            ""
        )
        kpi_grid2.addWidget(self.inventory_card, 0, 0)
        
        # Low Stock Alert
        self.low_stock_card = self.create_alert_card(
            "LOW STOCK ALERT",
            "0",
            "⚠️",
            "#ef4444"
        )
        kpi_grid2.addWidget(self.low_stock_card, 0, 1)
        
        # Customer Debt
        self.debt_card = self.create_kpi_card(
            "OUTSTANDING DEBT",
            "₵0.00",
            "👥",
            "#dc2626",
            "from customers",
            ""
        )
        kpi_grid2.addWidget(self.debt_card, 0, 2)
        
        # Total Products
        self.products_card = self.create_kpi_card(
            "TOTAL PRODUCTS",
            "0",
            "🏷️",
            "#0f766e",
            "active",
            ""
        )
        kpi_grid2.addWidget(self.products_card, 0, 3)
        
        main_layout.addLayout(kpi_grid2)
        
        # ===== CHARTS & TABLES SECTION =====
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # Left: Sales Chart (placeholder for now)
        chart_frame = QFrame()
        chart_frame.setMinimumHeight(350)
        chart_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f8fbff);
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }
        """)
        
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(20, 20, 20, 20)
        chart_layout.setSpacing(15)
        
        chart_header = QHBoxLayout()
        chart_title = QLabel("📈 Sales Overview (Last 7 Days)")
        chart_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            border: none;
            background: transparent;
        """)
        chart_header.addWidget(chart_title)
        chart_header.addStretch()
        
        chart_layout.addLayout(chart_header)
        
        # Simple bar chart using labels
        chart_content = QWidget()
        chart_content.setStyleSheet("background: transparent; border: none;")
        chart_content.setMinimumHeight(280)
        
        # We'll use a simple visual chart with QFrames
        bars_layout = QHBoxLayout(chart_content)
        bars_layout.setSpacing(10)
        bars_layout.setContentsMargins(10, 0, 10, 20)
        
        # Create 7 day bars
        self.bars = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for i, day in enumerate(days):
            bar_container = QVBoxLayout()
            bar_container.setSpacing(8)
            
            # Value label
            value_label = QLabel("₵0")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("""
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                border: none;
                background: transparent;
            """)
            bar_container.addWidget(value_label)
            
            # Bar
            bar = QFrame()
            bar.setFixedWidth(50)
            bar.setMinimumHeight(10)
            bar.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3498db, stop:1 #2980b9);
                    border-radius: 6px;
                    border: none;
                }
            """)
            bar_container.addWidget(bar)
            
            # Day label
            day_label = QLabel(day)
            day_label.setAlignment(Qt.AlignCenter)
            day_label.setStyleSheet("""
                font-size: 12px;
                color: #7f8c8d;
                border: none;
                background: transparent;
            """)
            bar_container.addWidget(day_label)
            
            bar_container.addStretch()
            bars_layout.addLayout(bar_container)
            self.bars.append((value_label, bar))
        
        chart_layout.addWidget(chart_content)
        
        charts_layout.addWidget(chart_frame, 2)
        
        # Right: Low Stock Table
        table_frame = QFrame()
        table_frame.setMinimumHeight(350)
        table_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f8fbff);
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }
        """)
        
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(20, 20, 20, 20)
        table_layout.setSpacing(15)
        
        table_header = QHBoxLayout()
        table_title = QLabel("⚠️ Low Stock Products")
        table_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            border: none;
            background: transparent;
        """)
        table_header.addWidget(table_title)
        table_header.addStretch()
        
        view_all_btn = QPushButton("View All →")
        view_all_btn.setCursor(Qt.PointingHandCursor)
        view_all_btn.setStyleSheet("""
            QPushButton {
                color: #3498db;
                border: none;
                background: transparent;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #2980b9;
                text-decoration: underline;
            }
        """)
        table_header.addWidget(view_all_btn)
        
        table_layout.addLayout(table_header)
        
        # Low stock table
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(4)
        self.low_stock_table.setHorizontalHeaderLabels(["Product", "Category", "Stock", "Status"])
        self.low_stock_table.horizontalHeader().setStretchLastSection(True)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.low_stock_table.setAlternatingRowColors(True)
        self.low_stock_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ecf0f1;
                border-radius: 8px;
                gridline-color: #f5f6fa;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #ecf0f1;
                font-weight: bold;
                font-size: 12px;
            }
            QTableWidget::item:alternate {
                background-color: #fafbfc;
            }
        """)
        table_layout.addWidget(self.low_stock_table)
        
        charts_layout.addWidget(table_frame, 1)
        
        main_layout.addLayout(charts_layout)
        
        # ===== QUICK ACTIONS =====
        actions_label = QLabel("Quick Actions")
        actions_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 10px;
            border: none;
            background: transparent;
        """)
        main_layout.addWidget(actions_label)
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(15)
        
        # New Sale Button
        new_sale_btn = self.create_action_button(
            "💰", 
            "New Sale", 
            "Start a new transaction",
            "#3498db"
        )
        actions_layout.addWidget(new_sale_btn)
        
        # Stock In Button
        stock_in_btn = self.create_action_button(
            "📥", 
            "Stock In", 
            "Receive inventory",
            "#27ae60"
        )
        actions_layout.addWidget(stock_in_btn)
        
        # Add Product Button
        add_product_btn = self.create_action_button(
            "📦", 
            "Add Product", 
            "Create new product",
            "#f39c12"
        )
        actions_layout.addWidget(add_product_btn)
        
        # Reports Button
        reports_btn = self.create_action_button(
            "📈", 
            "Reports", 
            "View analytics",
            "#8e44ad"
        )
        actions_layout.addWidget(reports_btn)
        
        main_layout.addLayout(actions_layout)
        
        main_layout.addStretch()
        
        scroll.setWidget(content)
        
        # Final layout
        final_layout = QVBoxLayout(self)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.addWidget(scroll)
    
    def create_kpi_card(self, title, value, icon, color, subtitle="", change=""):
        """Create a professional KPI card"""
        card = QFrame()
        card.setMinimumHeight(130)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, stop:1 #f8fbff);
                border-radius: 16px;
                border: 1px solid #e2e8f0;
                border-left: 4px solid {color};
            }}
            QFrame:hover {{
                border: 1px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        
        # Header row with icon and title
        header_row = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {color};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            border: none;
            background: transparent;
        """)
        header_row.addWidget(title_label)
        header_row.addStretch()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 20px;
            border: none;
            background: transparent;
        """)
        header_row.addWidget(icon_label)
        
        layout.addLayout(header_row)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {color};
            font-size: 26px;
            font-weight: 700;
            border: none;
            background: transparent;
        """)
        value_label.setObjectName(f"kpi_{title.lower().replace(' ', '_').replace("", '')}")
        layout.addWidget(value_label)
        
        # Subtitle
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("""
                color: #95a5a6;
                font-size: 11px;
                border: none;
                background: transparent;
            """)
            layout.addWidget(sub_label)
        
        return card
    
    def create_alert_card(self, title, value, icon, color):
        """Create an alert/warning KPI card"""
        card = QFrame()
        card.setMinimumHeight(130)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {color}dd);
                border-radius: 12px;
                border: none;
            }}
            QLabel {{
                color: white;
                border: none;
                background: transparent;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        
        # Header
        header_row = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        header_row.addWidget(title_label)
        header_row.addStretch()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        header_row.addWidget(icon_label)
        
        layout.addLayout(header_row)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
        """)
        value_label.setObjectName("kpi_low_stock_alert")
        layout.addWidget(value_label)
        
        # Subtitle
        sub_label = QLabel("needs attention")
        sub_label.setStyleSheet("font-size: 11px; opacity: 0.9;")
        layout.addWidget(sub_label)
        
        return card
    
    def create_action_button(self, icon, title, description, color):
        """Create a professional action button"""
        btn_frame = QFrame()
        btn_frame.setMinimumHeight(80)
        btn_frame.setCursor(Qt.PointingHandCursor)
        btn_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e8e8e8;
                border-top: 4px solid {color};
            }}
            QFrame:hover {{
                background-color: {color}10;
                border: 1px solid {color};
                border-top: 4px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(btn_frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(5)
        
        icon_label = QLabel(f"{icon}")
        icon_label.setStyleSheet("font-size: 24px; border: none; background: transparent;")
        layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {color};
            font-size: 14px;
            font-weight: bold;
            border: none;
            background: transparent;
        """)
        layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            color: #95a5a6;
            font-size: 11px;
            border: none;
            background: transparent;
        """)
        layout.addWidget(desc_label)
        
        return btn_frame
    
    def refresh_data(self):
        """Refresh all dashboard data"""
        try:
            data = get_dashboard_data()
            
            # Update Today's Sales
            self.find_child_with_text(self, "kpi_today's_sales", f"₵{data['today_sales']:,.2f}")

            # Update Today's Profit
            self.find_child_with_text(self, "kpi_today's_profit", f"₵{data.get('today_profit', 0):,.2f}")

            # Update Transactions
            self.find_child_with_text(self, "kpi_transactions", str(data['transactions_count']))

            # Update Monthly Revenue
            self.find_child_with_text(self, "kpi_monthly_revenue", f"₵{data['monthly_sales']:,.2f}")

            # Update Inventory Value
            self.find_child_with_text(self, "kpi_inventory_value", f"₵{data['inventory_value']:,.2f}")

            # Update Low Stock Alert
            self.find_child_with_text(self, "kpi_low_stock_alert", str(data['low_stock_count']))

            # Update Outstanding Debt
            self.find_child_with_text(self, "kpi_outstanding_debt", f"₵{data['outstanding_debt']:,.2f}")

            # Update Total Products
            self.find_child_with_text(self, "kpi_total_products", str(data.get('total_products', 0)))
            
            # Update low stock table
            self.update_low_stock_table()
            
            # Update sales chart
            self.update_sales_chart()
            
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
    
    def find_child_with_text(self, parent, object_name, text):
        """Find a child widget by object name and set its text"""
        widget = parent.findChild(QLabel, object_name)
        if widget:
            widget.setText(text)
    
    def update_low_stock_table(self):
        """Update low stock products table"""
        try:
            products = get_low_stock_products()
            self.low_stock_table.setRowCount(len(products))
            
            for i, product in enumerate(products[:5]):  # Show top 5
                self.low_stock_table.setItem(i, 0, QTableWidgetItem(product.name))
                self.low_stock_table.setItem(i, 1, QTableWidgetItem(product.category or "N/A"))
                self.low_stock_table.setItem(i, 2, QTableWidgetItem(str(product.stock_quantity)))
                
                # Status indicator
                status = "Critical" if product.stock_quantity <= 5 else "Low"
                status_item = QTableWidgetItem(f"{'🔴' if status == 'Critical' else '🟡'} {status}")
                self.low_stock_table.setItem(i, 3, status_item)
                
        except Exception as e:
            print(f"Error updating low stock table: {e}")
    
    def update_sales_chart(self):
        """Update the 7-day sales chart bars"""
        try:
            from app.database import SessionLocal, Sale
            from sqlalchemy import func
            
            session = SessionLocal()
            try:
                # Get last 7 days sales
                today = datetime.now().date()
                daily_sales = []
                
                for i in range(6, -1, -1):
                    date = today - timedelta(days=i)
                    sales = session.query(func.sum(Sale.total_amount)).filter(
                        func.date(Sale.created_at) == date
                    ).scalar() or 0
                    daily_sales.append(sales)
                
                # Find max for scaling
                max_sales = max(daily_sales) if max(daily_sales) > 0 else 1
                
                # Update bars
                for i, (value_label, bar) in enumerate(self.bars[:7]):
                    if i < len(daily_sales):
                        value_label.setText(f"₵{daily_sales[i]:,.0f}" if daily_sales[i] > 0 else "₵0")
                        height = max(int((daily_sales[i] / max_sales) * 200), 10)
                        bar.setFixedHeight(height)
                        
                        # Color based on sales
                        if daily_sales[i] > 0:
                            bar.setStyleSheet("""
                                QFrame {
                                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #3498db, stop:1 #2980b9);
                                    border-radius: 6px;
                                    border: none;
                                }
                            """)
                        else:
                            bar.setStyleSheet("""
                                QFrame {
                                    background: #ecf0f1;
                                    border-radius: 6px;
                                    border: none;
                                }
                            """)
            finally:
                session.close()
                
        except Exception as e:
            print(f"Error updating chart: {e}")