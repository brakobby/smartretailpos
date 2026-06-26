from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
from PySide6.QtCore import Qt

from app.auth import authenticate


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.user_data = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the login window UI"""
        # Remove window frame (borderless)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setWindowTitle("Aurex Retail - Secure Access")
        self.setFixedSize(460, 610)

        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0d1727, stop:1 #11233d);
                border-radius: 20px;
                border: 1px solid #1f3a5b;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(main_container)
        layout.setSpacing(12)
        layout.setContentsMargins(50, 50, 50, 50)  # More padding
        
        logo_label = QLabel("⚡")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setMinimumHeight(70)
        logo_label.setStyleSheet("""
            font-size: 52px;
            border: none;
            background: transparent;
        """)
        layout.addWidget(logo_label)

        title = QLabel("AUREX RETAIL")
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(42)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #f8fbff;
            letter-spacing: 1.2px;
            border: none;
            background: transparent;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Secure enterprise access")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setMinimumHeight(25)
        subtitle.setStyleSheet("""
            color: #7fb0ff;
            font-size: 14px;
            border: none;
            background: transparent;
        """)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Username section
        username_label = QLabel("Username")
        username_label.setMinimumHeight(22)
        username_label.setStyleSheet("""
            font-weight: bold;
            color: #f8fbff;
            font-size: 13px;
            border: none;
            background: transparent;
        """)
        layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(48)
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 15px;
                border: 1px solid #2c4f72;
                border-radius: 10px;
                font-size: 14px;
                color: #f8fbff;
                background-color: #0f172b;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                background-color: #111e33;
            }
        """)
        layout.addWidget(self.username_input)
        
        layout.addSpacing(5)
        
        # Password section
        password_label = QLabel("Password")
        password_label.setMinimumHeight(22)
        password_label.setStyleSheet("""
            font-weight: bold;
            color: #f8fbff;
            font-size: 13px;
            border: none;
            background: transparent;
        """)
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(48)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 15px;
                border: 1px solid #2c4f72;
                border-radius: 10px;
                font-size: 14px;
                color: #f8fbff;
                background-color: #0f172b;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                background-color: #111e33;
            }
        """)
        layout.addWidget(self.password_input)
        
        layout.addSpacing(10)
        
        # Error message label (hidden by default)
        self.error_label = QLabel("")
        self.error_label.setMinimumHeight(25)
        self.error_label.setStyleSheet("""
            color: #e74c3c;
            font-size: 12px;
            padding: 5px 10px;
            border: none;
            background: transparent;
        """)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Login button
        self.login_btn = QPushButton("LOGIN")
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #60a5fa, stop:1 #3b82f6);
            }
        """)
        self.login_btn.clicked.connect(self.login)
        layout.addWidget(self.login_btn)
        
        # Close button

        close_btn = QPushButton("✕")
        close_btn.setMinimumHeight(30)
        close_btn.setFlat(True)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                color: #8fb2ff;
                font-size: 13px;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        
        
        
        # Set main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(main_container)
        
        # Center on screen
        self.center_on_screen()
        
        # Focus on username input
        self.username_input.setFocus()
        
        # Connect enter key
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.login)
    
    def center_on_screen(self):
        """Center the window on screen"""
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def login(self):
        """Handle login button click"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        # Hide error label
        self.error_label.hide()
        
        if not username or not password:
            self.show_error("Please enter username and password")
            return
        
        # Disable button during login
        self.login_btn.setEnabled(False)
        self.login_btn.setText("LOGGING IN...")
        
        # Try to authenticate
        user = authenticate(username, password)
        
        # Re-enable button
        self.login_btn.setEnabled(True)
        self.login_btn.setText("LOGIN")
        
        if user:
            self.user_data = user
            self.accept()  # Close dialog with success
        else:
            self.show_error("Invalid username or password!")
            self.password_input.clear()
            self.password_input.setFocus()
    
    def show_error(self, message):
        """Show error message"""
        self.error_label.setText(message)
        self.error_label.show()
    
    def mousePressEvent(self, event):
        """Allow window dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Move window when dragged"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()